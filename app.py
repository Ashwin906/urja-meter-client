import os
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel

from client import UrjaPortalClient


class MeterRecord(BaseModel):
    meterId: str
    serialNo: str
    make: str
    phaseType: str
    installStatus: str
    dtCode: str


class MeterListResponse(BaseModel):
    data: list[MeterRecord]
    total: int


class MeterPageResponse(BaseModel):
    data: list[MeterRecord]
    total: int
    page: int
    pageSize: int


class MeterGeoData(BaseModel):
    latitude: str
    longitude: str


class MeterGeoResponse(BaseModel):
    data: MeterGeoData


class EnergyReading(BaseModel):
    timestamp: str
    kwh: str
    kvah: str
    voltR: str


class MeterEnergyResponse(BaseModel):
    data: list[EnergyReading]


class ErrorResponse(BaseModel):
    detail: str



@asynccontextmanager
async def lifespan(app: FastAPI):
    email = os.environ.get("URJA_EMAIL")
    password = os.environ.get("URJA_PASSWORD")

    if not email or not password:
        raise RuntimeError(
            "Set URJA_EMAIL and URJA_PASSWORD environment variables."
        )

    portal = UrjaPortalClient(email, password)
    app.state.portal_client = portal

    try:
        yield
    finally:
        portal.close()


app = FastAPI(
    title="Urja Meter API",
    description="REST API wrapper for the legacy Urja Meter Ops portal.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get(
    "/api/v1/meters",
    responses={
        502: {
            "model": ErrorResponse,
            "description": "Upstream portal or retrieval error.",
        }
    },
)
def list_meters(
    request: Request,
    q: str | None = Query(
        default=None,
        description="Optional meter search query.",
    ),
    page: int | None = Query(
        default=None,
        ge=1,
        description="Upstream page number. Omit to retrieve all matching meters.",
    ),
):
    portal = request.app.state.portal_client
    query = q or ""

    try:
        if page is not None:
            result = portal.get_meter_page(query=query, page=page)
            return result

        meters = portal.get_all_meters(query=query)

        return {
            "data": meters,
            "total": len(meters),
        }

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail="The upstream portal returned an HTTP error.",
        ) from exc
    except (httpx.RequestError, RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve a complete meter result from the portal.",
        ) from exc

@app.get(
    "/api/v1/meters/{meter_id}/geo",
    response_model=MeterGeoResponse,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Meter geography not found.",
        },
        502: {
            "model": ErrorResponse,
            "description": "Upstream portal or request error.",
        },
    },
)
def meter_geo(meter_id: str, request: Request):
    portal = request.app.state.portal_client

    try:
        return portal.get_meter_geo(meter_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Meter geography not found",
            ) from exc

        raise HTTPException(
            status_code=502,
            detail="Upstream portal returned an HTTP error",
        ) from exc
    except (httpx.RequestError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve meter geography",
        ) from exc


@app.get(
    "/api/v1/meters/{meter_id}/energy",
    response_model=MeterEnergyResponse,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Meter energy readings not found.",
        },
        502: {
            "model": ErrorResponse,
            "description": "Upstream portal or request error.",
        },
    },
)
def meter_energy(meter_id: str, request: Request):
    portal = request.app.state.portal_client

    try:
        return portal.get_meter_energy(meter_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Meter energy readings not found",
            ) from exc

        raise HTTPException(
            status_code=502,
            detail="Upstream portal returned an HTTP error",
        ) from exc
    except (httpx.RequestError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve meter energy readings",
        ) from exc

@app.get(
    "/api/v1/transformers",
    responses={
        502: {
            "model": ErrorResponse,
            "description": "Upstream portal or request error.",
        },
    },
)
def list_transformers(
    request: Request,
    page: int = Query(default=1, ge=1),
):
    portal = request.app.state.portal_client

    try:
        return portal.get_all_transformers(page=page)

    except httpx.HTTPStatusError as exc:
        print("Upstream status:", exc.response.status_code)
        print("Upstream URL:", exc.request.url)
        print("Upstream response:", exc.response.text[:1000])

        raise HTTPException(
            status_code=502,
            detail="The upstream portal returned an HTTP error",
        ) from exc

    except httpx.RequestError as exc:
        print("Upstream request error:", repr(exc))

        raise HTTPException(
            status_code=502,
            detail="Unable to connect to the upstream portal",
        ) from exc

    except Exception as exc:
        print("Unexpected error:", repr(exc))
        raise