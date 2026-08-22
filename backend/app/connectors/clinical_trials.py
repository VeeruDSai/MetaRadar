import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.connectors.base import (
    ConnectorFetchError,
    ProfileRunResult,
    RawSignalPayload,
    SourceConnector,
)
from app.services.deduplication import generate_fingerprint

logger = logging.getLogger(__name__)


class ClinicalTrialsConnector(SourceConnector):
    """ClinicalTrials.gov API v2 async adapter (REQ-P1-2).

    Near-real-time, incremental per profile via ConnectorState, paginated via
    nextPageToken, NCT-fingerprinted. Verbatim study JSON objects persisted
    to bronze (D-23).
    """

    source_id = "clinical_trials"
    source_type = "clinical_trial"
    freshness_class = "near_real_time"
    BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
    PAGE_SIZE = 100

    def __init__(self):
        super().__init__()
        self.config = self._connector_config()

    # ------------------------------------------------------------------ #

    async def run_profile(
        self,
        session: Any,
        profile_id: str,
        force_backfill: bool = False,
    ) -> ProfileRunResult:
        started = datetime.now(timezone.utc)
        profile = next(
            (p for p in (self.config.profiles if self.config else []) if p.id == profile_id),
            None,
        )
        if profile is None:
            return ProfileRunResult(
                profile_id=profile_id,
                status="FAILED",
                fetched=0,
                error_detail=f"Profile '{profile_id}' not found in domain config",
            )

        try:
            today = started.date()
            start_date = await self._window_start(session, profile_id, force_backfill, today)

            params: Dict[str, Any] = {
                "format": "json",
                "pageSize": self.PAGE_SIZE,
                "sort": "LastUpdatePostDate:desc",
                "filter.advanced": (
                    f"AREA[LastUpdatePostDate]RANGE[{start_date.isoformat()},{today.isoformat()}]"
                ),
            }
            if profile.conditions:
                params["query.cond"] = " OR ".join(profile.conditions)
            if profile.interventions:
                params["query.intr"] = " OR ".join(profile.interventions)
            if profile.sponsor_keywords:
                params["query.spons"] = " OR ".join(profile.sponsor_keywords)

            studies: List[Dict[str, Any]] = []
            next_token: Optional[str] = None
            max_results = (self.config.max_results_per_profile if self.config else 500) or 500
            upstream_data_timestamp: Optional[str] = None

            # Read previous state cursor
            state = await self._read_connector_state(session, profile_id)
            prev_data_timestamp: Optional[str] = None
            if state and state.cursor:
                try:
                    cursor_dict = json.loads(state.cursor)
                    if isinstance(cursor_dict, dict):
                        prev_data_timestamp = cursor_dict.get("data_timestamp")
                except Exception:
                    pass

            while True:
                page_params = dict(params)
                if next_token:
                    page_params["pageToken"] = next_token
                resp = await self._fetch_with_retry(self.BASE_URL, params=page_params)
                data = resp.json()
                upstream_data_timestamp = data.get("dataTimestamp") or upstream_data_timestamp
                page_studies = data.get("studies") or []
                studies.extend(page_studies)
                next_token = data.get("nextPageToken")
                if not next_token or not page_studies or len(studies) >= max_results:
                    break

            # If upstream data timestamp is unchanged from last check and no studies returned, resolve NO_NEW_DATA
            if not studies or (upstream_data_timestamp and upstream_data_timestamp == prev_data_timestamp and not force_backfill):
                self.last_success = datetime.now(timezone.utc)
                self.status = "active"
                self.last_error = None
                await self._write_connector_state(
                    session,
                    profile_id,
                    last_success=self.last_success,
                    cursor=json.dumps({"data_timestamp": upstream_data_timestamp or prev_data_timestamp}),
                    first_run_completed=True,
                )
                return ProfileRunResult(
                    profile_id=profile_id,
                    status="NO_NEW_DATA",
                    fetched=len(studies),
                    new_rows=0,
                    duplicates=len(studies),
                    duration_s=(datetime.now(timezone.utc) - started).total_seconds(),
                    upstream_data_timestamp=upstream_data_timestamp or prev_data_timestamp,
                )

            payloads: List[RawSignalPayload] = []
            for study in studies:
                payload = self._parse_study(study, started)
                if payload is not None:
                    payloads.append(payload)

            fetched = len(payloads)
            new_rows, duplicates = 0, 0
            if payloads:
                new_rows, duplicates = await self._persist_bronze(session, payloads)

            self.last_success = datetime.now(timezone.utc)
            self.status = "active"
            self.last_error = None
            await self._write_connector_state(
                session,
                profile_id,
                last_success=self.last_success,
                cursor=json.dumps({"data_timestamp": upstream_data_timestamp}),
                first_run_completed=True,
            )

            status_result = "SUCCESS" if new_rows > 0 or fetched > 0 else "NO_NEW_DATA"
            return ProfileRunResult(
                profile_id=profile_id,
                status=status_result,
                fetched=fetched,
                new_rows=new_rows,
                duplicates=duplicates,
                duration_s=(datetime.now(timezone.utc) - started).total_seconds(),
                upstream_data_timestamp=upstream_data_timestamp,
            )
        except ConnectorFetchError as e:
            return self._fail(profile_id, started, str(e))
        except json.JSONDecodeError as e:
            return self._fail(profile_id, started, f"Invalid JSON from ClinicalTrials API: {e}")
        except Exception as e:  # noqa: BLE001 — honest per-profile isolation
            logger.exception("ClinicalTrialsConnector profile %s failed", profile_id)
            return self._fail(profile_id, started, str(e))

    # ------------------------------------------------------------------ #

    async def _window_start(self, session: Any, profile_id: str, force_backfill: bool, today) -> Any:
        cfg = self.config
        if cfg is None:
            return today - timedelta(days=30)
        if force_backfill:
            return today - timedelta(days=cfg.backfill_days)
        state = await self._read_connector_state(session, profile_id)
        if state is None or not state.first_run_completed:
            return today - timedelta(days=cfg.backfill_days)
        rolling_start = today - timedelta(days=cfg.rolling_window_days)
        if state.last_success is not None and state.last_success.date() > rolling_start:
            return state.last_success.date()
        return rolling_start

    def _parse_study(self, study: Dict[str, Any], retrieved_at: datetime) -> Optional[RawSignalPayload]:
        protocol = study.get("protocolSection") or {}
        identification = protocol.get("identificationModule") or {}
        nct_id = (identification.get("nctId") or "").strip()
        if not nct_id:
            return None
        status_module = protocol.get("statusModule") or {}
        conditions_module = protocol.get("conditionsModule") or {}
        arms_module = protocol.get("armsInterventionsModule") or {}

        title = (
            identification.get("officialTitle")
            or identification.get("briefTitle")
            or ""
        ).strip()
        sponsor = (identification.get("organization") or {}).get("fullName") or ""
        status = status_module.get("overallStatus") or ""
        phases = status_module.get("phase") or []
        conditions = [c for c in (conditions_module.get("conditions") or []) if c]
        interventions = [
            i.get("name")
            for i in (arms_module.get("interventions") or [])
            if i.get("name")
        ]

        description_module = protocol.get("descriptionModule") or {}
        brief_summary = (description_module.get("briefSummary") or "").strip()

        first_post = status_module.get("studyFirstPostDateStruct") or {}
        published_at = self._parse_date(first_post.get("date"), retrieved_at)

        results_section = study.get("resultsSection")
        has_results = bool(results_section) or bool(study.get("hasResults"))
        status_upper = status.upper().strip()

        if has_results:
            event_type = "RESULTS_POSTED"
        elif "COMPLETED" in status_upper:
            event_type = "STUDY_COMPLETED"
        elif any(term in status_upper for term in ("TERMINATED", "SUSPENDED", "WITHDRAWN")):
            event_type = f"STUDY_{status_upper}"
        elif any(term in status_upper for term in ("RECRUITING", "NOT_RECRUITING", "ENROLLING")):
            event_type = "RECRUITMENT_UPDATE"
        elif phases:
            event_type = "PHASE_UPDATE"
        else:
            event_type = "NEW_TRIAL"

        url = f"https://clinicaltrials.gov/study/{nct_id}"
        fingerprint = generate_fingerprint(nct_id=nct_id, title=title, published_at=published_at)
        content_parts = [p for p in [title, brief_summary, " ".join(conditions + interventions)] if p]
        content = "\n".join(content_parts)
        content_hash = hashlib.sha256(f"{nct_id}:{content}".encode("utf-8")).hexdigest()

        evidence_parts = [p for p in [title, brief_summary, f"Conditions: {', '.join(conditions)}" if conditions else "", f"Interventions: {', '.join(interventions)}" if interventions else "", f"Status: {status}" if status else "", f"Event: {event_type}"] if p]
        evidence_text = ". ".join(evidence_parts)
        raw_payload = {
            "external_id": nct_id,
            "fingerprint": fingerprint,
            "title": title,
            "brief_summary": brief_summary,
            "status": status,
            "sponsor": sponsor,
            "source_name": "ClinicalTrials.gov",
            "source_tier": 1,
            "signal_type": "CLINICAL_TRIAL",
            "event_type": event_type,
            "url": url,
            "evidence_text": evidence_text,
            "phase": ",".join(phases),
            "conditions": conditions,
            "interventions": interventions,
            "entities": list({*conditions, *interventions}),
            "published_at": published_at.isoformat(),
            "retrieved_at": retrieved_at.isoformat(),
            "connector_version": self.connector_version,
            "study": study,  # verbatim APIv2 study object (D-23)
        }

        return RawSignalPayload(
            source_id=self.source_id,
            source_type=self.source_type,
            external_id=nct_id,
            title=title,
            content=content,
            url=url,
            published_at=published_at,
            publisher=sponsor or None,
            raw_hash=content_hash,
            raw_payload=raw_payload,
        )

    @staticmethod
    def _parse_date(value: Optional[str], fallback: datetime) -> datetime:
        if not value:
            return fallback
        for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
            try:
                parsed = datetime.strptime(value, fmt)
                return parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return fallback

    def _fail(self, profile_id: str, started: datetime, detail: str) -> ProfileRunResult:
        self.status = "error"
        self.last_error = detail
        return ProfileRunResult(
            profile_id=profile_id,
            status="FAILED",
            fetched=0,
            duration_s=(datetime.now(timezone.utc) - started).total_seconds(),
            error_detail=detail,
        )