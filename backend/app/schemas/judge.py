"""JudgeResult Pydantic schema。

仅定义 data 层结构。对齐 API 文档 §5.8。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JudgeAnalysis(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    triggers: list[str]
    misunderstandings: list[str]
    advice_for_a: list[str] = Field(alias="adviceForA")
    advice_for_b: list[str] = Field(alias="adviceForB")


class JudgeResultData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    judge_result_id: str = Field(alias="judgeResultId")
    event_id: str = Field(alias="eventId")
    status: str
    objective_summary: str = Field(alias="objectiveSummary")
    analysis: JudgeAnalysis
    created_at: datetime = Field(alias="createdAt")
