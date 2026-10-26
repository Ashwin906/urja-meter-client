
from unittest.mock import MagicMock, patch

import httpx
from fastapi.testclient import TestClient

from app import app


def test_meter_energy_returns_data():
    mock_portal = MagicMock()
    mock_portal.get_meter_energy.return_value = {
        "data": [
            {
                "timestamp": "30/06/2026 23:30",
                "kwh": "125.50",
                "kvah": "130.20",
                "voltR": "230.1",
            }
        ]
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
                result = client.get("/api/v1/meters/J100000/energy")

    assert result.status_code == 200
    assert len(result.json()["data"]) == 1
    assert result.json()["data"][0]["timestamp"] == "30/06/2026 23:30"
    assert result.json()["data"][0]["kwh"] == "125.50"


def test_meter_energy_returns_404_for_missing_meter():
    mock_portal = MagicMock()

    request = httpx.Request(
        "GET",
        "https://urja-ops.flockenergy.tech/portal/meters/INVALID/energy",
    )
    response = httpx.Response(404, request=request)

    mock_portal.get_meter_energy.side_effect = httpx.HTTPStatusError(
        "Not found",
        request=request,
        response=response,
    )

    with patch.dict(
        "os.environ",
        {
            "URJA_EMAIL": "test@example.com",
            "URJA_PASSWORD": "test-password",
        },
    ):
        with patch("app.UrjaPortalClient", return_value=mock_portal):
            with TestClient(app) as client:
                result = client.get("/api/v1/meters/INVALID/energy")

    assert result.status_code == 404
