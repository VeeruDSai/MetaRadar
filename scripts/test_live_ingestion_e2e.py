import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from datetime import datetime, timezone
from sqlalchemy import select, func

from app.db.session import AsyncSessionLocal
from app.models import (
    RawSignalBronze,
    Signal,
    Development,
    Confluence,
    Source,
    SourceHealthLog,
)
from app.services.ingestion import IngestionService
from app.workflows.runner import PipelineRunner


async def main():
    print("=== STEP 1: Running Live Connectors Ingestion ===")
    async with AsyncSessionLocal() as db:
        ingestion_service = IngestionService(db)
        ingestion_res = await ingestion_service.run_connectors(
            connector_ids=["pubmed", "clinical_trials", "fda", "ema"]
        )
    print(f"Ingestion result: {ingestion_res}")

    print("\n=== STEP 2: Running Pipeline Runner to Process Bronze Records ===")
    async with AsyncSessionLocal() as db:
        pipeline_runner = PipelineRunner(session=db)
        pipeline_res = await pipeline_runner.run(batch_size=20)
    print(f"Pipeline status: {pipeline_res.get('status')}")
    print(f"Signals processed: {pipeline_res.get('signals_processed')}")
    print(f"Developments: {pipeline_res.get('developments_count')}")
    print(f"Confluences: {pipeline_res.get('confluence_stories_count')}")

    print("\n=== STEP 3: Backward Trace Verification from Database ===")
    async with AsyncSessionLocal() as db:
        # Check Bronze records
        bronze_count = await db.scalar(select(func.count(RawSignalBronze.id)))
        print(f"Total Bronze Records: {bronze_count}")

        # Check Source Health Logs
        health_logs = (await db.execute(select(SourceHealthLog).order_by(SourceHealthLog.checked_at.desc()).limit(5))).scalars().all()
        print("\nLatest Source Health Logs:")
        for log in health_logs:
            print(f"  - [{log.source_id}] status={log.connector_status}, http={log.http_status}, latency={log.latency_ms}ms, fetched={log.records_fetched}, error={log.last_error}")

        # Check Silver Signals with Provenance
        sig_stmt = select(Signal).order_by(Signal.created_at.desc()).limit(5)
        signals = (await db.execute(sig_stmt)).scalars().all()
        print("\nLatest Silver Signals (with Live Provenance):")
        for s in signals:
            ext_id = s.pmid or s.nct_id or s.regulatory_id or s.fingerprint
            print(f"  - Signal ID: {s.signal_id}")
            print(f"    Source: {s.source_id} | Type: {s.signal_type} | Ext ID: {ext_id} | Priority: {s.priority}")
            print(f"    URL: {s.canonical_url}")
            print(f"    Published: {s.published_at} | Retrieved: {s.retrieved_at}")
            print(f"    Title: {s.title[:80]}...")
            print(f"    Verbatim Excerpt: {(s.content or '')[:120]}...")

        # Check Gold Confluences
        conf_stmt = select(Confluence, Development.title).outerjoin(Development, Confluence.development_id == Development.development_id).limit(5)
        confluences = (await db.execute(conf_stmt)).all()
        print(f"\nTotal Confluences: {len(confluences)}")
        for conf, dev_title in confluences:
            print(f"  - Confluence ID: {conf.confluence_id}")
            print(f"    Development: {dev_title}")
            print(f"    Type: {conf.confluence_type} | Signals: {conf.signal_count}")

    print("\n=== END-TO-END VERIFICATION COMPLETE ===")


if __name__ == "__main__":
    asyncio.run(main())
