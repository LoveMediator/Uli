"""B 不同意路径 完整端到端联调。

流程：
  1. 注册 A + B → 建立关系
  2. A 开启分析会话 → 发消息 → commit → waiting_b
  3. B 查看 Snapshot_A → 不同意
  4. B 开启 B 侧分析会话 (POST /events/{id}/analysis-sessions/b)
  5. B 发送 B 侧事实描述
  6. B commit B 侧分析会话 → 触发 AI 裁判 → judged
  7. A 查看裁判结果
  8. A 复盘聊天
  9. A 小精灵代转达

运行:
  cd backend
  .venv\\Scripts\\python.exe scripts/test_b_disagree_flow.py
"""
from __future__ import annotations

import secrets
import sys
import time

import httpx

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE = "http://127.0.0.1:8000"
c = httpx.Client(base_url=BASE, timeout=120, trust_env=False)
suffix = secrets.token_hex(3)

passed = 0
failed = 0
step = 0


def log_step(title: str) -> None:
    global step
    step += 1
    print(f"\n{'='*60}")
    print(f"  Step {step}: {title}")
    print(f"{'='*60}")


def ok(label: str, detail: str = "") -> None:
    global passed
    passed += 1
    print(f"  [OK] {label}" + (f"  ->  {detail}" if detail else ""))


def fail(label: str, detail: str = "") -> None:
    global failed
    failed += 1
    print(f"  [FAIL] {label}" + (f"  ->  {detail}" if detail else ""))


def check(condition: bool, label: str, detail: str = "") -> bool:
    if condition:
        ok(label, detail)
    else:
        fail(label, detail)
    return condition


def must(r: httpx.Response, label: str) -> dict:
    """Unwrap response, abort on failure."""
    if not check(r.status_code == 200, f"{label} -> HTTP {r.status_code}"):
        fail("  body", r.text[:300])
        print(f"\n  ABORT: {label} failed, cannot continue.")
        summary()
        sys.exit(1)
    body = r.json()
    check(body.get("code") == 0, f"{label} -> code=0", f"msg={body.get('message')}")
    return body["data"]


def summary() -> None:
    print(f"\n{'='*60}")
    print(f"  RESULT: [OK] {passed} passed  |  [FAIL] {failed} failed")
    print(f"{'='*60}")


# ======================================================================
# Step 1: Register + Login
# ======================================================================
log_step("Register + Login")
user_a = {"username": f"ava_{suffix}", "password": "Test1234!"}
user_b = {"username": f"ben_{suffix}", "password": "Test1234!"}

d = must(c.post("/api/v1/auth/register", json=user_a), f"Register {user_a['username']}")
d = must(c.post("/api/v1/auth/register", json=user_b), f"Register {user_b['username']}")

la = must(c.post("/api/v1/auth/login", json=user_a), f"Login {user_a['username']}")
lb = must(c.post("/api/v1/auth/login", json=user_b), f"Login {user_b['username']}")

ha = {"Authorization": f"Bearer {la['accessToken']}"}
hb = {"Authorization": f"Bearer {lb['accessToken']}"}
ok("Both users logged in")

# ======================================================================
# Step 2: Create Relationship
# ======================================================================
log_step("Create Relationship")
inv = must(c.post("/api/v1/relationships/invite", headers=ha), "A creates invite")
invite_token = inv["inviteToken"]
ok("Invite token obtained", invite_token[:30])

acc = must(c.post("/api/v1/relationships/accept", json={"inviteToken": invite_token}, headers=hb), "B accepts invite")
rel_id = acc["relationshipId"]
check(acc.get("status") == "active", "Relationship active", rel_id)

# ======================================================================
# Step 3: A opens analysis session + sends message + commit
# ======================================================================
log_step("A: Analysis Session -> Commit")
sess_a = must(
    c.post(f"/api/v1/relationships/{rel_id}/analysis-sessions/a", headers=ha),
    "A starts analysis session"
)
sid_a = sess_a["sessionId"]
check(sess_a["phase"] == "a", "phase=a")

