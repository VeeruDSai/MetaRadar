"""Single source of truth for canonical URL construction and provenance honesty (D-22/D-23)."""

from __future__ import annotations

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
    return f"https://pubmed.ncbi.nlm.nih.gov/{clean}/" if clean else None


def _nct_url(external_id: Optional[str]) -> Optional[str]:
    if not external_id:
        return None
    clean = external_id.strip()
    return f"https://clinicaltrials.gov/study/{clean}" if clean else None


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
    is_synthetic: bool = False,
    existing_status: Optional[str] = None,
) -> ProvenancePair:
    """Return (canonical_url, provenance_status).

    Record-specific PubMed/NCT URLs may be constructed. Generic FDA/EMA portal
    homepages are never marked ``available`` — they are ``landing_page_only``.
    """
    url = _normalize_url(existing_url)
    source = (source_id or "").lower()
    ext = external_id or pmid or nct_id

    if not url:
        if source == "pubmed":
            url = _pubmed_url(pmid or ext)
        elif source in ("clinical_trials", "clinicaltrials"):
            url = _nct_url(nct_id or ext)
        elif source == "fda":
            url = FDA_LANDING_PAGE
        elif source == "ema":
            url = EMA_LANDING_PAGE

    if url and ("metaradar.internal" in url or url.endswith(".internal")):
        url = None

    if url and not _looks_like_http_url(url):
        return url, "invalid_url"

    if is_generic_landing_page(url):
        return url, "landing_page_only"

    if existing_status == "fixture" or is_synthetic:
        return url, "fixture"

    if url:
        return url, "available"
    return None, existing_status or "missing_url"
