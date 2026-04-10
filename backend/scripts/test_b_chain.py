"""验证 B 侧完整链路：b-agree → 裁判 → 复盘 → 小精灵。

使用 E2E 测试中路径 A 刚创建的事件（charlie + diana）。
"""
from __future__ import annotations
import sys
import httpx

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE = "http://127.0.0.1:8000"
c = httpx.Client(base_url=BASE, timeout=120, trust_env=False)

# 查找最近一次路径 A 的 charlie/diana 用户
# 先尝试已知的用户名
test_users = []
for suffix in ["dbe489f6", "f642a7ca", "5b0c96dc", "591d65ed", "14298dff"]:
    username = f"charlie_{suffix}"
    r = c.post("/api/v1/auth/login", json={"username": username, "password": "Test1234!"})
    if r.status_code == 200:
        test_users.append(suffix)
        print(f"[OK] Found test user pair: charlie_{suffix} / diana_{suffix}")
        break

if not test_users:
    print("[FAIL] No test user pair found. Run e2e_api_test.py first.")
    sys.exit(1)

suffix = test_users[0]

# Login both
r = c.post("/api/v1/auth/login", json={"username": f"charlie_{suffix}", "password": "Test1234!"})
token_c = r.json()["data"]["accessToken"]
hc = {"Authorization": f"Bearer {token_c}"}

r = c.post("/api/v1/auth/login", json={"username": f"diana_{suffix}", "password": "Test1234!"})
token_d = r.json()["data"]["accessToken"]
hd = {"Authorization": f"Bearer {token_d}"}

# Diana 查看关系列表，找到 openEventId
r = c.get("/api/v1/relationships", headers=hd)
rels = r.json()["data"]["items"]
print(f"\nDiana has {len(rels)} relationship(s)")

event_id = None
for rel in rels:
    ce = rel.get("currentEvent")
    if ce and ce.get("eventId"):
        event_id = ce["eventId"]
        print(f"  Found open event: {event_id} (status={ce.get('status')})")
        break

if not event_id:
    print("[FAIL] No open event found for diana. The path A commit may not have succeeded.")
    sys.exit(1)

# 1. Diana 查看邀请
r = c.get(f"/api/v1/events/{event_id}/invite")
inv = r.json()["data"]
print(f"\n[1] Event invite: status={inv['status']}")

# 2. Diana 查看 Snapshot_A
r = c.get(f"/api/v1/events/{event_id}/snapshot-a", headers=hd)
if r.status_code == 200:
    snap = r.json()["data"]["snapshotA"]
    print(f"[2] Snapshot_A: summary={snap['summary'][:60]}...")
    print(f"    pointsA: {snap['pointsA']}")
else:
    print(f"[2] Snapshot_A: FAIL {r.status_code}")

# 3. Diana b-agree (触发 AI 裁判)
print("\n[3] Triggering b-agree (AI judge generation)...")
r = c.post(f"/api/v1/events/{event_id}/b-agree", json={"agree": True}, headers=hd)
result = r.json()
print(f"    HTTP {r.status_code}, code={result['code']}, message={result.get('message')}")

if result["code"] == 0:
    data = result["data"]
    print(f"    status={data.get('status')}")
    print(f"    judgeResultId={data.get('judgeResultId')}")

    # 4. Charlie 查看裁判结果
    r = c.get(f"/api/v1/events/{event_id}/judge-result", headers=hc)
    jr = r.json()
    print(f"\n[4] Judge result: code={jr['code']}")
    if jr["code"] == 0:
        jd = jr["data"]
        print(f"    objectiveSummary: {jd['objectiveSummary'][:80]}...")
        analysis = jd.get("analysis", {})
        print(f"    triggers: {analysis.get('triggers')}")
        print(f"    misunderstandings: {analysis.get('misunderstandings')}")
        print(f"    adviceForA: {analysis.get('adviceForA')}")
        print(f"    adviceForB: {analysis.get('adviceForB')}")

    # 5. Charlie 复盘聊天
    r = c.post(
        f"/api/v1/events/{event_id}/followup-chat/messages",
        json={"message": "你觉得我们这次争吵的核心问题是什么？"},
        headers=hc,
    )
    fu = r.json()
    print(f"\n[5] Followup chat: code={fu['code']}")
    if fu["code"] == 0:
        print(f"    reply: {fu['data']['reply'][:100]}...")
        meta = fu["data"].get("contextMeta", {})
        print(f"    contextMeta: {meta}")

    # 6. Charlie 小精灵代转达
    # 获取 diana 的 publicId
    r = c.get("/api/v1/auth/me", headers=hd)
    # 没有 /auth/me，用 relationships 获取 partnerPublicId
    r = c.get("/api/v1/relationships", headers=hc)
    partner_id = r.json()["data"]["items"][0].get("partnerPublicId", "")
    
    r = c.post(
        "/api/v1/elf/relay",
        json={
            "eventId": event_id,
            "targetUserId": partner_id,
            "rawMessage": "我觉得我们可以想个更好的分工方式，你怎么看？",
        },
        headers=hc,
    )
    er = r.json()
    print(f"\n[6] Elf relay: code={er['code']}")
    if er["code"] == 0:
        print(f"    finalMessage: {er['data']['finalMessage'][:100]}...")

    print("\n" + "=" * 50)
    print("  ALL STEPS COMPLETED SUCCESSFULLY!")
    print("=" * 50)
else:
    print(f"\n[FAIL] b-agree failed: {result.get('message')}")
    if result["code"] == 1003 and "已生成" in result.get("message", ""):
        print("  (裁判在上次运行时已生成。请用新的 seed 重试)")

c.close()
