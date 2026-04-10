"""LoveMediator 非 AI 功能全面检测脚本。

跳过所有需要 Kimi API 的步骤，只验证前后端非 AI 功能链路。

运行：
  cd backend
  .venv\\Scripts\\python.exe scripts/non_ai_test.py
"""

from __future__ import annotations

import secrets
import sys

import httpx

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE = "http://127.0.0.1:8000"
TIMEOUT = 15.0

passed = 0
failed = 0


def log(status: str, label: str, detail: str = "") -> None:
    global passed, failed
    icon = {"OK": "[OK]", "FAIL": "[FAIL]", "INFO": "[..]", "SKIP": "[--]"}.get(status, "  ")
    print(f"  {icon} {label}" + (f"  ->  {detail}" if detail else ""))
    if status == "OK":
        passed += 1
    elif status == "FAIL":
        failed += 1


def check(condition: bool, label: str, detail: str = "") -> bool:
    log("OK" if condition else "FAIL", label, detail)
    return condition


def unwrap(r: httpx.Response, label: str) -> dict | None:
    ok = check(r.status_code == 200, f"{label} -> HTTP {r.status_code}")
    if not ok:
        log("FAIL", f"  body", r.text[:200])
        return None
    body = r.json()
    check(body.get("code") == 0, f"{label} -> code=0", f"msg={body.get('message')}")
    return body.get("data")


