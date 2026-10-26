from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app import app


def test_health_endpoint():
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_meters_returns_all_records():
    mock_portal = MagicMock()
    mock_portal.get_all_meters.return_value = [
        {"meterId": "J100000", "make": "HPL"},
        {"meterId": "J100001", "make": "Genus"},
    ]

    with patch.dict("os.environ", {
        "URJA_EMAIL": "test@example.com",
        "URJA_PASSWORD": "test-password",
    }):
        with patch("app.UrjaPortalClient", return_value=mock_portal):
            with TestClient(app) as test_client:
                response = test_client.get("/api/v1/meters")

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["data"]) == 2
    mock_portal.get_all_meters.assert_called_once_with(query="")
