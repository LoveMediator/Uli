from __future__ import annotations

import base64
import binascii
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.constants.enums import EventStatus, SnapshotSide
from app.constants.error_codes import FORBIDDEN, INVALID_PARAMS, INVALID_STATE, NOT_FOUND
from app.core.config import settings
from app.core.errors import AppError
from app.models.user import User
from app.repos import audit_repo, event_repo, snapshot_repo
from app.schemas.analysis_session import (
    AnalysisSessionCommitData,
    AnalysisSessionData,
    AnalysisSessionImagePayload,
    AnalysisSessionMessageData,
    AnalysisSessionMessagePayload,
)
from app.services import analysis_session_store, event_service, private_chat_ai_service
from app.utils.ids import generate_public_id
from app.utils.permissions import get_event_with_permission, get_relationship_by_public_id

PHASE_A = "a"
PHASE_B = "b"
STATUS_ACTIVE = "active"
STATUS_COMMITTED = "committed"
MAX_TEXT_MESSAGE_LENGTH = 5000
ALLOWED_IMAGE_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _session_expiry() -> datetime:
    return _now() + timedelta(seconds=settings.analysis_session_ttl_seconds)


def _touch_session(session: dict[str, Any]) -> dict[str, Any]:
    session["updatedAt"] = _now().isoformat()
    session["expiresAt"] = _session_expiry().isoformat()
    return session


def _image_payloads(message: dict[str, Any]) -> list[AnalysisSessionImagePayload]:
    return [
        AnalysisSessionImagePayload(
            imageId=image["imageId"],
            mimeType=image["mimeType"],
            filename=image.get("filename"),
        )
        for image in message.get("images", [])
    ]


def _build_session_data(session: dict[str, Any]) -> AnalysisSessionData:
    return AnalysisSessionData(
        sessionId=session["sessionId"],
        phase=session["phase"],
        relationshipId=session.get("relationshipId"),
        eventId=session.get("eventId"),
        expiresAt=datetime.fromisoformat(session["expiresAt"]),
        messages=[
            AnalysisSessionMessagePayload(
                role=message["role"],
                content=message["content"],
                createdAt=datetime.fromisoformat(message["createdAt"]),
                images=_image_payloads(message),
            )
            for message in session.get("messages", [])
        ],
    )


def _append_message(
    session: dict[str, Any],
    *,
    role: str,
    content: str,
    images: list[dict[str, Any]] | None = None,
) -> None:
    session.setdefault("messages", []).append(
        {
            "role": role,
            "content": content,
            "images": images or [],
            "createdAt": _now().isoformat(),
        }
    )


def _build_private_system_prompt(session: dict[str, Any]) -> str:
    return (
        "You are a private mediation assistant. Help the user organize facts, "
        "clarify emotions, and identify viewpoints without advancing business state. "
        f"Current phase={session['phase']}."
    )


def _to_llm_message(message: dict[str, Any]) -> dict[str, Any]:
    images = message.get("images", [])
    content = str(message.get("content", ""))
    if not images:
        return {"role": message["role"], "content": content}

    blocks: list[dict[str, Any]] = []
    if content.strip():
        blocks.append({"type": "text", "text": content.strip()})
    for image in images:
        blocks.append(
            {
                "type": "image_url",
                "image_url": {"url": image["dataUrl"]},
            }
        )
    if not blocks:
        blocks.append({"type": "text", "text": "User uploaded an image for analysis."})
    return {"role": message["role"], "content": blocks}


def _build_private_messages(session: dict[str, Any]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _build_private_system_prompt(session)}
    ]
    for item in session.get("messages", [])[-8:]:
        messages.append(_to_llm_message(item))
    return messages


def _raw_payload_messages(session: dict[str, Any]) -> list[dict[str, Any]]:
    payload_messages: list[dict[str, Any]] = []
    for message in session.get("messages", []):
        payload_messages.append(
            {
                "role": message["role"],
                "content": message["content"],
                "createdAt": message["createdAt"],
                "images": [
                    {
                        "imageId": image["imageId"],
                        "mimeType": image["mimeType"],
                        "filename": image.get("filename"),
                    }
                    for image in message.get("images", [])
                ],
            }
        )
    return payload_messages


