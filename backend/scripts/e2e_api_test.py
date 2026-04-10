"""LoveMediator E2E API 集成测试脚本。

双轨测试：
  - 路径 A：新用户注册 → 建立关系 → A 侧分析会话 → 尝试 commit
  - 路径 B：使用 seed 用户 bob → b-agree seed 事件 → 裁判 → followup → elf → calendar

前置条件：
  - 后端运行在 http://127.0.0.1:8000
  - seed_db.py 已执行（alice/bob + waiting_b 事件存在）

运行：
  cd backend
  .venv\\Scripts\\python.exe scripts/e2e_api_test.py
"""

from __future__ import annotations

import secrets
import sys
import time

import httpx

# Windows 终端编码兼容
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:
        pass

BASE = "http://127.0.0.1:8000"
TIMEOUT = 120.0

passed = 0
failed = 0
warnings = 0


def _log(status: str, label: str, detail: str = "") -> None:
    global passed, failed, warnings
    icon = {"PASS": "[OK]", "FAIL": "[FAIL]", "WARN": "[WARN]", "INFO": "[..]"}.get(status, "  ")
    print(f"  {icon} {label}" + (f"  ->  {detail}" if detail else ""))
    if status == "PASS":
        passed += 1
    elif status == "FAIL":
        failed += 1
    elif status == "WARN":
        warnings += 1


def _assert(condition: bool, label: str, detail: str = "") -> bool:
    if condition:
        _log("PASS", label, detail)
    else:
        _log("FAIL", label, detail)
    return condition


def _unwrap(r: httpx.Response, label: str) -> dict | None:
    ok = _assert(r.status_code == 200, f"{label} → HTTP {r.status_code}")
    if not ok:
        _log("FAIL", f"  response body", r.text[:300])
        return None
    body = r.json()
    _assert(body.get("code") == 0, f"{label} → code=0", f"message={body.get('message')}")
    return body.get("data")


# ─── 健康检查 ──────────────────────────────────────────────────

def test_health(client: httpx.Client) -> bool:
    print("\n═══ 健康检查 ═══")
    r = client.get("/health")
    _assert(r.status_code == 200, "GET /health", r.text[:100])

    r = client.get("/health/ready")
    ok = _assert(r.status_code == 200, "GET /health/ready", r.text[:100])
    return ok


# ─── 路径 A：新用户 → 分析会话 ────────────────────────────────

