import uuid
from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from app.models.base import Base
from app.models import (  # noqa: F401
    Building,
    Lease,
    LeaseRentHistory,
    OwnerProfile,
    RefreshToken,
    Role,
    Tenant,
    Unit,
    UnitPhoto,
    UnitTenantHistory,
    User,
    UserBuildingAssignment,
    UserOwnerAssignment,
    UserPermission,
)

ROLE_IDS = {
    "super_admin": uuid.UUID("00000000-0000-4000-8000-000000000001"),
    "admin_familial": uuid.UUID("00000000-0000-4000-8000-000000000002"),
    "proprietaire": uuid.UUID("00000000-0000-4000-8000-000000000003"),
    "gestionnaire": uuid.UUID("00000000-0000-4000-8000-000000000004"),
    "visiteur": uuid.UUID("00000000-0000-4000-8000-000000000005"),
    "locataire": uuid.UUID("00000000-0000-4000-8000-000000000006"),
}


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = session_local()
    now = datetime.now(UTC)

    for role in [
        Role(
            id=ROLE_IDS["super_admin"],
            code="super_admin",
            label="Super Administrateur",
            created_at=now,
        ),
        Role(
            id=ROLE_IDS["admin_familial"],
            code="admin_familial",
            label="Administrateur Familial",
            created_at=now,
        ),
        Role(
            id=ROLE_IDS["proprietaire"],
            code="proprietaire",
            label="Propriétaire",
            created_at=now,
        ),
        Role(
            id=ROLE_IDS["gestionnaire"],
            code="gestionnaire",
            label="Gestionnaire",
            created_at=now,
        ),
        Role(
            id=ROLE_IDS["visiteur"],
            code="visiteur",
            label="Visiteur",
            created_at=now,
        ),
        Role(
            id=ROLE_IDS["locataire"],
            code="locataire",
            label="Locataire",
            created_at=now,
        ),
    ]:
        db.add(role)

    for user in [
        User(
            id=uuid.UUID("00000000-0000-4000-8000-000000000010"),
            email="admin@gestion-immo.local",
            password_hash=hash_password("Admin123!"),
            first_name="Super",
            last_name="Admin",
            role_id=ROLE_IDS["super_admin"],
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
        User(
            id=uuid.UUID("00000000-0000-4000-8000-000000000011"),
            email="gestionnaire@gestion-immo.local",
            password_hash=hash_password("Agent123!"),
            first_name="Jean",
            last_name="Gestionnaire",
            role_id=ROLE_IDS["gestionnaire"],
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
    ]:
        db.add(user)

    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
