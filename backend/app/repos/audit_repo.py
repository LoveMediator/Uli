"""审计日志与 AI 调用日志数据访问。"""

from sqlalchemy.orm import Session

from app.constants.enums import EventStatus
from app.models.audit import AiCallLog, EventStateLog


def create_event_state_log(
    db: Session,
    *,
    event_id: int,
    from_status: EventStatus,
    to_status: EventStatus,
    action: str,
    operator_user_id: int | None = None,
    trace_id: str | None = None,
) -> EventStateLog:
    log = EventStateLog(
        event_id=event_id,
        from_status=from_status,
        to_status=to_status,
        action=action,
        operator_user_id=operator_user_id,
        trace_id=trace_id,
    )
    db.add(log)
    db.flush()
    return log


def create_ai_call_log(
    db: Session,
    *,
    event_id: int | None,
    scene: str,
    model_name: str,
    success: bool,
    input_tokens: int = 0,
    output_tokens: int = 0,
    error_code: str | None = None,
    trace_id: str | None = None,
) -> AiCallLog:
    log = AiCallLog(
        event_id=event_id,
        scene=scene,
        model_name=model_name,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        success=success,
        error_code=error_code,
        trace_id=trace_id,
    )
    db.add(log)
    db.flush()
    return log
