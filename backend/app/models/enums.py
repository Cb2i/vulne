import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    TEAM_MANAGER = "team_manager"
    READONLY = "readonly"


class Severity(str, enum.Enum):
    CRITIQUE = "Critique"
    HAUTE = "Haute"
    MOYENNE = "Moyenne"
    FAIBLE = "Faible"


class FindingStatus(str, enum.Enum):
    OPEN = "open"
    REMEDIATED = "remediated"
    EXCEPTION = "exception"
    DECOMMISSIONED = "decommissioned"


class ExceptionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class ImportStatus(str, enum.Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
