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
