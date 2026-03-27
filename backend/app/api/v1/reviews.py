"""Reviews 路由（3 号）。"""

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentActiveUser, Db, PublicId
from app.core.errors import NotFoundError
from app.models.event import Event
from app.schemas.common import ApiEnvelope, envelope_success
from app.schemas.review import ReviewDetail, ReviewUpdateRequest, ReviewUpdateResponse
from app.services import review_service

router = APIRouter()


@router.get("/{review_id}", response_model=ApiEnvelope)
def get_review(
    review_id: PublicId,
    user: CurrentActiveUser,
    db: Db,
) -> ApiEnvelope:
    review = review_service.get_review(db, user_id=user.id, review_public_id=review_id)
    event = db.execute(
        select(Event).where(Event.id == review.event_id)
    ).scalar_one_or_none()
    if event is None:
        raise NotFoundError("复盘关联的事件不存在")
    event_public_id = event.public_id

    data = ReviewDetail(
        reviewId=review.public_id,
        eventId=event_public_id,
        content=review.content,
        source=review.source,
        createdAt=review.created_at,
        updatedAt=review.updated_at,
    )
    return envelope_success(data.model_dump(by_alias=True))


@router.put("/{review_id}", response_model=ApiEnvelope)
def update_review(
    review_id: PublicId,
    body: ReviewUpdateRequest,
    user: CurrentActiveUser,
    db: Db,
) -> ApiEnvelope:
    review = review_service.update_review(
        db, user_id=user.id, review_public_id=review_id, content=body.content,
    )
    data = ReviewUpdateResponse(
        reviewId=review.public_id,
        updatedAt=review.updated_at,
        updatedBy=user.public_id,
    )
    return envelope_success(data.model_dump(by_alias=True))
