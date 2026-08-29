import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Asset,
    Company,
    Confluence,
    Contradiction,
    Development,
    WatchItem,
    PipelineRun,
    RawSignalBronze,
    Signal,
)
from app.services.embeddings import embedding_service
from app.services.scoring import priority_scorer
from app.services.provenance_urls import resolve_canonical_provenance
from app.workflows.graph import build_graph
from app.workflows.state import MetaRadarState, create_initial_state

logger = logging.getLogger(__name__)


class PipelineRunner:
    """
    Async Execution Orchestrator for the 10-node MetaRadar LangGraph Intelligence Pipeline (D-01).
    Manages PipelineRun DB lifecycle, database persistence, error tracking, and state execution.
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session
        self._graph = build_graph()

    async def run(
        self,
        batch_size: int = 50,
        pipeline_run_id: Optional[str] = None,
        raw_signals: Optional[List[Dict[str, Any]]] = None,
        calibration_feedback: Optional[List[Dict[str, Any]]] = None,
    ) -> MetaRadarState:
        """
        Executes the 10-node LangGraph pipeline.
        Tracks PipelineRun lifecycle and persists output entities to the database if session is available.
        """
        run_uuid = uuid.UUID(pipeline_run_id) if pipeline_run_id else uuid.uuid4()
        run_id_str = str(run_uuid)

        db_run: Optional[PipelineRun] = None

        # 1. Initialize PipelineRun record in DB if session is active
        if self._session is not None:
            try:
                db_run = PipelineRun(
                    pipeline_run_id=run_uuid,
                    started_at=datetime.now(timezone.utc),
                    status="running",
                    trigger="scheduled" if not raw_signals else "manual",
                )
                self._session.add(db_run)
                await self._session.commit()
            except Exception as e:
                logger.warning(f"Failed to record initial PipelineRun {run_id_str}: {e}")

        # 2. Fetch unpromoted bronze records if raw_signals not explicitly passed
        fetched_bronze: List[Dict[str, Any]] = []
        if raw_signals is None and self._session is not None:
            try:
                stmt = (
                    select(RawSignalBronze)
                    .where(RawSignalBronze.pipeline_run_id.is_(None))
                    .order_by(RawSignalBronze.retrieved_at.desc())
                    .limit(batch_size)
                )
                result = await self._session.execute(stmt)
                bronze_rows = result.scalars().all()
                for row in bronze_rows:
                    payload = dict(row.raw_payload or {})
                    payload["id"] = str(row.id)
                    payload["source_id"] = row.source_id
                    payload["external_id"] = row.external_id
                    payload["retrieved_at"] = row.retrieved_at.isoformat() if row.retrieved_at else None
                    payload["is_synthetic"] = bool(payload.get("is_synthetic", False))
                    payload["data_mode"] = payload.get("data_mode", "live")
                    if not payload.get("content"):
                        payload["content"] = (
                            payload.get("abstract")
                            or payload.get("description")
                            or payload.get("evidence_text")
                            or (payload.get("study", {}).get("protocolSection", {}).get("descriptionModule", {}).get("briefSummary", "") if isinstance(payload.get("study"), dict) else "")
                            or payload.get("title", "")
                        )
                    if not payload.get("title") and payload.get("content"):
                        payload["title"] = str(payload["content"])[:100]
                    fetched_bronze.append(payload)
            except Exception as e:
                logger.warning(f"Failed to fetch unpromoted bronze signals: {e}")

        signals_input = raw_signals if raw_signals is not None else fetched_bronze
        logger.info(f"[PIPELINE] Starting LangGraph pipeline run {run_id_str[:8]} with {len(signals_input)} input signal(s)")
        initial_state = create_initial_state(
            pipeline_run_id=run_id_str,
            raw_signals=signals_input,
            calibration_feedback=calibration_feedback or [],
        )

        try:
            final_state = await self._graph.ainvoke(initial_state)
            logger.info(
                f"[PIPELINE] Pipeline run {run_id_str[:8]} complete -> "
                f"signals_processed: {final_state.get('signals_processed', 0)}, "
                f"confluences: {len(final_state.get('confluence_alerts', []))}, "
                f"contradictions: {len(final_state.get('contradictions', []))}"
            )

            # 3. Persist output entities to database
            if self._session is not None:
                await self._persist_state_to_db(final_state, run_uuid)

            # 4. Mark PipelineRun as completed
            if self._session is not None and db_run is not None:
                try:
                    db_run.status = "completed"
                    db_run.completed_at = datetime.now(timezone.utc)
                    db_run.signals_fetched = len(signals_input)
                    db_run.signals_created = len(final_state.get("scored_signals", []))
                    db_run.signals_updated = 0
                    db_run.duplicates_removed = final_state.get("duplicate_count", 0)
                    db_run.errors_count = len(final_state.get("errors", []))
                    db_run.error_summary = final_state.get("errors") or None
                    await self._session.commit()
                except Exception as e:
                    logger.warning(f"Failed to complete PipelineRun record {run_id_str}: {e}")

            return final_state

        except Exception as e:
            logger.error(f"Pipeline execution failed for run {run_id_str}: {e}", exc_info=True)
            if self._session is not None and db_run is not None:
                try:
                    db_run.status = "failed"
                    db_run.completed_at = datetime.now(timezone.utc)
                    db_run.errors_count = 1
                    db_run.error_summary = [{"error": str(e), "stage": "graph_execution"}]
                    await self._session.commit()
                except Exception:
                    pass
            raise

    async def _persist_state_to_db(self, final_state: MetaRadarState, run_uuid: uuid.UUID) -> None:
        """Persist gold developments, silver signals with embeddings, and confluence rows."""
        now = datetime.now(timezone.utc)

        # 1. Persist Developments
        # Query valid asset and company IDs to protect against FK violations
        asset_res = await self._session.execute(select(Asset.asset_id))
        valid_asset_ids = set(asset_res.scalars().all())
        comp_res = await self._session.execute(select(Company.company_id))
        valid_company_ids = set(comp_res.scalars().all())

        dev_id_map: Dict[str, uuid.UUID] = {}
        for dev_dict in final_state.get("developments", []):
            try:
                raw_id = dev_dict.get("development_id") or dev_dict.get("id")
                dev_uuid = uuid.UUID(str(raw_id)) if raw_id and len(str(raw_id)) == 36 else uuid.uuid4()
                dev_id_map[str(raw_id)] = dev_uuid

                existing_dev = await self._session.get(Development, dev_uuid)
                if not existing_dev:
                    asset_id = dev_dict.get("asset_id")
                    if asset_id and asset_id not in valid_asset_ids:
                        asset_id = None
                    company_id = dev_dict.get("company_id")
                    if company_id and company_id not in valid_company_ids:
                        company_id = None

                    dev_row = Development(
                        development_id=dev_uuid,
                        title=dev_dict.get("title", "Haemophilia Development"),
                        disease=dev_dict.get("disease", "haemophilia_a"),
                        asset_id=asset_id,
                        company_id=company_id,
                        current_stage=dev_dict.get("current_stage", "announced"),
                        created_at=now,
                        updated_at=now,
                    )
                    self._session.add(dev_row)
            except Exception as e:
                logger.warning(f"Could not persist development {dev_dict}: {e}")

        await self._session.flush()

        # 2. Persist Signals with Embeddings & Provenance
        failed_signal_ids: set = set()
        for sig in final_state.get("scored_signals", []) or final_state.get("validated_signals", []):
            try:
                sig_raw_id = sig.get("id") or sig.get("signal_id")
                sig_uuid = uuid.UUID(str(sig_raw_id)) if sig_raw_id and len(str(sig_raw_id)) == 36 else uuid.uuid4()
                source = sig.get("source_id", "pubmed")
                # Deterministic identity: prefer an explicit external_id, then a
                # pre-computed fingerprint; only fall back to a fresh UUID when
                # neither exists (random fallbacks break upsert dedup across runs).
                ext_id = sig.get("external_id") or sig.get("fingerprint") or str(sig_uuid)
                if len(ext_id) > 255:
                    ext_id = ext_id[:255]
                fp = sig.get("fingerprint") or f"sig:{source}:{ext_id}"

                pmid = ext_id if source == "pubmed" else None
                nct_id = ext_id if source == "clinical_trials" else None
                reg_id = ext_id if source in ("fda", "ema") else None

                # Generate embedding
                embedding = None
                try:
                    embedding = await embedding_service.embed_signal(sig)
                except Exception as emb_e:
                    logger.debug(f"Signal embedding generation skipped: {emb_e}")

                dev_uuid = None
                if sig.get("development_id"):
                    raw_d = str(sig.get("development_id"))
                    dev_uuid = dev_id_map.get(raw_d) or (uuid.UUID(raw_d) if len(raw_d) == 36 else None)

                pub_at = sig.get("published_at")
                if isinstance(pub_at, str):
                    try:
                        pub_at = datetime.fromisoformat(pub_at.replace("Z", "+00:00"))
                    except Exception:
                        pub_at = now
                elif not isinstance(pub_at, datetime):
                    pub_at = now

                ret_at = sig.get("retrieved_at")
                if isinstance(ret_at, str):
                    try:
                        ret_at = datetime.fromisoformat(ret_at.replace("Z", "+00:00"))
                    except Exception:
                        ret_at = now
                elif not isinstance(ret_at, datetime):
                    ret_at = now

                # Construct appropriate external direct source URL and provenance status
                url, prov_status = resolve_canonical_provenance(
                    source_id=source,
                    existing_url=sig.get("url") or sig.get("canonical_url"),
                    external_id=ext_id,
                    title_or_content=f"{sig.get('title', '')} {sig.get('content', '')}",
                    is_synthetic=bool(sig.get("is_synthetic", False)),
                    existing_status=sig.get("provenance_status"),
                )

                # Multi-Factor Deterministic Priority Scoring (Novelty 25% + Clinical 30% + Regulatory 25% + Recency 20%)
                score_breakdown = sig.get("score_breakdown")
                if not score_breakdown or not isinstance(score_breakdown, dict) or not score_breakdown.get("total"):
                    text_to_score = f"{sig.get('title', '')} {sig.get('content', '')}"
                    sb = priority_scorer.score_text(text_to_score, pub_at, novelty_distance=0.6)
                    if sb:
                        score_breakdown = sb.to_dict()

                raw_prio = sig.get("priority")
                if not raw_prio and score_breakdown and score_breakdown.get("priority_level"):
                    priority_str = score_breakdown["priority_level"]
                elif isinstance(raw_prio, (int, float)):
                    priority_str = "CRITICAL" if raw_prio >= 0.85 else "HIGH" if raw_prio >= 0.65 else "MEDIUM"
                else:
                    priority_str = str(raw_prio or "MEDIUM").upper()

                is_synth = bool(sig.get("is_synthetic", False))
                data_mode = sig.get("data_mode") or ("test_fixture" if is_synth else "live")
                provenance_status = sig.get("provenance_status") or ("fixture" if is_synth else "available" if url else "missing_url")
                source_name = sig.get("source_name") or (source.upper().replace("_", " ") if source else None)
                evidence_text = sig.get("evidence_text") or sig.get("content") or sig.get("title")
                raw_ref = sig.get("raw_record_reference")

                stmt = pg_insert(Signal).values(
                    signal_id=sig_uuid,
                    fingerprint=fp,
                    source_id=source,
                    source_name=source_name,
                    external_id=ext_id,
                    pmid=pmid,
                    nct_id=nct_id,
                    regulatory_id=reg_id,
                    title=sig.get("title", ""),
                    content=sig.get("content", ""),
                    canonical_url=url,
                    evidence_text=evidence_text,
                    raw_record_reference=raw_ref,
                    provenance_status=provenance_status,
                    published_at=pub_at,
                    retrieved_at=ret_at,
                    ingested_at=now,
                    signal_type=sig.get("signal_type", "CLINICAL_TRIAL"),
                    disease=sig.get("disease", "haemophilia_a"),
                    facts=sig.get("facts") or [],
                    interpretation=sig.get("interpretation") or "",
                    speculation=sig.get("speculation") or "",
                    priority=priority_str,
                    score_breakdown=score_breakdown or {},
                    development_id=dev_uuid,
                    data_mode=data_mode,
                    is_synthetic=is_synth,
                    pipeline_run_id=run_uuid,
                    embedding=embedding,
                ).on_conflict_do_update(
                    index_elements=["fingerprint"],
                    set_={
                        "source_name": source_name,
                        "external_id": ext_id,
                        "title": sig.get("title", ""),
                        "content": sig.get("content", ""),
                        "retrieved_at": ret_at,
                        "canonical_url": url,
                        "evidence_text": evidence_text,
                        "raw_record_reference": raw_ref,
                        "provenance_status": provenance_status,
                        "data_mode": data_mode,
                        "is_synthetic": is_synth,
                        "facts": sig.get("facts") or [],
                        "interpretation": sig.get("interpretation") or "",
                        "speculation": sig.get("speculation") or "",
                        "priority": priority_str,
                        "score_breakdown": score_breakdown or {},
                        "pipeline_run_id": run_uuid,
                    }
                )
                await self._session.execute(stmt)
            except Exception as e:
                logger.warning(f"Could not persist signal {sig.get('title')}: {e}")
                failed_raw_id = sig.get("id") or sig.get("signal_id")
                if failed_raw_id:
                    failed_signal_ids.add(str(failed_raw_id))

        # 3. Persist Confluences
        for story in final_state.get("confluent_stories", []):
            try:
                c_raw_id = story.get("confluence_id")
                c_uuid = uuid.UUID(str(c_raw_id)) if c_raw_id and len(str(c_raw_id)) == 36 else uuid.uuid4()
                raw_d = str(story.get("development_id"))
                dev_uuid = dev_id_map.get(raw_d) or (uuid.UUID(raw_d) if len(raw_d) == 36 else None)

                if dev_uuid:
                    c_row = Confluence(
                        confluence_id=c_uuid,
                        development_id=dev_uuid,
                        confluence_type=story.get("confluence_type", "emerging"),
                        signal_count=len(story.get("signal_ids", [])),
                        created_at=now,
                    )
                    self._session.add(c_row)
            except Exception as e:
                logger.warning(f"Could not persist confluence {story}: {e}")

        # 4. Mark Bronze Records as Promoted
        # Only promote bronze rows whose silver persistence succeeded — rows whose
        # insert failed stay unpromoted (pipeline_run_id IS NULL) so the next run
        # can retry them instead of being silently lost.
        try:
            bronze_ids = [
                uuid.UUID(str(s["id"]))
                for s in final_state.get("raw_signals", [])
                if s.get("id") and len(str(s["id"])) == 36 and str(s["id"]) not in failed_signal_ids
            ]
            if bronze_ids:
                upd_stmt = (
                    update(RawSignalBronze)
                    .where(RawSignalBronze.id.in_(bronze_ids))
                    .values(pipeline_run_id=run_uuid)
                )
                await self._session.execute(upd_stmt)
        except Exception as e:
            logger.warning(f"Could not update raw_signals_bronze promotion status: {e}")

        await self._session.commit()