msg_a = (
    "我和男朋友因为旅行计划吵架了。事实如下：\n"
    "1. 我提议五一去云南旅行\n"
    "2. 他想宅在家打游戏\n"
    "3. 我提前两周告知了他但他说没听到\n"
    "4. 他觉得我总是自作主张\n"
    "5. 最终我们大吵了一架，谁都不让步\n"
    "以上就是全部事实。"
)
msg_resp = must(
    c.post(f"/api/v1/analysis-sessions/{sid_a}/messages", json={"message": msg_a}, headers=ha),
    "A sends fact message"
)
can_commit = msg_resp.get("canCommit", False)
print(f"  [..] canCommit={can_commit}, reply_len={len(msg_resp.get('reply', ''))}")

if not can_commit:
    # Send one more message
    msg2 = must(
        c.post(f"/api/v1/analysis-sessions/{sid_a}/messages", json={"message": "对，事情就是这样，我确认。"}, headers=ha),
        "A sends confirmation"
    )
    can_commit = msg2.get("canCommit", False)
    print(f"  [..] canCommit={can_commit}")

if not can_commit:
    fail("AI did not return canCommit=true after 2 messages")
    print("  Attempting commit anyway (may fail)...")

commit_a = must(
    c.post(f"/api/v1/analysis-sessions/{sid_a}/commit", headers=ha),
    "A commits analysis session"
)
event_id = commit_a["eventId"]
check(commit_a["status"] == "waiting_b", "Status = waiting_b")
check(bool(commit_a.get("snapshotAId")), "snapshotAId returned", commit_a.get("snapshotAId", ""))
ok("A-side complete", f"eventId={event_id}")

# ======================================================================
# Step 4: B views Snapshot_A
# ======================================================================
log_step("B: View Snapshot_A")
snap = must(c.get(f"/api/v1/events/{event_id}/snapshot-a", headers=hb), "B views Snapshot_A")
sa = snap.get("snapshotA", {})
check(bool(sa.get("summary")), "Snapshot_A has summary", sa.get("summary", "")[:60])
check(len(sa.get("pointsA", [])) > 0, f"pointsA has {len(sa.get('pointsA', []))} items")

# ======================================================================
# Step 5: B disagrees -> Opens B-side analysis session
# ======================================================================
log_step("B: Open B-side Analysis Session (DISAGREE)")
sess_b = must(
    c.post(f"/api/v1/events/{event_id}/analysis-sessions/b", headers=hb),
    "B starts B-side analysis session"
)
sid_b = sess_b["sessionId"]
check(sess_b["phase"] == "b", "phase=b")
check(sid_b != sid_a, "B session != A session")
ok("B-side session opened", f"sessionId={sid_b}")

# ======================================================================
# Step 6: B sends messages (B-side facts)
# ======================================================================
log_step("B: Send B-side facts")
msg_b = (
    "我觉得她的描述不完全准确，以下是我的看法：\n"
    "1. 她确实提过五一去云南，但只是随口说说，不是正式提议\n"
    "2. 我不是想打游戏，是那段时间工作太累需要休息\n"
    "3. 她说提前两周告知，但其实是前一天才确定具体行程\n"
    "4. 我不是觉得她自作主张，而是希望她能多考虑我的感受\n"
    "5. 吵架时她有些情绪化，说了一些很伤人的话\n"
    "以上就是我的完整观点。"
)
msg_b_resp = must(
    c.post(f"/api/v1/analysis-sessions/{sid_b}/messages", json={"message": msg_b}, headers=hb),
    "B sends B-side facts"
)
can_commit_b = msg_b_resp.get("canCommit", False)
print(f"  [..] canCommit={can_commit_b}, reply_len={len(msg_b_resp.get('reply', ''))}")

if not can_commit_b:
    msg_b2 = must(
        c.post(f"/api/v1/analysis-sessions/{sid_b}/messages", json={"message": "对，这是我的完整看法，我确认。"}, headers=hb),
        "B sends confirmation"
    )
    can_commit_b = msg_b2.get("canCommit", False)
    print(f"  [..] canCommit={can_commit_b}")

# ======================================================================
# Step 7: B commits -> triggers AI judge
# ======================================================================
log_step("B: Commit B-side -> AI Judge Generation")
print("  [..] This will trigger AI judge. May take 20-60 seconds...")
t0 = time.time()
commit_b = must(
    c.post(f"/api/v1/analysis-sessions/{sid_b}/commit", headers=hb),
    "B commits B-side analysis session"
)
elapsed = time.time() - t0
print(f"  [..] Judge generation took {elapsed:.1f}s")