def _build_structured_snapshot(session: dict[str, Any]) -> tuple[str, list[str], list[str], dict[str, Any]]:
    user_messages = [
        str(item.get("content", "")).strip()
        for item in session.get("messages", [])
        if item.get("role") == "user" and str(item.get("content", "")).strip()
    ]
    if not user_messages:
        raise AppError("当前分析会话没有可确认的文字内容", code=INVALID_STATE)

    summary = user_messages[-1]
    unique_points: list[str] = []
    for item in user_messages:
        if item not in unique_points:
            unique_points.append(item)
        if len(unique_points) >= 3:
            break

    if session["phase"] == PHASE_A:
        points_a = unique_points
        points_b: list[str] = []
    else:
        points_a = []
        points_b = unique_points

    raw_payload = {
        "phase": session["phase"],
        "messages": _raw_payload_messages(session),
    }
    return summary, points_a, points_b, raw_payload


def _get_store() -> analysis_session_store.AnalysisSessionStore:
    return analysis_session_store.get_analysis_session_store()


def _get_owned_session(
    session_id: str,
    current_user: User,
    *,
    require_active: bool = True,
) -> dict[str, Any]:
    session = _get_store().get_session(session_id)
    if session is None:
        raise AppError("分析会话不存在或已过期", code=INVALID_STATE)
    if require_active and session["status"] != STATUS_ACTIVE:
        raise AppError("分析会话已确认，不能重复提交", code=INVALID_STATE)
    if int(session["userId"]) != current_user.id:
        raise AppError("无权访问该分析会话", code=FORBIDDEN)
    return session


def _ensure_session_event_state(db: Session, session: dict[str, Any], current_user: User) -> None:
    if session["phase"] != PHASE_B or session.get("eventId") is None:
        return
    event, _relationship = get_event_with_permission(db, str(session["eventId"]), current_user.id)
    if event.status != EventStatus.WAITING_B:
        raise AppError("当前状态不允许继续 B 侧分析", code=INVALID_STATE)


def _clean_text_message(message: str, *, allow_empty: bool = False) -> str:
    clean_message = message.strip()
    if not clean_message and not allow_empty:
        raise AppError("消息不能为空", code=INVALID_PARAMS)
    if len(clean_message) > MAX_TEXT_MESSAGE_LENGTH:
        raise AppError("消息长度超出限制", code=INVALID_PARAMS)
    return clean_message


def _validate_image_upload(mime_type: str | None, size_bytes: int) -> None:
    if mime_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise AppError("仅支持 jpg/png/webp 图片", code=INVALID_PARAMS)
    if size_bytes <= 0:
        raise AppError("图片不能为空", code=INVALID_PARAMS)
    if size_bytes > settings.max_upload_size_mb * 1024 * 1024:
        raise AppError("图片大小超出限制", code=INVALID_PARAMS)


def _encode_image_data_url(mime_type: str, image_bytes: bytes) -> str:
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _decode_image_data_url(data_url: str) -> tuple[str, bytes]:
    prefix, _, encoded = data_url.partition(",")
    if not prefix.startswith("data:") or ";base64" not in prefix or not encoded:
        raise AppError("图片数据已损坏", code=INVALID_STATE)
    mime_type = prefix[5:].split(";", 1)[0]
    try:
        return mime_type, base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        raise AppError("图片数据已损坏", code=INVALID_STATE) from None


def start_a_analysis_session(
    db: Session,
    current_user: User,
    relationship_public_id: str,
) -> AnalysisSessionData:
    relationship = get_relationship_by_public_id(db, relationship_public_id)
    if current_user.id not in (relationship.user_a_id, relationship.user_b_id):
        raise AppError("无权在该关系下发起分析", code=FORBIDDEN)
    if event_repo.get_open_event_for_relationship(db, relationship.id) is not None:
        raise AppError("当前关系已有未完成事件，请先处理完成后再创建", code=INVALID_STATE)

    store = _get_store()
    session = store.get_scoped_session(PHASE_A, relationship_public_id, current_user.id)
    if session is None:
        session = {
            "sessionId": generate_public_id(),
            "phase": PHASE_A,
            "status": STATUS_ACTIVE,
            "userId": current_user.id,
            "relationshipId": relationship.public_id,
            "relationshipDbId": relationship.id,
            "eventId": None,
            "eventDbId": None,
            "messages": [],
            "createdAt": _now().isoformat(),
        }
    store.save_session(_touch_session(session))
    return _build_session_data(session)


