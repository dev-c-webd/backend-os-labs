from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.db.database import get_db
from app.main import app


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
