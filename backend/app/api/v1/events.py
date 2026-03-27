"""Events 主链路由（2 号 + followup 串联点）。"""

from fastapi import APIRouter

from app.api.deps import CurrentActiveUser, Db, PublicId
from app.schemas.common import ApiEnvelope, envelope_success
from app.schemas.event import (
    BAgreeData,
    BAgreeRequest,
    CommitAData,
    CommitARequest,
    CommitBData,
    CommitBRequest,
    EventCreateData,
    EventCreateRequest,
    InviteData,
    SnapshotAData,
    SnapshotPayload,
)
from app.schemas.followup import FollowupRequest
from app.schemas.judge import JudgeAnalysis, JudgeResultData
from app.services import analysis_session_chat_service as analysis_session_service
from app.services import event_service, followup_service

router = APIRouter()


@router.post("", response_model=ApiEnvelope, deprecated=True)
def create_event(
    body: EventCreateRequest,
    user: CurrentActiveUser,
    db: Db,
) -> ApiEnvelope:
    event = event_service.create_event(
        db,
        user_id=user.id,
        title=body.title,
        relationship_public_id=body.relationship_id,
    )
    data = EventCreateData(
        eventId=event.public_id,
        status=event.status.value,
    )
    return envelope_success(data.model_dump(by_alias=True))


@router.post("/{event_id}/commit-a", response_model=ApiEnvelope, deprecated=True)
def commit_a(
    event_id: PublicId,
    body: CommitARequest,
    user: CurrentActiveUser,
    db: Db,
) -> ApiEnvelope:
    event, snapshot = event_service.commit_a(
        db,
        user_id=user.id,
        event_public_id=event_id,
        confirm_text=body.confirm_text,
    )
    data = CommitAData(
        eventId=event.public_id,
        status=event.status.value,
        snapshotAId=snapshot.public_id,
    )
    return envelope_success(data.model_dump(by_alias=True))


@router.post("/{event_id}/analysis-sessions/b", response_model=ApiEnvelope)
def start_b_analysis_session(
    event_id: PublicId,
    user: CurrentActiveUser,
    db: Db,
) -> ApiEnvelope:
    data = analysis_session_service.start_b_analysis_session(
        db,
        current_user=user,
        event_public_id=event_id,
    )
    return envelope_success(data.model_dump(by_alias=True))


@router.get("/{event_id}/invite", response_model=ApiEnvelope)
def get_invite(
    event_id: PublicId,
    db: Db,
) -> ApiEnvelope:
    event = event_service.get_invite(db, event_public_id=event_id)
    data = InviteData(
        eventId=event.public_id,
        status=event.status.value,
        title=event.title,
        inviteMessage="对方邀请你参与本次事件，请先登录后继续。",
        requiresAuth=True,
    )
    return envelope_success(data.model_dump(by_alias=True))


@router.get("/{event_id}/snapshot-a", response_model=ApiEnvelope)
def get_snapshot_a(
    event_id: PublicId,
    user: CurrentActiveUser,
    db: Db,
) -> ApiEnvelope:
    event, snapshot = event_service.get_snapshot_a(
        db, user_id=user.id, event_public_id=event_id,
    )
    data = SnapshotAData(
        eventId=event.public_id,
        status=event.status.value,
        snapshotA=SnapshotPayload(
            summary=snapshot.summary,
            pointsA=snapshot.points_a,
            pointsB=snapshot.points_b,
        ),
    )
    return envelope_success(data.model_dump(by_alias=True))


@router.post("/{event_id}/b-agree", response_model=ApiEnvelope)
def b_agree(
    event_id: PublicId,
    body: BAgreeRequest,
    user: CurrentActiveUser,
    db: Db,
) -> ApiEnvelope:
    event, judge_result = event_service.b_agree(
        db, user_id=user.id, event_public_id=event_id, agree=body.agree,
    )
    data = BAgreeData(
        eventId=event.public_id,
        status=event.status.value,
        judgeResultId=judge_result.public_id,
    )
    return envelope_success(data.model_dump(by_alias=True))


@router.post("/{event_id}/commit-b", response_model=ApiEnvelope, deprecated=True)
def commit_b(
    event_id: PublicId,
    body: CommitBRequest,
    user: CurrentActiveUser,
    db: Db,
) -> ApiEnvelope:
    event, snapshot_b, judge_result = event_service.commit_b(
        db,
        user_id=user.id,
        event_public_id=event_id,
        summary=body.summary,
        points_a=body.points_a,
        points_b=body.points_b,
    )
    data = CommitBData(
        eventId=event.public_id,
        status=event.status.value,
        snapshotBId=snapshot_b.public_id,
        judgeResultId=judge_result.public_id,
    )
    return envelope_success(data.model_dump(by_alias=True))


@router.get("/{event_id}/judge-result", response_model=ApiEnvelope)
def get_judge_result(
    event_id: PublicId,
    user: CurrentActiveUser,
    db: Db,
) -> ApiEnvelope:
    event, judge = event_service.get_judge_result(
        db, user_id=user.id, event_public_id=event_id,
    )
    data = JudgeResultData(
        judgeResultId=judge.public_id,
        eventId=event.public_id,
        status=event.status.value,
        objectiveSummary=judge.objective_summary,
        analysis=JudgeAnalysis(
            triggers=judge.triggers,
            misunderstandings=judge.misunderstandings,
            adviceForA=judge.advice_for_a,
            adviceForB=judge.advice_for_b,
        ),
        createdAt=judge.created_at,
    )
    return envelope_success(data.model_dump(by_alias=True))


@router.post("/{event_id}/followup-chat/messages", response_model=ApiEnvelope)
def followup_chat(
    event_id: PublicId,
    body: FollowupRequest,
    user: CurrentActiveUser,
    db: Db,
) -> ApiEnvelope:
    resp = followup_service.followup_chat(
        db,
        user_id=user.id,
        event_public_id=event_id,
        message=body.message,
    )
    return envelope_success(resp.model_dump(by_alias=True))
