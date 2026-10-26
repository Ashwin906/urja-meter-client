
from unittest.mock import MagicMock, patch

import httpx
from fastapi.testclient import TestClient

from app import app


def make_upstream_404():
    request = httpx.Request(
        "GET",
        "https://urja-ops.flockenergy.tech/portal/meters/INVALID/geo",
    )
    response = httpx.Response(404, request=request)

    return httpx.HTTPStatusError(
        "Not found",
        request=request,
        response=response,
    )


def test_meter_geo_returns_data():
    mock_portal = MagicMock()
    mock_portal.get_meter_geo.return_value = {
        "data": {
            "latitude": "26.938961002479868",
            "longitude": "75.83095696146852",
        }
    }

    with patch.dict(
        "os.environ",
        {
            "URJA_EMAIL": "test@example.com",
            "URJA_PASSWORD": "test-password",
        },
    ):
        with patch("app.UrjaPortalClient", return_value=mock_portal):
            with TestClient(app) as client:
                result = client.get("/api/v1/meters/J100000/geo")

    assert result.status_code == 200
    assert result.json()["data"]["latitude"] == "26.938961002479868"
    assert result.json()["data"]["longitude"] == "75.83095696146852"


def test_meter_geo_returns_404_for_missing_data():
    mock_portal = MagicMock()
    mock_portal.get_meter_geo.side_effect = make_upstream_404()

    with patch.dict(
        "os.environ",
        {
            "URJA_EMAIL": "test@example.com",
            "URJA_PASSWORD": "test-password",
        },
    ):
        with patch("app.UrjaPortalClient", return_value=mock_portal):
            with TestClient(app) as client:
                result = client.get("/api/v1/meters/INVALID/geo")

    assert result.status_code == 404
    assert result.json()["detail"] == "Meter geography not found"
