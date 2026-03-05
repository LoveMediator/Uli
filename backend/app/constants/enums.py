from enum import Enum


class UserStatus(str, Enum):
    ACTIVE = "active"
    LOCKED = "locked"
    DISABLED = "disabled"


class RelationshipStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"


class EventStatus(str, Enum):
    DRAFT = "draft"
    WAITING_B = "waiting_b"
    JUDGED = "judged"
    REVIEWED = "reviewed"
    CLOSED = "closed"


class SnapshotSide(str, Enum):
    A = "a"
    B = "b"


class ModerationRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
