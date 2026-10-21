from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.db.database import get_db
from app.main import app

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.modules.notes.models import Note

TEST_DATABASE_URL = (
    "postgresql+psycopg://test_user:test_only_password"
    "@127.0.0.1:55432/backend_foundation_test"
)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def fake_db():
    fake_result = MagicMock()
    fake_result.scalar_one.return_value = 1

    fake_session = MagicMock()
    fake_session.execute.return_value = fake_result

    def override_get_db():
        yield fake_session

    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db

    try:
        yield fake_session
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override


@pytest.fixture
def postgres_db():
    engine = create_engine(TEST_DATABASE_URL)
    connection = engine.connect()
    transaction = connection.begin()

    TestSessionLocal = sessionmaker(
        bind=connection,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    db = TestSessionLocal()

    def override_get_db():
        yield db

    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db

    try:
        yield db
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override

        db.close()
        transaction.rollback()
        connection.close()
        engine.dispose()


def test_check_with_real_postgres(
    client: TestClient,
    postgres_db: Session,
):
    result = postgres_db.execute(text("SELECT 1"))

    assert result.scalar_one() == 1

    response = client.get("/check")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_returns_setup_message(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == "setup initial"


def test_check_returns_ok_without_real_database(
    client: TestClient,
    fake_db: MagicMock,
):
    response = client.get("/check")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    fake_db.execute.assert_called_once()
    fake_db.execute.return_value.scalar_one.assert_called_once()


def test_note_can_be_saved_and_retrieved(postgres_db: Session):
    # Create a note and save it to PostgreSQL.
    note = Note(title="Integration test note")
    postgres_db.add(note)
    postgres_db.commit()

    # Keep the generated ID, then clear the session's object cache.
    note_id = note.id
    postgres_db.expunge_all()

    # Retrieve the note again from the database.
    retrieved_note = postgres_db.get(Note, note_id)

    assert retrieved_note is not None
    assert retrieved_note.id == note_id
    assert retrieved_note.title == "Integration test note"
    assert retrieved_note.created_at is not None