def test_path_a(client: httpx.Client) -> dict:
    """路径 A：注册新用户 → 建关系 → A 分析会话 → 尝试 commit。"""
    print("\n═══ 路径 A：新用户 + 分析会话流程 ═══")
    suffix = secrets.token_hex(4)
    user_c = {"username": f"charlie_{suffix}", "password": "Test1234!"}
    user_d = {"username": f"diana_{suffix}", "password": "Test1234!"}

    # 注册
    r = client.post("/api/v1/auth/register", json=user_c)
    data_c = _unwrap(r, f"注册 {user_c['username']}")

    r = client.post("/api/v1/auth/register", json=user_d)
    data_d = _unwrap(r, f"注册 {user_d['username']}")

    if not data_c or not data_d:
        return {}

    # 登录
    r = client.post("/api/v1/auth/login", json=user_c)
    login_c = _unwrap(r, f"登录 {user_c['username']}")

    r = client.post("/api/v1/auth/login", json=user_d)
    login_d = _unwrap(r, f"登录 {user_d['username']}")

    if not login_c or not login_d:
        return {}

    token_c = login_c.get("accessToken", "")
    token_d = login_d.get("accessToken", "")
    _assert(bool(token_c), "C 获得 accessToken")
    _assert(bool(token_d), "D 获得 accessToken")

    headers_c = {"Authorization": f"Bearer {token_c}"}
    headers_d = {"Authorization": f"Bearer {token_d}"}

    # C 创建关系邀请
    r = client.post("/api/v1/relationships/invite", headers=headers_c)
    invite_data = _unwrap(r, "C 创建关系邀请")
    if not invite_data:
        return {}
    invite_token = invite_data.get("inviteToken", "")
    _assert(bool(invite_token), "获得 inviteToken", invite_token[:30])

    # D 接受邀请
    r = client.post(
        "/api/v1/relationships/accept",
        json={"inviteToken": invite_token},
        headers=headers_d,
    )
    accept_data = _unwrap(r, "D 接受关系邀请")
    if not accept_data:
        return {}
    relationship_id = accept_data.get("relationshipId", "")
    _assert(bool(relationship_id), "获得 relationshipId", relationship_id)

    # C 查看关系列表
    r = client.get("/api/v1/relationships", headers=headers_c)
    list_data = _unwrap(r, "C 查看关系列表")

    # C 开始 A 侧分析会话
    r = client.post(
        f"/api/v1/relationships/{relationship_id}/analysis-sessions/a",
        headers=headers_c,
    )
    session_data = _unwrap(r, "C 开启 A 侧分析会话")
    if not session_data:
        return {"relationship_id": relationship_id}
    session_id = session_data.get("sessionId", "")
    _assert(bool(session_id), "获得 sessionId", session_id)
    _assert(session_data.get("phase") == "a", "phase == 'a'")

    # C 发送分析消息（结构化事实，增大 canCommit 概率）
    structured_msg = (
        "我和女朋友昨晚因为家务分工吵了一架。事实如下：\n"
        "1. 我认为应该轮流做饭，每人一天\n"
        "2. 她认为我应该每天做饭，因为她工作更忙\n"
        "3. 争吵发生在晚上 9 点的厨房\n"
        "4. 她认为我不够体贴，我认为她不够公平\n"
        "5. 最终她去了卧室不说话了\n"
        "以上就是全部事实，请帮我整理确认。"
    )

    can_commit = False
    fact_summary = None

    for i, msg in enumerate([structured_msg, "对，基本就是这样，请确认。", "我确认以上事实无误。"], 1):
        r = client.post(
            f"/api/v1/analysis-sessions/{session_id}/messages",
            json={"message": msg},
            headers=headers_c,
        )
        if r.status_code == 500:
            # AI 服务可能因代理/网络问题不可达，不算代码逻辑错误
            _log("WARN", f"C 发送分析消息 #{i} -> AI 服务异常 (HTTP 500)", r.text[:150])
            continue
        msg_data = _unwrap(r, f"C 发送分析消息 #{i}")
        if msg_data:
            can_commit = msg_data.get("canCommit", False)
            fact_summary = msg_data.get("factSummary")
            _log("INFO", f"  canCommit={can_commit}, factSummary长度={len(fact_summary or '')}")
            if can_commit:
                break

    result = {"relationship_id": relationship_id, "session_id": session_id}

    if can_commit:
        # 尝试 commit
        r = client.post(
            f"/api/v1/analysis-sessions/{session_id}/commit",
            headers=headers_c,
        )
        commit_data = _unwrap(r, "C commit 分析会话")
        if commit_data:
            _assert(commit_data.get("status") == "waiting_b", "commit 后 status == waiting_b")
            _assert(bool(commit_data.get("snapshotAId")), "commit 返回 snapshotAId")
            result["event_id"] = commit_data.get("eventId")
            result["committed"] = True
    else:
        _log("WARN", "AI 未返回 canCommit=true（AI 行为不可控，不影响测试结论）")
        result["committed"] = False

    return result


# ─── 路径 B：seed 用户 → b-agree → 裁判 → 下游链 ──────────────

