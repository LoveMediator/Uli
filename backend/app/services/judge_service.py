"""裁判服务层。

同步可用版 judge 实现（mock）。后续接入真实 LLM 时替换生成逻辑。
judge-result 查询接口严禁实时触发本模块，仅由 b-agree / commit-b 调用。
"""

from sqlalchemy.orm import Session

from app.models.judge import JudgeResult
from app.models.snapshot import EventSnapshot
from app.repos import judge_repo
from app.utils.ids import generate_public_id

MOCK_MODEL_NAME = "mock-judge-v1"
MOCK_SUMMARY_PREVIEW_LEN = 30


def generate_judge_result(
    db: Session,
    *,
    event_id: int,
    snapshot_a: EventSnapshot,
    snapshot_b: EventSnapshot | None = None,
) -> JudgeResult:
    """根据快照生成裁判结果（当前为 mock）。

    真实实现应将 snapshot 内容拼成 prompt，调用 ai_service.call_llm，
    并用 Pydantic 校验 LLM 输出后写入 judge_results。
    """
    summary_a = (snapshot_a.summary or "")[:MOCK_SUMMARY_PREVIEW_LEN]
    objective_summary = f"[MOCK] 基于 A 侧快照「{summary_a}…」"
    if snapshot_b:
        summary_b = (snapshot_b.summary or "")[:MOCK_SUMMARY_PREVIEW_LEN]
        objective_summary += f"与 B 侧快照「{summary_b}…」"
    objective_summary += "生成的客观事实摘要。"

    triggers = ["[MOCK] 沟通频率下降", "[MOCK] 情绪管理失控"]
    misunderstandings = ["[MOCK] A 认为 B 不关心，实际 B 在忙工作"]
    advice_for_a = ["[MOCK] 尝试在冷静时表达需求"]
    advice_for_b = ["[MOCK] 主动告知忙碌状态以减少误解"]

    return judge_repo.create_judge_result(
        db,
        public_id=generate_public_id(),
        event_id=event_id,
        objective_summary=objective_summary,
        triggers=triggers,
        misunderstandings=misunderstandings,
        advice_for_a=advice_for_a,
        advice_for_b=advice_for_b,
        model_name=MOCK_MODEL_NAME,
        input_tokens=0,
        output_tokens=0,
    )

from pydantic import BaseModel, ConfigDict, Field

from app.services import ai_service


class JudgeAiPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    objective_summary: str = Field(min_length=1)
    triggers: list[str]
    misunderstandings: list[str]
    advice_for_a: list[str] = Field(alias="adviceForA")
    advice_for_b: list[str] = Field(alias="adviceForB")


def _normalize_items(items: list[str], *, fallback: str) -> list[str]:
    clean_items = [str(item).strip() for item in items if str(item).strip()]
    if clean_items:
        return clean_items[:5]
    return [fallback]


def _build_snapshot_block(snapshot: EventSnapshot, *, side_label: str) -> str:
    return "\n".join(
        [
            f"{side_label} summary: {snapshot.summary or '（无）'}",
            f"{side_label} points_a: {snapshot.points_a or []}",
            f"{side_label} points_b: {snapshot.points_b or []}",
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
        "你是情侣冲突调解系统的裁判助手。",
        "请基于双方快照输出中立、克制、可执行的判断。",
        "不要站队，不要扩写不存在的事实。",
        "输出字段要求：",
        "- objective_summary: 1 段客观事实摘要",
        "- triggers: 1 到 5 条触发点",
        "- misunderstandings: 1 到 5 条误解点",
        "- adviceForA: 1 到 5 条给 A 的建议",
        "- adviceForB: 1 到 5 条给 B 的建议",
        "",
        _build_snapshot_block(snapshot_a, side_label="A"),
    ]
    if snapshot_b is not None:
        prompt_parts.extend(["", _build_snapshot_block(snapshot_b, side_label="B")])
    else:
        prompt_parts.append("\nB snapshot: （B 未提交，仅基于 A 视角与现有信息判断）")

    ai_result = ai_service.call_llm_json(
        prompt="\n".join(prompt_parts),
        response_model=JudgeAiPayload,
        model_name="judge-v1",
        system_prompt=(
            "你是后端裁判生成器。"
            "你只输出合法 JSON，且所有建议都必须具体、可执行、避免攻击性。"
        ),
        temperature=0.2,
    )
    data: JudgeAiPayload = ai_result["data"]

    return judge_repo.create_judge_result(
        db,
        public_id=generate_public_id(),
        event_id=event_id,
        objective_summary=data.objective_summary.strip(),
        triggers=_normalize_items(data.triggers, fallback="触发点信息不足"),
        misunderstandings=_normalize_items(data.misunderstandings, fallback="误解点信息不足"),
        advice_for_a=_normalize_items(data.advice_for_a, fallback="先表达事实，再表达感受"),
        advice_for_b=_normalize_items(data.advice_for_b, fallback="先确认对方感受，再表达立场"),
        model_name=str(ai_result["model_name"]),
        input_tokens=int(ai_result["input_tokens"]),
        output_tokens=int(ai_result["output_tokens"]),
    )
