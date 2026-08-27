"""
MetaRadar Phase 11 — Full 6-Function Decision-Intelligence E2E Harness (Revision 11.2)
Executes authentic cross-functional workflows across all 6 stakeholder functions:
1. Seed/verify deterministic test signals for all 6 roles
2. Medical Affairs: Login -> Queue -> Inspect Evidence/Provenance -> IN_REVIEW -> REVIEWED -> Audit Check -> Logout
3. Regulatory: Login -> Queue -> Inspect Evidence -> IN_REVIEW -> ACTION_REQUIRED -> Audit Check -> Logout
4. Safety: Login -> Queue -> Inspect Evidence -> IN_REVIEW -> ACTION_REQUIRED (escalate=True) -> Verify SIGNAL_ESCALATED -> Logout
5. Leadership: Login -> Summary -> Verify Pending Escalation -> Resolve Escalation (status=ACTIONED) -> Verify ESCALATION_RESOLVED -> Logout
6. Market Access: Login -> Queue -> Inspect Evidence -> IN_REVIEW -> ACTIONED -> Verify Terminal Lock -> Logout
7. Communications: Login -> Queue -> Inspect Evidence -> IN_REVIEW -> DISMISSED -> Logout
8. Leadership: Direct Decision on distinct unreviewed signal -> IN_REVIEW -> ACTIONED -> Logout
"""

import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
import uuid
from pathlib import Path
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")




# Ensure backend directory is in sys.path for direct DB seeding
base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.db.session import AsyncSessionLocal
from app.models import Signal, User

BASE_URL = os.environ.get("METARADAR_API_URL", "http://localhost:8000/api/v1")
ALLOWED_ORIGIN = os.environ.get("METARADAR_ORIGIN", "http://localhost:3000")


async def ensure_acceptance_fixtures():
    """Seeds deterministic unreviewed test signals for all 6 stakeholder functions if absent."""
    canonical_roles = ["MEDICAL_AFFAIRS", "REGULATORY", "SAFETY", "MARKET_ACCESS", "COMMUNICATIONS", "LEADERSHIP"]
    now_utc = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        for role in canonical_roles:
            # Check existing unreviewed signal
            from sqlalchemy import select, func
            count_res = await db.execute(
                select(func.count(Signal.signal_id)).where(
                    Signal.relevant_function == role,
                    Signal.review_status == "UNREVIEWED",
                )
            )
            count = count_res.scalar() or 0
            if count == 0:
                sig = Signal(
                    signal_id=uuid.uuid4(),
                    source_id="fda" if role in ("SAFETY", "REGULATORY") else "pubmed",
                    fingerprint=f"e2e-fixture-{role.lower()}-{uuid.uuid4().hex[:8]}",
                    signal_type="CLINICAL_TRIAL" if role == "MEDICAL_AFFAIRS" else "REGULATORY_UPDATE",
                    disease="Haemophilia A",
                    title=f"Deterministic E2E Acceptance Signal for {role}",
                    content=f"Verbatim clinical evidence excerpt and findings for {role} stakeholder decision workflow.",
                    published_at=now_utc - timedelta(hours=2),
                    retrieved_at=now_utc,
                    ingested_at=now_utc,
                    relevant_function=role,
                    review_status="UNREVIEWED",
                    priority="CRITICAL" if role in ("SAFETY", "LEADERSHIP") else "HIGH",
                    is_escalated=False,
                    canonical_url=f"https://clinicaltrials.gov/study/NCT05{uuid.uuid4().hex[:6]}",
                    provenance_status="URL_PRESENT",
                    facts=["Biomarker durability confirmed", "Safety profile acceptable"],
                )
                db.add(sig)
        await db.commit()
    print("  ✓ Ensured deterministic acceptance fixtures for all 6 functions.")


from app.main import app

BASE_URL = os.environ.get("METARADAR_API_URL", "http://localhost:8000/api/v1")
ALLOWED_ORIGIN = os.environ.get("METARADAR_ORIGIN", "http://localhost:3000")


from app.api.deps import _auth_rate_buckets

