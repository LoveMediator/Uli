"""JudgeResult 数据访问。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.judge import JudgeResult


def get_judge_result_by_event_id(db: Session, event_id: int) -> JudgeResult | None:
    stmt = select(JudgeResult).where(JudgeResult.event_id == event_id)
    return db.execute(stmt).scalar_one_or_none()


def create_judge_result(
    db: Session,
    *,
    public_id: str,
    event_id: int,
    objective_summary: str,
    triggers: list[str],
    misunderstandings: list[str],
    advice_for_a: list[str],
    advice_for_b: list[str],
    model_name: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> JudgeResult:
    result = JudgeResult(
        public_id=public_id,
        event_id=event_id,
        objective_summary=objective_summary,
        triggers=triggers,
        misunderstandings=misunderstandings,
        advice_for_a=advice_for_a,
        advice_for_b=advice_for_b,
        model_name=model_name,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    db.add(result)
    db.flush()
    return result
