"""Review 业务服务层。

负责复盘详情、编辑、以及 judged 后自动创建 review + calendar_entry 的编排。
权限校验：通过 relationship 的 user_a_id / user_b_id 判断当前用户是否为关系参与方。
"""

from datetime import date

from sqlalchemy.orm import Session

from app.constants.error_codes import INVALID_PARAMS, NOT_FOUND
from app.core.errors import AppError
from app.models.review import Review
from app.repos import review_repo
from app.utils.ids import generate_public_id
from app.utils.permissions import assert_relationship_member


def _get_review_with_permission(db: Session, user_id: int, review_public_id: str) -> Review:
    """查询复盘并校验权限（内部复用）。"""
    review = review_repo.get_review_by_public_id(db, review_public_id)
    if review is None:
        raise AppError("复盘不存在", code=NOT_FOUND)
    assert_relationship_member(db, review.relationship_id, user_id)
    return review


def get_review(db: Session, user_id: int, review_public_id: str) -> Review:
    """按 public_id 获取复盘详情，含权限校验。

    对应 API §6.3 GET /reviews/{reviewId}。
    """
    return _get_review_with_permission(db, user_id, review_public_id)


def update_review(
    db: Session,
    user_id: int,
    review_public_id: str,
    content: str,
) -> Review:
    """编辑复盘正文，同时写入 review_versions。

    对应 API §6.4 PUT /reviews/{reviewId}。
    同一事务内完成：更新正文 + 插入版本记录（DB §6.4）。
    """
    review = _get_review_with_permission(db, user_id, review_public_id)
    if not content or not content.strip():
        raise AppError("复盘内容不能为空", code=INVALID_PARAMS)

    latest_version_no = review_repo.get_latest_version_no(db, review.id)
    new_version_no = latest_version_no + 1

    review_repo.update_review_content(
        db,
        review,
        content=content,
        updated_by_user_id=user_id,
    )
    review_repo.create_review_version(
        db,
        review_id=review.id,
        version_no=new_version_no,
        content=content,
        edited_by_user_id=user_id,
    )

    db.commit()
    db.refresh(review)
    return review


def create_review_from_judge(
    db: Session,
    *,
    event_id: int,
    relationship_id: int,
    content: str,
    created_by_user_id: int | None = None,
    calendar_date: date | None = None,
) -> Review:
    """judged 后创建 review 并自动入历。

    供 event_service._execute_judge 在裁判完成后调用。
    本函数只做 flush（不 commit），由调用方统一管理事务边界。

    Parameters
    ----------
    calendar_date :
        入历日期；若未指定，默认使用当天。
    """
    if not content or not content.strip():
        raise AppError("复盘内容不能为空", code=INVALID_PARAMS)

    existing = review_repo.get_review_by_event_id(db, event_id)
    if existing is not None:
        existing_entry = review_repo.get_calendar_entry_by_event_id(db, event_id)
        if existing_entry is None:
            entry_date = calendar_date if calendar_date is not None else date.today()
            review_repo.create_calendar_entry(
                db,
                review_id=existing.id,
                event_id=event_id,
                relationship_id=relationship_id,
                calendar_date=entry_date,
            )
        return existing

    review = review_repo.create_review(
        db,
        public_id=generate_public_id(),
        event_id=event_id,
        relationship_id=relationship_id,
        content=content,
        source="judge_result",
        created_by_user_id=created_by_user_id,
    )

    entry_date = calendar_date if calendar_date is not None else date.today()
    review_repo.create_calendar_entry(
        db,
        review_id=review.id,
        event_id=event_id,
        relationship_id=relationship_id,
        calendar_date=entry_date,
    )

    return review

from pydantic import BaseModel, Field

from app.models.judge import JudgeResult
from app.models.snapshot import EventSnapshot
from app.services import ai_service


class ReviewAiPayload(BaseModel):
    content: str = Field(min_length=1)


def build_fallback_review_content(judge_result: JudgeResult) -> str:
    trigger_lines = "\n".join(f"- {item}" for item in (judge_result.triggers or []))
    misunderstanding_lines = "\n".join(
        f"- {item}" for item in (judge_result.misunderstandings or [])
    )
    advice_a_lines = "\n".join(f"- {item}" for item in (judge_result.advice_for_a or []))
    advice_b_lines = "\n".join(f"- {item}" for item in (judge_result.advice_for_b or []))
    return (
        "一、事件回顾\n"
        f"{judge_result.objective_summary}\n\n"
        "二、容易重复触发的点\n"
        f"{trigger_lines or '- 暂无更多信息'}\n\n"
        "三、可能的误解\n"
        f"{misunderstanding_lines or '- 暂无更多信息'}\n\n"
        "四、后续建议\n"
        "给 A：\n"
        f"{advice_a_lines or '- 先描述事实，再表达感受'}\n"
        "给 B：\n"
        f"{advice_b_lines or '- 先确认感受，再回应立场'}"
    )


def generate_review_content_from_judge(
    *,
    snapshot_a: EventSnapshot,
    snapshot_b: EventSnapshot | None,
    judge_result: JudgeResult,
) -> dict[str, str | int]:
    snapshot_b_text = snapshot_b.summary if snapshot_b is not None else "（B 未提交私有确认，仅有 A 快照）"
    prompt = (
        "请根据下面的情侣冲突材料，生成一份面向双方的复盘正文。\n"
        "要求：\n"
        "1. 使用中文。\n"
        "2. 内容分成 3 到 4 个自然段，不要使用 JSON 之外的额外说明。\n"
        "3. 重点包括：发生了什么、双方各自的感受/需求、有哪些误解、下次可以怎么做。\n"
        "4. 保持中立，不指责，不说教，不编造事实。\n\n"
        f"A 快照：{snapshot_a.summary or '（无）'}\n"
        f"B 快照：{snapshot_b_text}\n"
        f"客观摘要：{judge_result.objective_summary}\n"
        f"触发点：{judge_result.triggers or []}\n"
        f"误解点：{judge_result.misunderstandings or []}\n"
        f"给 A 的建议：{judge_result.advice_for_a or []}\n"
        f"给 B 的建议：{judge_result.advice_for_b or []}"
    )
    ai_result = ai_service.call_llm_json(
        prompt=prompt,
        response_model=ReviewAiPayload,
        model_name="review-v1",
        system_prompt=(
            "你是后端复盘正文生成器。"
            "你只输出合法 JSON，字段 content 必须是一段可直接展示给用户的复盘正文。"
        ),
        temperature=0.35,
    )
    data: ReviewAiPayload = ai_result["data"]
    return {
        "content": data.content.strip(),
        "model_name": str(ai_result["model_name"]),
        "input_tokens": int(ai_result["input_tokens"]),
        "output_tokens": int(ai_result["output_tokens"]),
    }
