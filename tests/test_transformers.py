from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app import app


def test_meter_search():
    mock_portal = MagicMock()
    mock_portal.get_all_meters.return_value = [
        {"meterId": "J100000", "make": "HPL"}
    ]

    with patch.dict(
        "os.environ",
        {
            "URJA_EMAIL": "test@example.com",
            "URJA_PASSWORD": "test-password",
        },
    ):
        with patch("app.UrjaPortalClient", return_value=mock_portal):
            with TestClient(app) as test_client:
                response = test_client.get(
                    "/api/v1/meters",
                    params={"q": "J100000"},
                )

    assert response.status_code == 200

    body = response.json()
    assert body["total"] == 1
    assert body["data"][0]["meterId"] == "J100000"

    mock_portal.get_all_meters.assert_called_once_with(query="J100000")


def test_meter_pagination():
    mock_portal = MagicMock()
    mock_portal.get_meter_page.return_value = {
        "data": [{"meterId": "J000020"}],
        "total": 403,
        "page": 2,
        "pageSize": 20,
    }

    with patch.dict(
        "os.environ",
        {
            "URJA_EMAIL": "test@example.com",
            "URJA_PASSWORD": "test-password",
        },
    ):
        with patch("app.UrjaPortalClient", return_value=mock_portal):
            with TestClient(app) as test_client:
                response = test_client.get(
                    "/api/v1/meters",
                    params={"page": 2},
                )

    assert response.status_code == 200

    body = response.json()
    assert body["page"] == 2
    assert body["total"] == 403
    assert len(body["data"]) == 1

    mock_portal.get_meter_page.assert_called_once_with(
        query="",
        page=2,
    )


def test_transformer_page():
    mock_portal = MagicMock()
    mock_portal.get_all_transformers.return_value = [
        {
            "code": "DT-001",
            "name": "Malviya Nagar DT 1",
            "feederCode": "F-001",
            "capacityKva": 100,
        },
        {
            "code": "DT-002",
            "name": "Mansarovar DT 2",
            "feederCode": "F-002",
            "capacityKva": 63,
        },
    ]

    with patch.dict(
        "os.environ",
        {
            "URJA_EMAIL": "test@example.com",
            "URJA_PASSWORD": "test-password",
        },
    ):
        with patch("app.UrjaPortalClient", return_value=mock_portal):
            with TestClient(app) as test_client:
                response = test_client.get(
                    "/api/v1/transformers",
                    params={"page": 1},
                )

    assert response.status_code == 200

    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 2
    assert body[0]["code"] == "DT-001"
    assert body[1]["code"] == "DT-002"

    mock_portal.get_all_transformers.assert_called_once_with(page=1)
