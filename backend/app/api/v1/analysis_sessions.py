from fastapi import APIRouter, File, Form, Response, UploadFile

from app.api.deps import CurrentActiveUser, Db, PublicId
from app.schemas.analysis_session import AnalysisSessionMessageRequest
from app.schemas.common import ApiEnvelope, envelope_success
from app.services import analysis_session_chat_service as analysis_session_service

router = APIRouter()


@router.post("/{session_id}/messages", response_model=ApiEnvelope)
def send_analysis_message(
    session_id: PublicId,
    body: AnalysisSessionMessageRequest,
    user: CurrentActiveUser,
    db: Db,
) -> ApiEnvelope:
    data = analysis_session_service.send_analysis_message(
        db,
        current_user=user,
        session_id=session_id,
        message=body.message,
    )
    return envelope_success(data.model_dump(by_alias=True))


@router.post("/{session_id}/images", response_model=ApiEnvelope)
async def send_analysis_image_message(
    session_id: PublicId,
    user: CurrentActiveUser,
    db: Db,
    image: UploadFile = File(...),
    message: str = Form(default=""),
) -> ApiEnvelope:
    data = analysis_session_service.send_analysis_image_message(
        db,
        current_user=user,
        session_id=session_id,
        filename=image.filename,
        mime_type=image.content_type,
        image_bytes=await image.read(),
        message=message,
    )
    return envelope_success(data.model_dump(by_alias=True))


@router.get("/{session_id}/images/{image_id}")
def get_analysis_image(
    session_id: PublicId,
    image_id: PublicId,
    user: CurrentActiveUser,
) -> Response:
    image_bytes, mime_type, _filename = analysis_session_service.get_analysis_image(
        session_id=session_id,
        current_user=user,
        image_id=image_id,
    )
    return Response(content=image_bytes, media_type=mime_type)


@router.post("/{session_id}/commit", response_model=ApiEnvelope)
def commit_analysis_session(
    session_id: PublicId,
    user: CurrentActiveUser,
    db: Db,
) -> ApiEnvelope:
    data = analysis_session_service.commit_analysis_session(
        db,
        current_user=user,
        session_id=session_id,
    )
    return envelope_success(data.model_dump(by_alias=True))
