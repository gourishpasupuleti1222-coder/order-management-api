from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.dependencies import get_db
from app.main import app


TEST_DATABASE_FILE = Path("test_order_management.db")
TEST_DATABASE_URL = "sqlite:///./test_order_management.db"


test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)


TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """
    Create a fresh test database for every test.

    After the test finishes, all tables and test data are removed.
    """

    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)

        if TEST_DATABASE_FILE.exists():
            try:
                TEST_DATABASE_FILE.unlink()
            except PermissionError:
                pass


@pytest.fixture
def client(
    db: Session,
) -> Generator[TestClient, None, None]:
    """
    Replace the application's normal database dependency
    with the test database session.
    """

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()