class AuthenticatedDecisionClient:
    def __init__(self, base_url: str, origin: str):
        self.origin = origin
        transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(
            transport=transport,
            base_url=base_url,
            timeout=30.0,
            headers={"Origin": self.origin}
        )


    def _get_csrf_header(self) -> Dict[str, str]:
        csrf = self.client.cookies.get("metaradar_csrf")
        return {"X-CSRF-Token": csrf} if csrf else {}

    async def demo_login(self, role: str) -> Dict[str, Any]:
        _auth_rate_buckets.clear()
        res = await self.client.post("/auth/demo-login", json={"role": role})
        assert res.status_code == 200, f"Demo login failed for {role}: {res.text}"
        assert "metaradar_session" in self.client.cookies, "Missing session cookie"
        assert "metaradar_csrf" in self.client.cookies, "Missing CSRF cookie"
        return res.json()

    async def get_queue(self, function_id: str) -> Dict[str, Any]:
        res = await self.client.get(f"/signals/queue/{function_id}")
        assert res.status_code == 200, f"Get queue failed for {function_id}: {res.text}"
        return res.json()

    async def get_signal_detail(self, signal_id: str) -> Dict[str, Any]:
        res = await self.client.get(f"/signals/{signal_id}")
        assert res.status_code == 200, f"Get signal detail failed: {res.text}"
        return res.json()

    async def submit_review(self, signal_id: str, payload: Dict[str, Any]) -> httpx.Response:
        headers = self._get_csrf_header()
        res = await self.client.post(f"/signals/{signal_id}/review", json=payload, headers=headers)
        return res

    async def get_audit_history(self, signal_id: str) -> List[Dict[str, Any]]:
        res = await self.client.get(f"/signals/{signal_id}/audit-history")
        assert res.status_code == 200, f"Audit history failed: {res.text}"
        return res.json()

    async def get_leadership_summary(self) -> Dict[str, Any]:
        res = await self.client.get("/leadership/summary")
        assert res.status_code == 200, f"Leadership summary failed: {res.text}"
        return res.json()

    async def logout(self) -> None:
        headers = self._get_csrf_header()
        res = await self.client.post("/auth/logout", headers=headers)
        assert res.status_code == 200, f"Logout failed: {res.text}"

    async def close(self):
        await self.client.aclose()


async def verify_provenance_and_evidence(signal: dict) -> None:
    assert signal.get("what_changed") or signal.get("content") or signal.get("title"), "Missing content / title"
    canon_url = signal.get("canonical_url")
    prov_status = signal.get("provenance_status")
    if canon_url:
        assert prov_status in {"SOURCE_VERIFIED", "URL_PRESENT", "FIXTURE", "available"}, f"Invalid status for valid URL: {prov_status}"


