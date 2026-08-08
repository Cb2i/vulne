"""Upserts Exceptions and OwnershipRule rows parsed from a Tenable workbook's
"Exceptions" and "KPI" sheets, so they persist in the database and keep applying to
every future scan instead of only the workbook they were first imported from.

Existing rows are matched by their natural key and updated in place; nothing is ever
deleted here, so a rule an admin created or edited by hand in the app is never
clobbered by a later re-import that happens not to mention it.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.importers.tenable_excel.parser import ParsedExceptionRow, ParsedOwnershipRow
from app.models.enums import ExceptionStatus
from app.models.exception import ExceptionRecord
from app.models.rules import OwnershipRule
from app.repositories.team_repo import get_or_create_team


def upsert_ownership_rules(db: Session, rows: list[ParsedOwnershipRow]) -> int:
    if not rows:
        return 0

    max_priority = db.scalar(select(OwnershipRule.priority).order_by(OwnershipRule.priority.desc())) or 0
    created = 0

    for row in rows:
        team = get_or_create_team(db, name=row.team_name)
        existing = db.scalar(
            select(OwnershipRule).where(
                OwnershipRule.team_id == team.id,
                OwnershipRule.hostname_pattern == row.hostname_pattern,
                OwnershipRule.os_pattern == row.os_pattern,
            )
        )
        if existing:
            continue
        max_priority += 10
        db.add(
            OwnershipRule(
                team_id=team.id,
                hostname_pattern=row.hostname_pattern,
                os_pattern=row.os_pattern,
                priority=max_priority,
                active=True,
            )
        )
        created += 1

    db.flush()
    return created


def upsert_exceptions(db: Session, rows: list[ParsedExceptionRow], *, imported_by_id: int | None) -> int:
    if not rows:
        return 0

    created = 0
    for row in rows:
        existing = db.scalar(
            select(ExceptionRecord).where(
                ExceptionRecord.vulnerability_match == row.vulnerability_match,
                ExceptionRecord.hostname_pattern == row.hostname_pattern,
            )
        )
        if existing:
            existing.asset_type = row.asset_type or existing.asset_type
            existing.granted_by = row.granted_by
            existing.granted_at = row.granted_at
            existing.confluence_link = row.confluence_link or existing.confluence_link
            continue
        db.add(
            ExceptionRecord(
                vulnerability_match=row.vulnerability_match,
                asset_type=row.asset_type,
                hostname_pattern=row.hostname_pattern,
                granted_by=row.granted_by,
                granted_at=row.granted_at,
                confluence_link=row.confluence_link,
                status=ExceptionStatus.ACTIVE,
                created_by_id=imported_by_id,
            )
        )
        created += 1

    db.flush()
    return created
