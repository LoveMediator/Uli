"""Calendar 路由（3 号）。"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentActiveUser, Db
from app.schemas.common import ApiEnvelope, envelope_success
from app.services import calendar_service
from app.utils.permissions import get_relationship_by_public_id

router = APIRouter()

MonthQuery = Annotated[str, Query(pattern=r"^\d{4}-\d{2}$")]
RelationshipIdQuery = Annotated[str, Query(alias="relationshipId")]


@router.get("", response_model=ApiEnvelope)
def get_month_calendar(
    user: CurrentActiveUser,
    db: Db,
    month: MonthQuery,
    relationship_id: RelationshipIdQuery,
) -> ApiEnvelope:
    year, month_num = int(month[:4]), int(month[5:7])
    rel = get_relationship_by_public_id(db, relationship_id)
    data = calendar_service.get_month_summary(
        db, user_id=user.id, relationship_id=rel.id, year=year, month=month_num,
    )
    return envelope_success(data.model_dump(by_alias=True))


@router.get("/days/{target_date}/reviews", response_model=ApiEnvelope)
def get_day_reviews(
    target_date: date,
    user: CurrentActiveUser,
    db: Db,
    relationship_id: RelationshipIdQuery,
) -> ApiEnvelope:
    rel = get_relationship_by_public_id(db, relationship_id)
    data = calendar_service.get_day_reviews(
        db, user_id=user.id, relationship_id=rel.id, target_date=target_date,
    )
    return envelope_success(data.model_dump(by_alias=True))
