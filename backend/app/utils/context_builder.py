"""复盘聊天上下文构建器。

实现 FD §5.8 build_context(user_id, event_id)：
  1. 近期 followup_messages（短期记忆，≤10 条）
  2. event_snapshots A / B（中期，分别读取，**禁止合并**——罗生门原则）
  3. judge_results（长期，≤1 条）
  4. 可选 review 正文

本模块为**只读**操作，不修改任何表，不依赖 1/2 号 repo。
"""

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.judge import JudgeResult
from app.models.review import Review
from app.models.snapshot import EventSnapshot
from app.repos import followup_repo


@dataclass
class ContextPayload:
    """拼接完成的上下文结构，供 LLM prompt 使用。"""

    snapshot_a: dict | None = None
    snapshot_b: dict | None = None
    judge_result: dict | None = None
    review_content: str | None = None
    recent_messages: list[dict] = field(default_factory=list)
    meta: dict = field(default_factory=dict)


def build_context(
    db: Session,
    user_id: int,
    event_id: int,
    *,
    max_recent_messages: int = 10,
) -> ContextPayload:
    """为 followup chat 构建上下文。

    Parameters
    ----------
    db : Session
        数据库会话。
    user_id : int
        当前用户内部 ID（用于日志/审计，不影响查询范围）。
    event_id : int
        事件内部 ID。
    max_recent_messages : int
        最近对话条数上限，FD §5.9 约定 ≤10。

    Returns
    -------
    ContextPayload
        包含快照、裁判结果、近期对话等上下文；meta 记录各部分命中数量。
    """
    payload = ContextPayload()

    # 1) 近期 followup_messages（短期记忆）— 复用 followup_repo
    messages = followup_repo.get_recent_messages(db, event_id, limit=max_recent_messages)
    payload.recent_messages = []
    for msg in messages:
        payload.recent_messages.append(
            {
                "role": "user",
                "content": msg.user_message,
            }
        )
        payload.recent_messages.append(
            {
                "role": "assistant",
                "content": msg.assistant_reply,
            }
        )

    # 2) event_snapshots A / B（罗生门原则：分别读取，绝不合并）
    stmt_snap = (
        select(EventSnapshot)
        .where(EventSnapshot.event_id == event_id)
    )
    snapshots = list(db.execute(stmt_snap).scalars().all())
    snap_count = 0
    for snap in snapshots:
        snap_dict = {
            "side": snap.side.value if hasattr(snap.side, "value") else str(snap.side),
            "summary": snap.summary,
            "points_a": snap.points_a,
            "points_b": snap.points_b,
        }
        if snap_dict["side"] == "a":
            payload.snapshot_a = snap_dict
            snap_count += 1
        elif snap_dict["side"] == "b":
            payload.snapshot_b = snap_dict
            snap_count += 1

    # 3) judge_results（≤1 条，与 event 1:1）
    stmt_judge = (
        select(JudgeResult)
        .where(JudgeResult.event_id == event_id)
    )
    judge = db.execute(stmt_judge).scalar_one_or_none()
    judge_count = 0
    if judge is not None:
        payload.judge_result = {
            "objective_summary": judge.objective_summary,
            "triggers": judge.triggers,
            "misunderstandings": judge.misunderstandings,
            "advice_for_a": judge.advice_for_a,
            "advice_for_b": judge.advice_for_b,
        }
        judge_count = 1

    # 4) 可选 review 正文
    stmt_review = (
        select(Review)
        .where(Review.event_id == event_id)
    )
    review = db.execute(stmt_review).scalar_one_or_none()
    if review is not None:
        payload.review_content = review.content

    # meta：供 API 响应的 contextMeta 使用
    payload.meta = {
        "recentMessages": len(messages),
        "snapshots": snap_count,
        "judgeResults": judge_count,
    }

    return payload