def start_b_analysis_session(
    db: Session,
    current_user: User,
    event_public_id: str,
) -> AnalysisSessionData:
    event, relationship = get_event_with_permission(db, event_public_id, current_user.id)
    if current_user.id == event.initiator_user_id:
        raise AppError("发起方不能进入 B 侧私有分析", code=FORBIDDEN)
    if event.status != EventStatus.WAITING_B:
        raise AppError("当前状态不允许开启 B 侧分析", code=INVALID_STATE)

    store = _get_store()
    session = store.get_scoped_session(PHASE_B, event_public_id, current_user.id)
    if session is None:
        session = {
            "sessionId": generate_public_id(),
            "phase": PHASE_B,
            "status": STATUS_ACTIVE,
            "userId": current_user.id,
            "relationshipId": relationship.public_id,
            "relationshipDbId": relationship.id,
            "eventId": event.public_id,
            "eventDbId": event.id,
            "messages": [],
            "createdAt": _now().isoformat(),
        }
    store.save_session(_touch_session(session))
    return _build_session_data(session)


def _save_reply(
    db: Session,
    session: dict[str, Any],
    *,
    session_id: str,
    ai_result: dict[str, Any],
) -> AnalysisSessionMessageData:
    reply = str(ai_result["content"])
    _append_message(session, role="assistant", content=reply)
    _get_store().save_session(_touch_session(session))
    audit_repo.create_ai_call_log(
        db,
        event_id=session.get("eventDbId"),
        scene="private_chat",
        model_name=ai_result.get("model_name", "mock-private-chat-v1"),
        success=True,
        input_tokens=int(ai_result.get("input_tokens", 0) or 0),
        output_tokens=int(ai_result.get("output_tokens", 0) or 0),
        trace_id=session_id,
    )
    db.commit()
    return AnalysisSessionMessageData(sessionId=session_id, reply=reply)


def send_analysis_message(
    db: Session,
    current_user: User,
    session_id: str,
    message: str,
) -> AnalysisSessionMessageData:
    session = _get_owned_session(session_id, current_user)
    _ensure_session_event_state(db, session, current_user)

    clean_message = _clean_text_message(message)
    _append_message(session, role="user", content=clean_message)
    ai_result = private_chat_ai_service.call_private_chat_llm(
        messages=_build_private_messages(session),
        model_name="mock-private-chat-v1",
    )
    return _save_reply(db, session, session_id=session_id, ai_result=ai_result)


def send_analysis_image_message(
    db: Session,
    current_user: User,
    session_id: str,
    *,
    filename: str | None,
    mime_type: str | None,
    image_bytes: bytes,
    message: str = "",
) -> AnalysisSessionMessageData:
    session = _get_owned_session(session_id, current_user)
    _ensure_session_event_state(db, session, current_user)

    _validate_image_upload(mime_type, len(image_bytes))
    clean_message = _clean_text_message(message, allow_empty=True)
    image = {
        "imageId": generate_public_id(),
        "mimeType": mime_type,
        "filename": filename or "image",
        "dataUrl": _encode_image_data_url(mime_type or "application/octet-stream", image_bytes),
        "sizeBytes": len(image_bytes),
    }
    _append_message(session, role="user", content=clean_message, images=[image])
    ai_result = private_chat_ai_service.call_private_chat_llm(
        messages=_build_private_messages(session),
        model_name="mock-private-chat-v1",
    )
    return _save_reply(db, session, session_id=session_id, ai_result=ai_result)


def get_analysis_image(
    session_id: str,
    current_user: User,
    image_id: str,
) -> tuple[bytes, str, str | None]:
    session = _get_owned_session(session_id, current_user, require_active=False)
    for message in session.get("messages", []):
        for image in message.get("images", []):
            if image.get("imageId") != image_id:
                continue
            mime_type, image_bytes = _decode_image_data_url(str(image["dataUrl"]))
            return image_bytes, mime_type, image.get("filename")
    raise AppError("图片不存在", code=NOT_FOUND)


