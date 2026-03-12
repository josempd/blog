from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Connection
from sqlmodel import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session")
def _db_connection() -> Generator[Connection]:
    """Session-scoped connection with an outer transaction that never commits."""
    with Session(engine) as setup_session:
        init_db(setup_session)

    connection = engine.connect()
    transaction = connection.begin()
    yield connection
    transaction.rollback()
    connection.close()


@pytest.fixture()
def db(_db_connection: Connection) -> Generator[Session]:
    """Function-scoped session on a savepoint. Rolls back after each test."""
    nested = _db_connection.begin_nested()
    session = Session(bind=_db_connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    nested.rollback()


@pytest.fixture()
def client(db: Session) -> Generator[TestClient]:
    """Function-scoped TestClient sharing the test's DB session."""

    def _override_get_db() -> Generator[Session]:
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    app.state.limiter.enabled = False
    with TestClient(app) as c:
        yield c
    app.state.limiter.enabled = True
    app.dependency_overrides.clear()


@pytest.fixture()
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture()
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
