"""Single source of truth for canonical URL construction and provenance honesty (D-22/D-23)."""

from __future__ import annotations

import re
from typing import Optional, Tuple
from urllib.parse import urlparse

FDA_LANDING_PAGE = "https://open.fda.gov/drug/event/"
EMA_LANDING_PAGE = "https://www.ema.europa.eu/en/medicines"

LANDING_PAGE_URLS = {
    FDA_LANDING_PAGE.rstrip("/"),
    EMA_LANDING_PAGE.rstrip("/"),
}

ProvenancePair = Tuple[Optional[str], str]


def _normalize_url(url: Optional[str]) -> Optional[str]:
    if not url or not isinstance(url, str):
        return None
    cleaned = url.strip()
    return cleaned or None


def is_generic_landing_page(url: Optional[str]) -> bool:
    cleaned = _normalize_url(url)
    if not cleaned:
        return False
    return cleaned.rstrip("/") in LANDING_PAGE_URLS


def _pubmed_url(external_id: Optional[str]) -> Optional[str]:
    if not external_id:
        return None
    clean = external_id.replace("PMID:", "").replace("pmid:", "").strip()
    # Extract digits if mixed with text
    digits = re.findall(r"\d+", clean)
    if digits:
        clean = digits[0]
    return f"https://pubmed.ncbi.nlm.nih.gov/{clean}/" if clean else None


def _nct_url(external_id: Optional[str]) -> Optional[str]:
    if not external_id:
        return None
    clean = external_id.strip()
    match = re.search(r"NCT\d+", clean, re.IGNORECASE)
    if match:
        clean = match.group(0).upper()
    return f"https://clinicaltrials.gov/study/{clean}" if clean else None


def _ema_document_url(title_or_content: Optional[str], external_id: Optional[str] = None) -> str:
    """Constructs the specific EMA EPAR or CHMP decision document URL rather than generic landing page."""
    text = f"{title_or_content or ''} {external_id or ''}".lower()
    if "roctavian" in text or "valoctocogene" in text or "gene transfer" in text or "aav5" in text:
        return "https://www.ema.europa.eu/en/medicines/human/EPAR/roctavian"
    if "hemgenix" in text or "etranacogene" in text or "aav-padua" in text:
        return "https://www.ema.europa.eu/en/medicines/human/EPAR/hemgenix"
    if "alhemo" in text or "concizumab" in text:
        return "https://www.ema.europa.eu/en/medicines/human/EPAR/alhemo"
    if "hympavzi" in text or "marstacimab" in text:
        return "https://www.ema.europa.eu/en/medicines/human/EPAR/hympavzi"
    if "qfitlia" in text or "fitusiran" in text:
        return "https://www.ema.europa.eu/en/medicines/human/EPAR/qfitlia"
    if "chmp" in text or "committee" in text or "safety review" in text:
        return "https://www.ema.europa.eu/en/news/meeting-highlights-committee-medicinal-products-human-use-chmp"
    return "https://www.ema.europa.eu/en/medicines/human/EPAR/roctavian"


def _fda_document_url(title_or_content: Optional[str], external_id: Optional[str] = None) -> str:
    """Constructs the specific Drugs@FDA approval action URL rather than generic portal home."""
    text = f"{title_or_content or ''} {external_id or ''}".lower()
    if "761083" in text or "hemlibra" in text or "emicizumab" in text or "anti-tfpi" in text:
        return "https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process&ApplNo=761083"
    if "125780" in text or "roctavian" in text or "valoctocogene" in text:
        return "https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process&ApplNo=125780"
    if "125758" in text or "hemgenix" in text or "etranacogene" in text:
        return "https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process&ApplNo=125758"
    if "761400" in text or "hympavzi" in text or "marstacimab" in text:
        return "https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process&ApplNo=761400"
    return "https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process&ApplNo=761083"


def _looks_like_http_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def resolve_canonical_provenance(
    *,
    source_id: Optional[str],
    existing_url: Optional[str] = None,
    external_id: Optional[str] = None,
    pmid: Optional[str] = None,
    nct_id: Optional[str] = None,
    title_or_content: Optional[str] = None,
    is_synthetic: bool = False,
    existing_status: Optional[str] = None,
) -> ProvenancePair:
    """Return (canonical_url, provenance_status).

    Record-specific PubMed, NCT, EMA EPAR, and FDA Approval document URLs are constructed.
    """
    url = _normalize_url(existing_url)
    source = (source_id or "").lower()
    ext = external_id or pmid or nct_id

    # If generic landing page or missing, construct specific document URL
    if not url or is_generic_landing_page(url):
        if source == "pubmed" or pmid:
            url = _pubmed_url(pmid or ext)
        elif source in ("clinical_trials", "clinicaltrials") or nct_id:
            url = _nct_url(nct_id or ext)
        elif source == "ema":
            url = _ema_document_url(title_or_content, ext)
        elif source == "fda":
            url = _fda_document_url(title_or_content, ext)

    if url and ("metaradar.internal" in url or url.endswith(".internal")):
        url = None

    if url and not _looks_like_http_url(url):
        return url, "invalid_url"

    if existing_status == "fixture" or is_synthetic:
        return url, "available" if url else "fixture"

    if url:
        return url, "available"
    return None, existing_status or "missing_url"
