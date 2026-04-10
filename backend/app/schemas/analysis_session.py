from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.validators import reject_null_bytes


class AnalysisSessionImagePayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    image_id: str = Field(alias="imageId")
    mime_type: str = Field(alias="mimeType")
    filename: str | None = None


class AnalysisSessionMessagePayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    role: str
    content: str
    created_at: datetime = Field(alias="createdAt")
    images: list[AnalysisSessionImagePayload] = Field(default_factory=list)


class AnalysisSessionData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(alias="sessionId")
    phase: str
    relationship_id: str | None = Field(alias="relationshipId", default=None)
    event_id: str | None = Field(alias="eventId", default=None)
    expires_at: datetime = Field(alias="expiresAt")
    can_commit: bool = Field(alias="canCommit", default=False)
    fact_summary: str | None = Field(alias="factSummary", default=None)
    messages: list[AnalysisSessionMessagePayload]


class AnalysisSessionMessageRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message: str = Field(min_length=1, max_length=5000)

    _no_null = field_validator("message", mode="before")(reject_null_bytes)


class AnalysisSessionMessageData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(alias="sessionId")
    reply: str
    can_commit: bool = Field(alias="canCommit", default=False)
    fact_summary: str | None = Field(alias="factSummary", default=None)


class AnalysisSessionCommitData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(alias="sessionId")
    event_id: str = Field(alias="eventId")
    status: str
    snapshot_a_id: str | None = Field(alias="snapshotAId", default=None)
    snapshot_b_id: str | None = Field(alias="snapshotBId", default=None)
    judge_result_id: str | None = Field(alias="judgeResultId", default=None)
