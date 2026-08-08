import os
from collections.abc import Generator

os.environ["VULNASSIST_DATABASE_URL"] = "sqlite:///:memory:"
os.environ["VULNASSIST_SECRET_KEY"] = "test-secret-key"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.enums import Severity, UserRole
from app.models.rules import CAAConfig, SLERule
from app.models.team import Team
from app.models.user import User

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session() -> Generator:
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    db_session.add(
        CAAConfig(
            name="test-config",
            is_active=True,
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
        )
    )
    db_session.add(SLERule(severity=Severity.CRITIQUE, caa_min=8.5, caa_max=10.0, delay_days=15))
    db_session.add(SLERule(severity=Severity.HAUTE, caa_min=6.5, caa_max=8.49, delay_days=30))
    db_session.add(SLERule(severity=Severity.MOYENNE, caa_min=4.0, caa_max=6.49, delay_days=90))
    db_session.add(SLERule(severity=Severity.FAIBLE, caa_min=0.0, caa_max=3.99, delay_days=180))

    admin = User(
        email="admin@test.internal",
        full_name="Test Admin",
        role=UserRole.ADMIN,
        hashed_password=hash_password("Password123!"),
        is_active=True,
    )
    db_session.add(admin)
    db_session.add(Team(name="Serveurs"))
    db_session.commit()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def admin_token(client) -> str:
    resp = client.post("/api/auth/login", json={"email": "admin@test.internal", "password": "Password123!"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]