check(commit_b["status"] == "judged", "Status = judged", commit_b["status"])
check(bool(commit_b.get("snapshotBId")), "snapshotBId returned", commit_b.get("snapshotBId", ""))
check(bool(commit_b.get("judgeResultId")), "judgeResultId returned", commit_b.get("judgeResultId", ""))

# ======================================================================
# Step 8: A views Judge Result
# ======================================================================
log_step("A: View Judge Result")
jr = must(c.get(f"/api/v1/events/{event_id}/judge-result", headers=ha), "A views judge result")
check(bool(jr.get("objectiveSummary")), "Has objectiveSummary", jr.get("objectiveSummary", "")[:80])

analysis = jr.get("analysis", {})
triggers = analysis.get("triggers", [])
misunderstandings = analysis.get("misunderstandings", [])
advice_a = analysis.get("adviceForA", [])
advice_b = analysis.get("adviceForB", [])

check(len(triggers) > 0, f"triggers: {len(triggers)} items")
check(len(misunderstandings) > 0, f"misunderstandings: {len(misunderstandings)} items")
check(len(advice_a) > 0, f"adviceForA: {len(advice_a)} items")
check(len(advice_b) > 0, f"adviceForB: {len(advice_b)} items")

print(f"\n  --- Judge Summary ---")
print(f"  {jr.get('objectiveSummary', '')[:200]}")
print(f"  Triggers: {triggers[:2]}")
print(f"  Advice A: {advice_a[:1]}")
print(f"  Advice B: {advice_b[:1]}")

# ======================================================================
# Step 9: A followup chat (post-judge)
# ======================================================================
log_step("A: Followup Chat")
fu = c.post(
    f"/api/v1/events/{event_id}/followup-chat/messages",
    json={"message": "谢谢你的分析。你觉得我们这次争吵的核心矛盾是什么？"},
    headers=ha,
)
if fu.status_code == 200 and fu.json().get("code") == 0:
    fu_data = fu.json()["data"]
    ok("Followup chat success", f"reply_len={len(fu_data.get('reply', ''))}")
    meta = fu_data.get("contextMeta", {})
    check(meta.get("judgeResults", 0) >= 1, f"contextMeta.judgeResults={meta.get('judgeResults')}")
    check(meta.get("snapshots", 0) >= 2, f"contextMeta.snapshots={meta.get('snapshots')} (should be >=2 for A+B)")
    print(f"  Reply: {fu_data.get('reply', '')[:120]}...")
else:
    fail("Followup chat", f"HTTP {fu.status_code}, body={fu.text[:200]}")

# ======================================================================
# Step 10: Elf moderate + relay
# ======================================================================
log_step("A: Elf Moderate + Relay")
mod = must(
    c.post("/api/v1/elf/moderate", json={"rawMessage": "给他说我真的很生气，他从来不考虑我的感受！"}, headers=ha),
    "A moderate message"
)
check(mod.get("riskLevel") in ("low", "medium", "high"), f"riskLevel={mod.get('riskLevel')}")
if mod.get("suggestedMessage"):
    ok("Has softened message", mod["suggestedMessage"][:80])

# Get B's publicId from relationship list
rels = must(c.get("/api/v1/relationships", headers=ha), "A lists relationships")
partner_public_id = ""
for rel in rels.get("items", []):
    if rel.get("relationshipId") == rel_id:
        partner_public_id = rel.get("partnerUserId", "")
        break

if partner_public_id:
    relay = c.post(
        "/api/v1/elf/relay",
        json={
            "eventId": event_id,
            "targetUserId": partner_public_id,
            "rawMessage": "我觉得我们都需要冷静一下，找个时间好好谈谈",
        },
        headers=ha,
    )
    if relay.status_code == 200 and relay.json().get("code") == 0:
        rd = relay.json()["data"]
        ok("Elf relay success", f"finalMessage_len={len(rd.get('finalMessage', ''))}")
    else:
        fail("Elf relay", f"HTTP {relay.status_code}, body={relay.text[:200]}")
else:
    fail("Could not find partner publicId for relay")

# ======================================================================
# Final Summary
# ======================================================================
c.close()
summary()

if failed == 0:
    print("\n  B-DISAGREE FULL CHAIN: ALL STEPS PASSED!")
    print("  The complete Rashomon flow with B-side analysis is verified.\n")
else:
    print(f"\n  {failed} step(s) need attention.\n")
    sys.exit(1)
