from unittest.mock import MagicMock, patch

import httpx
from fastapi.testclient import TestClient

from app import app


def test_meter_upstream_http_error():
    mock_portal = MagicMock()
    request = httpx.Request(
        "GET",
        "https://urja-ops.flockenergy.tech/portal/meters/search",
    )
    response = httpx.Response(503, request=request)

    mock_portal.get_all_meters.side_effect = httpx.HTTPStatusError(
        "Upstream unavailable",
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
            with TestClient(app) as test_client:
                result = test_client.get("/api/v1/meters")

    assert result.status_code == 502
    assert "upstream" in result.json()["detail"].lower()


def test_transformer_upstream_http_error():
    mock_portal = MagicMock()
    request = httpx.Request(
        "GET",
        "https://urja-ops.flockenergy.tech/portal/dts?page=1",
    )
    response = httpx.Response(503, request=request)

    mock_portal.get_all_transformers.side_effect = httpx.HTTPStatusError(
        "Upstream unavailable",
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
            with TestClient(app) as test_client:
                result = test_client.get("/api/v1/transformers?page=1")

    assert result.status_code == 502
    assert "upstream" in result.json()["detail"].lower()
