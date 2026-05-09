"""Judge service."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.judge import JudgeResult
from app.models.snapshot import EventSnapshot
from app.repos import judge_repo
from app.services import ai_service
from app.utils.ids import generate_public_id


class JudgeAiPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    objective_summary: str = Field(min_length=1)
    triggers: list[str]
    misunderstandings: list[str]
    advice_for_a: list[str] = Field(alias="adviceForA")
    advice_for_b: list[str] = Field(alias="adviceForB")



def _normalize_items(items: list[str], *, fallback: str) -> list[str]:
    clean_items = [str(item).strip() for item in items if str(item).strip()]
    return clean_items[:5] if clean_items else [fallback]



def _build_snapshot_block(snapshot: EventSnapshot, *, side_label: str) -> str:
    return "\n".join(
        [
            f"{side_label}摘要：{snapshot.summary or '（空）'}",
            f"{side_label}视角要点：{snapshot.points_a or []}",
            f"{side_label}对另一方的描述：{snapshot.points_b or []}",
        ]
    )



def generate_judge_result(
    db: Session,
    *,
    event_id: int,
    snapshot_a: EventSnapshot,
    snapshot_b: EventSnapshot | None = None,
) -> JudgeResult:
    prompt_parts = [
        "你是情侣冲突调解流程中的裁判助手。",
        "请只基于快照里的事实，输出中立、具体、可执行的判断。",
        "所有自然语言字段必须使用简体中文。",
        "不要编造快照中不存在的事实。",
        "必须返回这些字段：",
        "- objective_summary：一段中立的客观总结",
        "- triggers：1 到 5 条触发点",
        "- misunderstandings：1 到 5 条可能的误解点",
        "- adviceForA：1 到 5 条给 A 的可执行建议",
        "- adviceForB：1 到 5 条给 B 的可执行建议",
        "",
        _build_snapshot_block(snapshot_a, side_label="A方"),
    ]
    if snapshot_b is not None:
        prompt_parts.extend(["", _build_snapshot_block(snapshot_b, side_label="B方")])
    else:
        prompt_parts.append("\nB方快照：（未提交，仅可基于现有内容谨慎推断，不得编造）")

    ai_result = ai_service.call_llm_json(
        prompt="\n".join(prompt_parts),
        response_model=JudgeAiPayload,
        model_name=settings.effective_llm_text_model,
        system_prompt=(
            "你是后端裁判 JSON 生成器。"
            "你只能输出合法 JSON。"
            "所有自然语言字段必须使用简体中文。"
            "内容要平衡、具体、克制，不站队，不攻击任何一方。"
        ),
        temperature=0.2,
    )
    data: JudgeAiPayload = ai_result["data"]

    return judge_repo.create_judge_result(
        db,
        public_id=generate_public_id(),
        event_id=event_id,
        objective_summary=data.objective_summary.strip(),
        triggers=_normalize_items(data.triggers, fallback="信息不足，暂时无法归纳明确触发点。"),
        misunderstandings=_normalize_items(
            data.misunderstandings,
            fallback="信息不足，暂时无法归纳明确误解点。",
        ),
        advice_for_a=_normalize_items(
            data.advice_for_a,
            fallback="先描述事实，再表达自己的感受和需求。",
        ),
        advice_for_b=_normalize_items(
            data.advice_for_b,
            fallback="先确认对方的感受，再表达自己的立场。",
        ),
        model_name=str(ai_result["model_name"]),
        input_tokens=int(ai_result["input_tokens"]),
        output_tokens=int(ai_result["output_tokens"]),
    )
