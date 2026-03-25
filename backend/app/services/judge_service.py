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
    objective_summary = f"[MOCK] 基于 A 侧快照「{snapshot_a.summary[:30]}…」"
    if snapshot_b:
        objective_summary += f"与 B 侧快照「{snapshot_b.summary[:30]}…」"
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
