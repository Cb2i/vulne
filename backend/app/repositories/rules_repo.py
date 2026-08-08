from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.exception import ExceptionRecord
from app.models.rules import CAAConfig, OwnershipRule, SLERule


def get_active_caa_config(db: Session) -> CAAConfig:
    config = db.scalar(select(CAAConfig).where(CAAConfig.is_active.is_(True)).order_by(CAAConfig.id.desc()))
    if config is None:
        raise LookupError("No active CAA configuration found. Run the seed script first.")
    return config


def list_sle_rules(db: Session) -> list[SLERule]:
    return list(db.scalars(select(SLERule)))


def list_active_ownership_rules(db: Session) -> list[OwnershipRule]:
    return list(db.scalars(select(OwnershipRule).where(OwnershipRule.active.is_(True)).order_by(OwnershipRule.priority)))


def list_active_exceptions(db: Session) -> list[ExceptionRecord]:
    return list(db.scalars(select(ExceptionRecord).where(ExceptionRecord.status == "active")))