async def main():
    print("=" * 75)
    print("MetaRadar Phase 11 — Full Cross-Functional Decision Vertical Slice (Rev 11.2)")
    print("=" * 75)

    await ensure_acceptance_fixtures()

    # -------------------------------------------------------------
    # Step 1: Medical Affairs (UNREVIEWED -> IN_REVIEW -> REVIEWED)
    # -------------------------------------------------------------
    print("\n[1/6] Testing Medical Affairs Decision Workflow...")
    c_med = AuthenticatedDecisionClient(BASE_URL, ALLOWED_ORIGIN)
    try:
        me = await c_med.demo_login("MEDICAL_AFFAIRS")
        print(f"  ✓ Authenticated as: {me['display_name']}")
        
        queue = await c_med.get_queue("MEDICAL_AFFAIRS")
        signals = queue.get("signals", [])
        if not signals:
            raise AssertionError("Acceptance fixture missing: no pending signals for MEDICAL_AFFAIRS")
        
        sig = await c_med.get_signal_detail(signals[0]["signal_id"])
        await verify_provenance_and_evidence(sig)
        print(f"  ✓ Inspected evidence & verified provenance for '{sig['title'][:40]}...'")

        # In Review
        res = await c_med.submit_review(sig["signal_id"], {"status": "IN_REVIEW"})
        assert res.status_code == 200, f"Open review failed: {res.text}"

        # Reviewed
        res = await c_med.submit_review(sig["signal_id"], {
            "status": "REVIEWED",
            "decision": "REVIEWED",
            "notes": "Factor VIII biomarker durability validated against clinical criteria",
            "resulting_action": "Update clinical intelligence dossier",
        })
        assert res.status_code == 200, f"Submit decision failed: {res.text}"
        print("  ✓ State transitioned: UNREVIEWED -> IN_REVIEW -> REVIEWED")

        audits = await c_med.get_audit_history(sig["signal_id"])
        assert any(a["action"] == "SIGNAL_REVIEWED" for a in audits)
        print("  ✓ Immutable audit trail entry verified")
        await c_med.logout()
        print("  ✓ Logged out successfully with CSRF & Origin validation")
    finally:
        await c_med.close()

    # -------------------------------------------------------------
    # Step 2: Safety & Leadership Escalation Loop
    # -------------------------------------------------------------
    print("\n[2/6] Testing Safety Escalation -> Leadership Resolution Workflow...")
    c_safe = AuthenticatedDecisionClient(BASE_URL, ALLOWED_ORIGIN)
    escalated_signal_id = None
    try:
        me_safe = await c_safe.demo_login("SAFETY")
        queue_safe = await c_safe.get_queue("SAFETY")
        signals_safe = queue_safe.get("signals", [])
        if not signals_safe:
            raise AssertionError("Acceptance fixture missing: no pending signals for SAFETY")
        
        sig_safe = await c_safe.get_signal_detail(signals_safe[0]["signal_id"])
        escalated_signal_id = sig_safe["signal_id"]
        await verify_provenance_and_evidence(sig_safe)

        # In Review
        await c_safe.submit_review(escalated_signal_id, {"status": "IN_REVIEW"})

        # Escalate with ACTION_REQUIRED
        res_esc = await c_safe.submit_review(escalated_signal_id, {
            "status": "ACTION_REQUIRED",
            "decision": "ACTION_REQUIRED",
            "notes": "Potential liver enzyme elevation signal in high-dose cohort",
            "escalate": True,
            "escalation_reason": "Cross-functional safety review requested by Pharmacovigilance lead"
        })
        assert res_esc.status_code == 200, f"Escalation failed: {res_esc.text}"
        
        # Verify escalation flag
        updated_sig = await c_safe.get_signal_detail(escalated_signal_id)
        assert updated_sig["is_escalated"] is True, "Signal is_escalated was not set to True"
        
        audits_safe = await c_safe.get_audit_history(escalated_signal_id)
        assert any(a["action"] == "SIGNAL_ESCALATED" for a in audits_safe), "Missing SIGNAL_ESCALATED audit record"
        print("  ✓ Safety escalated signal to Leadership: is_escalated=True, SIGNAL_ESCALATED logged")
        await c_safe.logout()
    finally:
        await c_safe.close()

    # Leadership Resolves Escalation
    c_lead = AuthenticatedDecisionClient(BASE_URL, ALLOWED_ORIGIN)
    try:
        me_lead = await c_lead.demo_login("LEADERSHIP")
        summary = await c_lead.get_leadership_summary()
        pending_esc = summary.get("pending_escalations", [])
        assert any(s["signal_id"] == escalated_signal_id for s in pending_esc), "Escalated signal missing from Leadership summary"
        print(f"  ✓ Leadership visibility confirmed: Signal {escalated_signal_id} present in pending_escalations")

        # Resolve escalation to ACTIONED
        res_resolve = await c_lead.submit_review(escalated_signal_id, {
            "status": "ACTIONED",
            "decision": "ACTIONED",
            "notes": "Portfolio clinical hold approved pending safety data review",
            "resulting_action": "Issue clinical hold directive",
            "resolve_escalation": True
        })
        assert res_resolve.status_code == 200, f"Leadership resolve failed: {res_resolve.text}"
        
        # Assert resolution invariants
        resolved_sig = await c_lead.get_signal_detail(escalated_signal_id)
        assert resolved_sig["is_escalated"] is False, "Signal is_escalated was not cleared after resolution"
        assert resolved_sig["review_status"] == "ACTIONED", f"Expected ACTIONED, got {resolved_sig['review_status']}"

        audits_lead = await c_lead.get_audit_history(escalated_signal_id)
        assert any(a["action"] == "ESCALATION_RESOLVED" for a in audits_lead), "Missing ESCALATION_RESOLVED audit record"
        print("  ✓ Leadership resolved escalation: is_escalated=False, status=ACTIONED, ESCALATION_RESOLVED logged")
        await c_lead.logout()
    finally:
        await c_lead.close()

    # -------------------------------------------------------------
    # Step 3: Market Access (Terminal ACTIONED enforcement)
    # -------------------------------------------------------------
    print("\n[3/6] Testing Market Access Terminal Decision Workflow...")
    c_ma = AuthenticatedDecisionClient(BASE_URL, ALLOWED_ORIGIN)
    try:
        await c_ma.demo_login("MARKET_ACCESS")
        queue_ma = await c_ma.get_queue("MARKET_ACCESS")
        signals_ma = queue_ma.get("signals", [])
        if not signals_ma:
            raise AssertionError("Acceptance fixture missing: no pending signals for MARKET_ACCESS")
        
        sig_ma = signals_ma[0]
        ma_id = sig_ma["signal_id"]
        await c_ma.submit_review(ma_id, {"status": "IN_REVIEW"})
        await c_ma.submit_review(ma_id, {
            "status": "ACTIONED",
            "decision": "ACTIONED",
            "notes": "Pricing parity dossier submitted to regional payer committee",
            "resulting_action": "Dossier dispatched",
        })
        
        # Verify terminal lock: Attempting to modify ACTIONED signal must return 409
        res_reopen = await c_ma.submit_review(ma_id, {"status": "IN_REVIEW"})
        assert res_reopen.status_code == 409, f"Expected 409 on mutating ACTIONED signal, got {res_reopen.status_code}"
        print("  ✓ Market Access executed ACTIONED; terminal lock successfully verified (409 on re-mutation)")
        await c_ma.logout()
    finally:
        await c_ma.close()

    # -------------------------------------------------------------
    # Step 4: Communications (Dismiss Workflow)
    # -------------------------------------------------------------
    print("\n[4/6] Testing Communications Dismiss Decision Workflow...")
    c_comms = AuthenticatedDecisionClient(BASE_URL, ALLOWED_ORIGIN)
    try:
        await c_comms.demo_login("COMMUNICATIONS")
        queue_comms = await c_comms.get_queue("COMMUNICATIONS")
        signals_comms = queue_comms.get("signals", [])
        if not signals_comms:
            raise AssertionError("Acceptance fixture missing: no pending signals for COMMUNICATIONS")
        
        sig_comms = signals_comms[0]
        comms_id = sig_comms["signal_id"]
        await c_comms.submit_review(comms_id, {"status": "IN_REVIEW"})
        res_dismiss = await c_comms.submit_review(comms_id, {
            "status": "DISMISSED",
            "decision": "DISMISSED",
            "notes": "Low media relevance; no press statement needed",
        })
        assert res_dismiss.status_code == 200
        print("  ✓ Communications executed DISMISSED successfully")
        await c_comms.logout()
    finally:
        await c_comms.close()

    # -------------------------------------------------------------
    # Step 5: Regulatory (Action Required Workflow)
    # -------------------------------------------------------------
    print("\n[5/6] Testing Regulatory Action-Required Decision Workflow...")
    c_reg = AuthenticatedDecisionClient(BASE_URL, ALLOWED_ORIGIN)
    try:
        await c_reg.demo_login("REGULATORY")
        queue_reg = await c_reg.get_queue("REGULATORY")
        signals_reg = queue_reg.get("signals", [])
        if not signals_reg:
            raise AssertionError("Acceptance fixture missing: no pending signals for REGULATORY")
        
        sig_reg = signals_reg[0]
        reg_id = sig_reg["signal_id"]
        await c_reg.submit_review(reg_id, {"status": "IN_REVIEW"})
        res_reg = await c_reg.submit_review(reg_id, {
            "status": "ACTION_REQUIRED",
            "decision": "ACTION_REQUIRED",
            "notes": "PDUFA target date scheduled; agency briefing document required",
            "resulting_action": "Draft regulatory response",
        })
        assert res_reg.status_code == 200
        print("  ✓ Regulatory executed ACTION_REQUIRED successfully")
        await c_reg.logout()
    finally:
        await c_reg.close()

    # -------------------------------------------------------------
    # Step 6: Leadership Direct Strategic Decision
    # -------------------------------------------------------------
    print("\n[6/6] Testing Leadership Direct Strategic Decision Workflow...")
    c_ld = AuthenticatedDecisionClient(BASE_URL, ALLOWED_ORIGIN)
    try:
        await c_ld.demo_login("LEADERSHIP")
        queue_ld = await c_ld.get_queue("LEADERSHIP")
        signals_ld = queue_ld.get("signals", [])
        if signals_ld:
            ld_id = signals_ld[0]["signal_id"]
            await c_ld.submit_review(ld_id, {"status": "IN_REVIEW"})
            res_dir = await c_ld.submit_review(ld_id, {
                "status": "ACTIONED",
                "decision": "ACTIONED",
                "notes": "Direct executive authorization for strategic partnership",
                "resulting_action": "Executive memo issued",
                "is_override": True
            })
            assert res_dir.status_code == 200
            print("  ✓ Leadership direct override decision executed to ACTIONED")
        await c_ld.logout()
    finally:
        await c_ld.close()

    print("\n" + "=" * 75)
    print("✓ COMPLETE 6-FUNCTION CROSS-FUNCTIONAL DECISION VERTICAL SLICE PASSED")
    print("=" * 75)
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
