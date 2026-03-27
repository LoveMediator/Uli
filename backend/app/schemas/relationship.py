from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RelationshipInviteData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    invite_token: str = Field(alias="inviteToken")
    invite_url: str = Field(alias="inviteUrl")
    expires_at: datetime = Field(alias="expiresAt")


class RelationshipAcceptRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    invite_token: str = Field(alias="inviteToken", min_length=20, max_length=4096)


class RelationshipCancelConfirmRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    cancel_token: str = Field(alias="cancelToken", min_length=20, max_length=4096)


class RelationshipCurrentEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(alias="eventId")
    status: str
    pending_action: str = Field(alias="pendingAction")
    title: str | None = None


class RelationshipSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    relationship_id: str = Field(alias="relationshipId")
    partner_user_id: str = Field(alias="partnerUserId")
    partner_username: str = Field(alias="partnerUsername")
    status: str
    current_event: RelationshipCurrentEvent | None = Field(alias="currentEvent", default=None)


class RelationshipAcceptData(RelationshipSummary):
    pass


class RelationshipListData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[RelationshipSummary]


class RelationshipCancelRequestData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    cancel_token: str = Field(alias="cancelToken")
    cancel_url: str = Field(alias="cancelUrl")
    expires_at: datetime = Field(alias="expiresAt")


class RelationshipDeleteCounts(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    private_messages: int = Field(alias="privateMessages")
    private_sessions: int = Field(alias="privateSessions")
    followup_messages: int = Field(alias="followupMessages")
    event_state_logs: int = Field(alias="eventStateLogs")
    ai_call_logs: int = Field(alias="aiCallLogs")
    elf_messages: int = Field(alias="elfMessages")
    judge_results: int = Field(alias="judgeResults")
    event_snapshots: int = Field(alias="eventSnapshots")
    calendar_entries: int = Field(alias="calendarEntries")
    review_versions: int = Field(alias="reviewVersions")
    reviews: int
    events: int
    relationships: int


class RelationshipCancelData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    relationship_id: str = Field(alias="relationshipId")
    deleted_counts: RelationshipDeleteCounts = Field(alias="deletedCounts")
    deleted_at: datetime = Field(alias="deletedAt")