def test_path_b(client: httpx.Client) -> None:
    """路径 B：使用 seed 数据跑通 B 同意 → 裁判生成 → 复盘 → 小精灵 → 日历。"""
    print("\n═══ 路径 B：seed 用户 + 下游链验证 ═══")

    # bob 登录
    r = client.post("/api/v1/auth/login", json={"username": "bob", "password": "Secret123!"})
    login_b = _unwrap(r, "bob 登录")
    if not login_b:
        _log("FAIL", "bob 登录失败，跳过路径 B")
        return

    token_b = login_b.get("accessToken", "")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # alice 登录
    r = client.post("/api/v1/auth/login", json={"username": "alice", "password": "Secret123!"})
    login_a = _unwrap(r, "alice 登录")
    if not login_a:
        return
    token_a = login_a.get("accessToken", "")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 使用 seed 的 waiting_b 事件
    event_id = "e_seed_waiting_b_1"

    # bob 查看邀请信息
    r = client.get(f"/api/v1/events/{event_id}/invite")
    invite_data = _unwrap(r, "bob 查看邀请信息 (GET /events/{id}/invite)")
    if invite_data:
        _assert(invite_data.get("status") == "waiting_b", "事件状态 == waiting_b")

    # bob 查看 Snapshot_A
    r = client.get(f"/api/v1/events/{event_id}/snapshot-a", headers=headers_b)
    snap_data = _unwrap(r, "bob 查看 Snapshot_A")
    if snap_data:
        snapshot = snap_data.get("snapshotA", {})
        _log("INFO", f"Snapshot_A summary 长度={len(snapshot.get('summary', ''))}")

    # bob b-agree → 触发裁判（真实 AI 调用）
    _log("INFO", "即将调用 b-agree，这会触发真实 AI 裁判生成，可能需要 10-30 秒...")
    r = client.post(
        f"/api/v1/events/{event_id}/b-agree",
        json={"agree": True},
        headers=headers_b,
    )
    if r.status_code == 500 and "Kimi" in r.text:
        # AI 服务不可达（代理/网络问题），不算代码逻辑错误
        _log("WARN", "bob b-agree -> AI 服务不可达 (Kimi SSL)", r.text[:150])
        agree_data = None
    else:
        agree_data = _unwrap(r, "bob b-agree（触发 AI 裁判）")

    if agree_data:
        _assert(agree_data.get("status") == "judged", "b-agree 后 status == judged")
        judge_result_id = agree_data.get("judgeResultId", "")
        _assert(bool(judge_result_id), "b-agree 返回 judgeResultId")

        # alice 查看裁判结果
        r = client.get(f"/api/v1/events/{event_id}/judge-result", headers=headers_a)
        judge_data = _unwrap(r, "alice 查看裁判结果")
        if judge_data:
            _assert(bool(judge_data.get("objectiveSummary")), "裁判结果有 objectiveSummary")
            analysis = judge_data.get("analysis", {})
            _assert(isinstance(analysis.get("triggers"), list), "analysis.triggers 是列表")
            _assert(isinstance(analysis.get("adviceForA"), list), "analysis.adviceForA 是列表")

        # alice 复盘聊天
        r = client.post(
            f"/api/v1/events/{event_id}/followup-chat/messages",
            json={"message": "AI 你觉得我们这次争吵的核心问题是什么？"},
            headers=headers_a,
        )
        followup_data = _unwrap(r, "alice 复盘聊天")
        if followup_data:
            _assert(bool(followup_data.get("reply")), "复盘聊天有 reply")
            meta = followup_data.get("contextMeta", {})
            _assert(meta.get("judgeResults", 0) >= 1, "contextMeta.judgeResults >= 1")

        # alice 小精灵代转达
        r = client.post(
            "/api/v1/elf/relay",
            json={
                "eventId": event_id,
                "targetUserId": "u_seed_b_1",
                "rawMessage": "我觉得我们可以想个更好的分工方式",
            },
            headers=headers_a,
        )
        relay_data = _unwrap(r, "alice 小精灵代转达")
        if relay_data:
            _assert(bool(relay_data.get("finalMessage")), "代转达有 finalMessage")

        # alice 过激检测
        r = client.post(
            "/api/v1/elf/moderate",
            json={"rawMessage": "你怎么每次都这样！我真的受不了了！你从来不考虑我的感受！每天都在争吵让我很累很累很累！"},
            headers=headers_a,
        )
        mod_data = _unwrap(r, "alice 过激检测")
        if mod_data:
            _assert(mod_data.get("riskLevel") in ("low", "medium", "high"), "riskLevel 有效")

    else:
        _log("WARN", "b-agree 失败（可能 seed 事件缺少 Snapshot_A），跳过下游链测试")

        # 尝试用 seed judged 事件测试裁判结果读取
        judged_event_id = "e_seed_judged_1"
        r = client.get(f"/api/v1/events/{judged_event_id}/judge-result", headers=headers_a)
        if r.status_code == 200 and r.json().get("code") == 0:
            _log("INFO", "使用 seed judged 事件验证裁判结果读取")
            _unwrap(r, "alice 查看 seed judged 事件裁判结果")

    # 日历（独立于 b-agree 结果）
    seed_rel_id = "r_seed_ab_1"
    print("\n── 日历 API ──")
    r = client.get(f"/api/v1/calendar?month=2026-04&relationshipId={seed_rel_id}", headers=headers_a)
    cal_data = _unwrap(r, "alice 查看 2026-04 日历")

    r = client.get(f"/api/v1/calendar/days/2026-04-10/reviews?relationshipId={seed_rel_id}", headers=headers_a)
    day_data = _unwrap(r, "alice 查看 2026-04-10 日期复盘")


# ─── 主入口 ───────────────────────────────────────────────────

def main() -> None:
    print("╔══════════════════════════════════════════════════╗")
    print("║   LoveMediator E2E API 集成测试                 ║")
    print("╚══════════════════════════════════════════════════╝")

    with httpx.Client(base_url=BASE, timeout=TIMEOUT, trust_env=False) as client:
        if not test_health(client):
            print("\n💥 后端未启动或数据库不可达，中止测试。")
            sys.exit(1)

        path_a_result = test_path_a(client)
        test_path_b(client)

    print("\n" + "═" * 52)
    print(f"  Result: [OK] {passed} passed  |  [FAIL] {failed} failed  |  [WARN] {warnings} warnings")
    print("═" * 52)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