def _mark_session_committed(session: dict[str, Any], **result_fields: str | None) -> None:
    session["status"] = STATUS_COMMITTED
    session["committedAt"] = _now().isoformat()
    for key, value in result_fields.items():
        session[key] = value
    _get_store().save_session(_touch_session(session))


def commit_analysis_session(
    db: Session,
    current_user: User,
    session_id: str,
) -> AnalysisSessionCommitData:
    session = _get_owned_session(session_id, current_user)
    summary, points_a, points_b, raw_payload = _build_structured_snapshot(session)

    if session["phase"] == PHASE_A:
        relationship = get_relationship_by_public_id(db, str(session["relationshipId"]))
        if current_user.id not in (relationship.user_a_id, relationship.user_b_id):
            raise AppError("无权在该关系下确认分析", code=FORBIDDEN)
        if event_repo.get_open_event_for_relationship(db, relationship.id) is not None:
            raise AppError("当前关系已有未完成事件，请先处理完成后再创建", code=INVALID_STATE)

        event = event_repo.create_event(
            db,
            public_id=generate_public_id(),
            relationship_id=relationship.id,
            initiator_user_id=current_user.id,
            title=None,
        )
        snapshot = snapshot_repo.create_snapshot(
            db,
            public_id=generate_public_id(),
            event_id=event.id,
            side=SnapshotSide.A,
            summary=summary,
            points_a=points_a,
            points_b=points_b,
            raw_payload=raw_payload,
            confirmed_by_user_id=current_user.id,
        )
        old_status = event.status
        event.status = EventStatus.WAITING_B
        db.flush()
        audit_repo.create_event_state_log(
            db,
            event_id=event.id,
            from_status=old_status,
            to_status=EventStatus.WAITING_B,
            action="commit_a",
            operator_user_id=current_user.id,
            trace_id=session_id,
        )
        db.commit()
        db.refresh(event)
        db.refresh(snapshot)
        _mark_session_committed(
            session,
            eventId=event.public_id,
            eventDbId=str(event.id),
            snapshotAId=snapshot.public_id,
        )
        return AnalysisSessionCommitData(
            sessionId=session_id,
            eventId=event.public_id,
            status=event.status.value,
            snapshotAId=snapshot.public_id,
        )

    event, relationship = get_event_with_permission(db, str(session["eventId"]), current_user.id)
    if current_user.id == event.initiator_user_id:
        raise AppError("发起方不能确认 B 侧分析", code=FORBIDDEN)
    if event.status != EventStatus.WAITING_B:
        raise AppError("当前状态不允许确认 B 侧分析", code=INVALID_STATE)
    existing_b = snapshot_repo.get_snapshot_by_event_and_side(db, event.id, SnapshotSide.B)
    if existing_b is not None:
        raise AppError("Snapshot_B 已存在", code=INVALID_STATE)
    snapshot_a = snapshot_repo.get_snapshot_by_event_and_side(db, event.id, SnapshotSide.A)
    if snapshot_a is None:
        raise AppError("Snapshot_A 不存在，无法继续", code=INVALID_STATE)

    snapshot_b = snapshot_repo.create_snapshot(
        db,
        public_id=generate_public_id(),
        event_id=event.id,
        side=SnapshotSide.B,
        summary=summary,
        points_a=points_a,
        points_b=points_b,
        raw_payload=raw_payload,
        confirmed_by_user_id=current_user.id,
    )
    judge_result = event_service._execute_judge(
        db,
        event,
        relationship,
        snapshot_a,
        snapshot_b,
        current_user.id,
    )
    db.refresh(snapshot_b)
    _mark_session_committed(
        session,
        judgeResultId=judge_result.public_id,
        snapshotBId=snapshot_b.public_id,
    )
    return AnalysisSessionCommitData(
        sessionId=session_id,
        eventId=event.public_id,
        status=event.status.value,
        snapshotBId=snapshot_b.public_id,
        judgeResultId=judge_result.public_id,
    )
