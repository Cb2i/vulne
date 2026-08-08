"""Import all models so Base.metadata / Alembic autogenerate can discover them."""
from app.models.asset import Asset
from app.models.decommission import Decommission
from app.models.exception import ExceptionRecord
from app.models.finding import Finding
from app.models.import_history import ImportHistory
from app.models.remediation import RemediationAction, RemediationActionFinding
from app.models.rules import CAAConfig, OwnershipRule, SLERule
from app.models.scan import Scan
from app.models.team import Team
from app.models.user import User

__all__ = [
    "Asset",
    "Decommission",
    "ExceptionRecord",
    "Finding",
    "ImportHistory",
    "RemediationAction",
    "RemediationActionFinding",
    "CAAConfig",
    "OwnershipRule",
    "SLERule",
    "Scan",
    "Team",
    "User",
]
