import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Set

from app.services.deduplication import generate_fingerprint
from app.services.pii import PIIPHIScrubber
from app.workflows.state import MetaRadarState

logger = logging.getLogger(__name__)


def _is_english_heuristic(text: str) -> bool:
    """Fast heuristic checking whether text is predominantly English ASCII/printable."""
    if not text:
        return False
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    return (ascii_chars / len(text)) >= 0.80


async def node_validate(state: MetaRadarState) -> Dict[str, Any]:
    """
    Node 2: node_validate (D-03, D-04)
    Filters short/non-English text, scrubs PII/PHI, deduplicates within batch,
    and preserves cross-source group identifiers.
    """
    node_name = "node_validate"
    raw_signals = state.get("raw_signals", [])
    validated_signals: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    seen_fingerprints: Set[str] = set()

    try:
        for sig in raw_signals:
            content = str(
                sig.get("content")
                or sig.get("abstract")
                or sig.get("description")
                or sig.get("evidence_text")
                or (sig.get("study", {}).get("protocolSection", {}).get("descriptionModule", {}).get("briefSummary", "") if isinstance(sig.get("study"), dict) else "")
                or sig.get("title")
                or ""
            ).strip()
            title = str(sig.get("title") or "").strip()
            if not title and content:
                title = content[:100]

            # 1. Filter short text (< 50 chars)
            if len(content) < 50:
                logger.debug(f"Filtering out signal with short content ({len(content)} chars): {sig.get('id')}")
                continue

            # 2. Filter non-English
            if not _is_english_heuristic(content):
                logger.debug(f"Filtering out signal failing English heuristic: {sig.get('id')}")
                continue

            # 3. PII / PHI scrubbing
            scrubbed_content, has_pii_content, _ = PIIPHIScrubber.scrub(content)
            scrubbed_title, has_pii_title, _ = PIIPHIScrubber.scrub(title)

            # 4. Deterministic fingerprint generation & deduplication
            pub_date_str = sig.get("published_at")
            try:
                if pub_date_str:
                    pub_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
                else:
                    pub_date = datetime.now(timezone.utc)
            except Exception:
                pub_date = datetime.now(timezone.utc)

            pmid = sig.get("pmid")
            nct_id = sig.get("nct_id")
            reg_id = sig.get("regulatory_id")

            # Extract from external_id if possible
            ext_id = str(sig.get("external_id") or "")
            if ext_id.startswith("pmid:") or "pubmed" in str(sig.get("source_id", "")).lower():
                pmid = pmid or ext_id.replace("pmid:", "").replace("SYN_PUBMED_", "")
            elif ext_id.startswith("nct:") or "NCT" in ext_id:
                nct_id = nct_id or ext_id.replace("nct:", "")

            fingerprint = generate_fingerprint(
                title=scrubbed_title,
                published_at=pub_date,
                publisher=sig.get("publisher", ""),
                company=sig.get("company", ""),
                asset=sig.get("asset", ""),
                pmid=pmid,
                nct_id=nct_id,
                regulatory_id=reg_id
            )

            if fingerprint in seen_fingerprints:
                logger.info(f"Duplicate fingerprint {fingerprint} skipped in batch.")
                continue

            seen_fingerprints.add(fingerprint)

            val_sig = dict(sig)
            val_sig["content"] = scrubbed_content
            val_sig["title"] = scrubbed_title
            val_sig["fingerprint"] = fingerprint
            val_sig["pmid"] = pmid
            val_sig["nct_id"] = nct_id
            val_sig["regulatory_id"] = reg_id
            val_sig["published_at"] = pub_date.isoformat()
            val_sig["is_validated"] = True
            val_sig["is_synthetic"] = bool(sig.get("is_synthetic", False))
            val_sig["data_mode"] = sig.get("data_mode") or ("test_fixture" if val_sig["is_synthetic"] else "live")

            validated_signals.append(val_sig)

        status = "SUCCESS" if validated_signals or not raw_signals else "DEGRADED"
        return {
            "validated_signals": validated_signals,
            "node_statuses": {node_name: status}
        }

    except Exception as e:
        logger.error(f"Error in {node_name}: {e}", exc_info=True)
        errors.append({
            "node": node_name,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        return {
            "validated_signals": [],
            "errors": errors,
            "node_statuses": {node_name: "FAILED"}
        }
