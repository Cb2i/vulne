"""Bootstraps a fresh installation: creates tables, a default admin user, a default
CAA scoring configuration, default SLE delay rules, and a starter team so the
application is immediately usable after `python -m app.seed`.

Safe to re-run: every step is idempotent (skipped if data already exists).
"""
import sys

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.enums import Severity, UserRole
from app.models.rules import CAAConfig, SLERule
from app.models.team import Team
from app.models.user import User

settings = get_settings()

DEFAULT_SLE_RULES = [
    (Severity.CRITIQUE, 8.5, 10.0, 15),
    (Severity.HAUTE, 6.5, 8.49, 30),
    (Severity.MOYENNE, 4.0, 6.49, 90),
    (Severity.FAIBLE, 0.0, 3.99, 180),
]

DEFAULT_TEAMS = ["Postes de travail", "Serveurs", "Infrastructure réseau", "Applications"]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.scalar(select(CAAConfig)):
            db.add(
                CAAConfig(
                    name="Configuration CAA par défaut",
                    description="Pondérations initiales inspirées du prototype VulnContext.",
                    weight_exposition_internet=1.5,
                    weight_exposition_dmz=0.5,
                    weight_exposition_internal=-0.5,
                    weight_exposition_airgapped=-2.0,
                    weight_criticite_critical=2.5,
                    weight_criticite_high=1.5,
                    weight_criticite_medium=0.0,
                    weight_criticite_low=-1.0,
                    weight_exploitable=2.0,
                    normalization_divisor=1.0,
                    is_active=True,
                )
            )
            print("Created default CAA configuration.")

        if not db.scalar(select(SLERule)):
            for severity, caa_min, caa_max, delay in DEFAULT_SLE_RULES:
                db.add(SLERule(severity=severity, caa_min=caa_min, caa_max=caa_max, delay_days=delay))
            print("Created default SLE rules.")

        teams_by_name = {}
        for name in DEFAULT_TEAMS:
            team = db.scalar(select(Team).where(Team.name == name))
            if not team:
                team = Team(name=name)
                db.add(team)
                db.flush()
                print(f"Created team '{name}'.")
            teams_by_name[name] = team

        if not db.scalar(select(User)):
            admin = User(
                email=settings.default_admin_email,
                full_name="Administrateur VulnAssist",
                role=UserRole.ADMIN,
                hashed_password=hash_password(settings.default_admin_password),
                is_active=True,
            )
            db.add(admin)
            print(
                f"Created default admin user: {settings.default_admin_email} "
                f"(password: {settings.default_admin_password}) — change it immediately after first login."
            )

        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    sys.exit(0)
