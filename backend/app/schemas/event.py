"""Event 主链 Pydantic schema。

仅定义 data 层结构，不含外层 code/message/data envelope。
字段名与类型严格对齐 API 文档 §5.2 - §5.7。
"""

from pydantic import BaseModel, ConfigDict, Field


class EventCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(min_length=1, max_length=120)
    relationship_id: str = Field(alias="relationshipId", min_length=1, max_length=40)


class EventCreateData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(alias="eventId")
    status: str


class CommitARequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    confirm_text: str = Field(alias="confirmText", min_length=1, max_length=5000)


class CommitAData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(alias="eventId")
    status: str
    snapshot_a_id: str = Field(alias="snapshotAId")


class InviteData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(alias="eventId")
    status: str
    title: str | None = None
    invite_message: str = Field(alias="inviteMessage")
    requires_auth: bool = Field(alias="requiresAuth")


class SnapshotPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    summary: str
    points_a: list[str] = Field(alias="pointsA")
    points_b: list[str] = Field(alias="pointsB")


class SnapshotAData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(alias="eventId")
    status: str
    snapshot_a: SnapshotPayload = Field(alias="snapshotA")


class BAgreeRequest(BaseModel):
    agree: bool


class BAgreeData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(alias="eventId")
    status: str
    judge_result_id: str = Field(alias="judgeResultId")


class CommitBRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    summary: str = Field(min_length=1, max_length=5000)
    points_a: list[str] = Field(alias="pointsA")
    points_b: list[str] = Field(alias="pointsB")


class CommitBData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(alias="eventId")
    status: str
    snapshot_b_id: str = Field(alias="snapshotBId")
    judge_result_id: str = Field(alias="judgeResultId")