def main() -> None:
    print("=" * 60)
    print("  LoveMediator Non-AI Full Feature Test")
    print("=" * 60)

    c = httpx.Client(base_url=BASE, timeout=TIMEOUT, trust_env=False)

    # ──────────────────────────────────────────────
    print("\n[1] Health & Readiness")
    # ──────────────────────────────────────────────
    r = c.get("/health")
    check(r.status_code == 200, "GET /health")
    r = c.get("/health/ready")
    check(r.status_code == 200 and r.json().get("database") is True, "GET /health/ready (DB ok)")

    # ──────────────────────────────────────────────
    print("\n[2] Auth: Register + Login + Token")
    # ──────────────────────────────────────────────
    suffix = secrets.token_hex(3)
    user_a = {"username": f"test_a_{suffix}", "password": "Test1234!"}
    user_b = {"username": f"test_b_{suffix}", "password": "Test1234!"}

    r = c.post("/api/v1/auth/register", json=user_a)
    data = unwrap(r, f"Register {user_a['username']}")
    check(data is not None and "userId" in data, "Response has userId")

    r = c.post("/api/v1/auth/register", json=user_b)
    unwrap(r, f"Register {user_b['username']}")

    # Duplicate register
    r = c.post("/api/v1/auth/register", json=user_a)
    check(r.status_code == 409, f"Duplicate register -> 409", f"got {r.status_code}")

    r = c.post("/api/v1/auth/login", json=user_a)
    login_a = unwrap(r, f"Login {user_a['username']}")
    token_a = login_a.get("accessToken", "") if login_a else ""
    check(bool(token_a), "Got accessToken")

    r = c.post("/api/v1/auth/login", json=user_b)
    login_b = unwrap(r, f"Login {user_b['username']}")
    token_b = login_b.get("accessToken", "") if login_b else ""
    check(bool(token_b), "Got accessToken for B")

    # Invalid login
    r = c.post("/api/v1/auth/login", json={"username": user_a["username"], "password": "wrongpassword123"})
    check(r.status_code == 401, "Wrong password -> 401", f"got {r.status_code}")

    # Auth header test
    ha = {"Authorization": f"Bearer {token_a}"}
    hb = {"Authorization": f"Bearer {token_b}"}

    r = c.get("/api/v1/auth/me", headers=ha)
    me_data = unwrap(r, "GET /auth/me")
    if me_data:
        check(me_data.get("username") == user_a["username"], "me.username correct")

    # No auth
    r = c.get("/api/v1/auth/me")
    check(r.status_code == 401, "GET /auth/me without token -> 401", f"got {r.status_code}")

    # ──────────────────────────────────────────────
    print("\n[3] Relationships: Invite + Accept + List")
    # ──────────────────────────────────────────────
    r = c.post("/api/v1/relationships/invite", headers=ha)
    invite = unwrap(r, "A creates invite")
    invite_token = invite.get("inviteToken", "") if invite else ""
    check(bool(invite_token), "Got invite token")
    check(bool(invite.get("inviteUrl")), "Got invite URL") if invite else None
    check(invite.get("expiresAt") is not None, "Got expiresAt") if invite else None

    r = c.post("/api/v1/relationships/accept", json={"inviteToken": invite_token}, headers=hb)
    accept = unwrap(r, "B accepts invite")
    rel_id = accept.get("relationshipId", "") if accept else ""
    check(bool(rel_id), "Got relationshipId", rel_id)
    if accept:
        check(accept.get("partnerUsername") == user_a["username"], "partnerUsername correct")
        check(accept.get("status") == "active", "Relationship status=active")

    # List relationships
    r = c.get("/api/v1/relationships", headers=ha)
    list_data = unwrap(r, "A lists relationships")
    if list_data:
        items = list_data.get("items", [])
        check(len(items) >= 1, f"Has {len(items)} relationship(s)")
        first = items[0] if items else {}
        check(first.get("relationshipId") == rel_id, "Listed rel matches accepted rel")

    r = c.get("/api/v1/relationships", headers=hb)
    list_b = unwrap(r, "B lists relationships")
    if list_b:
        check(len(list_b.get("items", [])) >= 1, "B also sees relationship")

    # ──────────────────────────────────────────────
    print("\n[4] Analysis Session: Start (no AI needed)")
    # ──────────────────────────────────────────────
    r = c.post(f"/api/v1/relationships/{rel_id}/analysis-sessions/a", headers=ha)
    session = unwrap(r, "A starts analysis session")
    if session:
        sid = session.get("sessionId", "")
        check(bool(sid), "Got sessionId", sid)
        check(session.get("phase") == "a", "phase=a")
        check(session.get("canCommit") is False, "canCommit initially false")
        check(isinstance(session.get("messages"), list), "messages is list")

    # Duplicate session start (should return same session)
    r = c.post(f"/api/v1/relationships/{rel_id}/analysis-sessions/a", headers=ha)
    session2 = unwrap(r, "A starts session again (idempotent)")
    if session and session2:
        check(session2.get("sessionId") == session.get("sessionId"), "Same sessionId (idempotent)")

    # ──────────────────────────────────────────────
    print("\n[5] Seed Data: Events + Snapshots + Judge")
    # ──────────────────────────────────────────────
    # Login as alice (seed user)
    r = c.post("/api/v1/auth/login", json={"username": "alice", "password": "Secret123!"})
    alice = unwrap(r, "alice login")
    h_alice = {"Authorization": f"Bearer {alice['accessToken']}"} if alice else {}

    r = c.post("/api/v1/auth/login", json={"username": "bob", "password": "Secret123!"})
    bob = unwrap(r, "bob login")
    h_bob = {"Authorization": f"Bearer {bob['accessToken']}"} if bob else {}

    # Invite page (public, no auth needed)
    r = c.get("/api/v1/events/e_seed_waiting_b_1/invite")
    inv = unwrap(r, "GET invite (waiting_b)")
    if inv:
        check(inv.get("status") == "waiting_b", "invite status=waiting_b")
        check(inv.get("eventId") == "e_seed_waiting_b_1", "eventId correct")

    # Snapshot_A (needs auth)
    r = c.get("/api/v1/events/e_seed_waiting_b_1/snapshot-a", headers=h_bob)
    snap = unwrap(r, "GET snapshot-a (waiting_b)")
    if snap:
        sa = snap.get("snapshotA", {})
        check(bool(sa.get("summary")), "Snapshot_A has summary")
        check(isinstance(sa.get("pointsA"), list), "pointsA is list")
        check(isinstance(sa.get("pointsB"), list), "pointsB is list")
        check(len(sa.get("pointsA", [])) > 0, "pointsA not empty")

    # Snapshot_A without auth
    r = c.get("/api/v1/events/e_seed_waiting_b_1/snapshot-a")
    check(r.status_code == 401, "Snapshot_A without auth -> 401", f"got {r.status_code}")

    # Judge result (seed judged event)
    r = c.get("/api/v1/events/e_seed_judged_1/judge-result", headers=h_alice)
    judge = unwrap(r, "GET judge-result (judged)")
    if judge:
        check(bool(judge.get("objectiveSummary")), "Has objectiveSummary")
        analysis = judge.get("analysis", {})
        check(isinstance(analysis.get("triggers"), list), "triggers is list")
        check(isinstance(analysis.get("misunderstandings"), list), "misunderstandings is list")
        check(isinstance(analysis.get("adviceForA"), list), "adviceForA is list")
        check(isinstance(analysis.get("adviceForB"), list), "adviceForB is list")
        check(len(analysis.get("triggers", [])) > 0, "triggers not empty")

    # Nonexistent event
    r = c.get("/api/v1/events/nonexistent_event/invite")
    check(r.status_code == 404, "Nonexistent event -> 404", f"got {r.status_code}")

    # ──────────────────────────────────────────────
    print("\n[6] Calendar API")
    # ──────────────────────────────────────────────
    r = c.get("/api/v1/calendar?month=2026-04&relationshipId=r_seed_ab_1", headers=h_alice)
    cal = unwrap(r, "GET calendar 2026-04")
    if cal:
        check("days" in cal or "entries" in cal or isinstance(cal, dict), "Calendar has data structure")

    r = c.get("/api/v1/calendar/days/2026-04-10/reviews?relationshipId=r_seed_ab_1", headers=h_alice)
    day = unwrap(r, "GET calendar day reviews")

    # Invalid month format
    r = c.get("/api/v1/calendar?month=2026-4&relationshipId=r_seed_ab_1", headers=h_alice)
    check(r.status_code == 422, "Invalid month format -> 422", f"got {r.status_code}")

    # ──────────────────────────────────────────────
    print("\n[7] Permission & Auth Edge Cases")
    # ──────────────────────────────────────────────
    # B cannot start A-side session
    r = c.post(f"/api/v1/relationships/{rel_id}/analysis-sessions/a", headers=hb)
    check(r.status_code in (403, 409), "B cannot start A-side session", f"got {r.status_code}")

    # Expired/invalid token
    r = c.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token_xxxx"})
    check(r.status_code == 401, "Invalid token -> 401", f"got {r.status_code}")

    # ──────────────────────────────────────────────
    print("\n[8] Elf Moderate (mock, no AI needed)")
    # ──────────────────────────────────────────────
    # Short message (low risk)
    r = c.post("/api/v1/elf/moderate", json={"rawMessage": "你好"}, headers=h_alice)
    mod = unwrap(r, "Moderate short message")
    if mod:
        check(mod.get("riskLevel") == "low", "Short message -> low risk")
        check(mod.get("blocked") is False, "Not blocked")

    # Long message (medium risk per mock logic)
    long_msg = "你怎么每次都这样！" * 20  # > 100 chars
    r = c.post("/api/v1/elf/moderate", json={"rawMessage": long_msg}, headers=h_alice)
    mod2 = unwrap(r, "Moderate long message")
    if mod2:
        check(mod2.get("riskLevel") == "medium", "Long message -> medium risk")
        check(bool(mod2.get("suggestedMessage")), "Has suggested message")

    # Empty message
    r = c.post("/api/v1/elf/moderate", json={"rawMessage": ""}, headers=h_alice)
    check(r.status_code in (400, 409, 422), "Empty message rejected", f"got {r.status_code}")

    # ──────────────────────────────────────────────
    print("\n[9] Relationship Cancel Flow")
    # ──────────────────────────────────────────────
    # Create cancel request
    r = c.post(f"/api/v1/relationships/{rel_id}/cancel-request", headers=ha)
    cancel_req = unwrap(r, "A creates cancel request")
    if cancel_req:
        cancel_token = cancel_req.get("cancelToken", "")
        check(bool(cancel_token), "Got cancel token")
        check(bool(cancel_req.get("cancelUrl")), "Got cancel URL")

    # ──────────────────────────────────────────────
    print("\n[10] OpenAPI / Docs")
    # ──────────────────────────────────────────────
    r = c.get("/docs")
    check(r.status_code == 200, "GET /docs (Swagger UI)")

    r = c.get("/openapi.json")
    check(r.status_code == 200, "GET /openapi.json")
    if r.status_code == 200:
        spec = r.json()
        paths = spec.get("paths", {})
        check(len(paths) > 10, f"OpenAPI has {len(paths)} paths")

    # ──────────────────────────────────────────────
    print("\n[11] Frontend Static Serving")
    # ──────────────────────────────────────────────
    # Check frontend is accessible
    fr = httpx.get("http://localhost:5173/", timeout=5, trust_env=False)
    check(fr.status_code == 200, "Frontend / -> 200")
    check("<!DOCTYPE html>" in fr.text or "<html" in fr.text, "Frontend returns HTML")

    fr = httpx.get("http://localhost:5173/app/mediation", timeout=5, trust_env=False)
    check(fr.status_code == 200, "Frontend /app/mediation -> 200")

    fr = httpx.get("http://localhost:5173/invite/e_seed_waiting_b_1", timeout=5, trust_env=False)
    check(fr.status_code == 200, "Frontend /invite/... -> 200")

    c.close()

    # ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"  Result: [OK] {passed} passed  |  [FAIL] {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)
    else:
        print("\n  All non-AI features are working correctly!")


if __name__ == "__main__":
    main()
