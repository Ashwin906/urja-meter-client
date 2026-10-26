# Urja Meter API

A REST API wrapper for the legacy Urja Meter Ops portal. The project provides endpoints to retrieve meter information, meter geography, energy readings, and transformer information through a FastAPI application.

## Features

- Retrieve meter records from the portal.
- Search meters using a query parameter.
- Retrieve a specific page of meter records or fetch all matching records.
- Retrieve geographical coordinates for a meter.
- Retrieve energy readings for a meter.
- Retrieve transformer information with page selection.
- Handle upstream HTTP and request errors.
- Generate an OpenAPI specification through FastAPI.
- Run automated tests using pytest.

## Tech Stack

- Python
- FastAPI
- HTTPX
- Pydantic
- Uvicorn
- pytest

## Project Structure

```text
meter-data-client/
├── app.py
├── client.py
├── openapi.json
├── PROTOCOL.md
├── README.md
├── requirements.txt
└── tests/
    ├── test_energy.py
    ├── test_errors.py
    ├── test_meter_details.py
    ├── test_meters.py
    └── test_transformers.py
```

## Requirements

- Python 3.10 or later
- Access to the Urja Meter Ops portal
- Valid portal login credentials

## Setup

Clone the repository and move into the project directory:

```bash
git clone <your-github-repository-url>
cd meter-data-client
```

Create and activate a virtual environment.

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Configuration

Set the credentials used by the upstream portal client as environment variables. Do not commit actual credentials or session cookies to the repository.

**Windows PowerShell:**

```powershell
$env:URJA_EMAIL = "your-email@example.com"
$env:URJA_PASSWORD = "your-password"
```

These variables must be set in the terminal where the application is started.

## Run the Application

Start the development server:

```powershell
uvicorn app:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

The generated OpenAPI specification is available at:

```text
http://127.0.0.1:8000/openapi.json
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check whether the API is running |
| GET | `/api/v1/meters` | Retrieve meter records |
| GET | `/api/v1/meters/{meter_id}/geo` | Retrieve meter geographical coordinates |
| GET | `/api/v1/meters/{meter_id}/energy` | Retrieve meter energy readings |
| GET | `/api/v1/transformers` | Retrieve transformer information |

### 1. Health Check

```http
GET /health
```

Returns the application health status.

### 2. List and Search Meters

Retrieve all matching meter records:

```http
GET /api/v1/meters
```

Search for a meter using the `q` parameter:

```http
GET /api/v1/meters?q=J100000
```

Retrieve a specific page:

```http
GET /api/v1/meters?page=2
```

Combine search and pagination:

```http
GET /api/v1/meters?q=J100000&page=1
```

When `page` is omitted, the wrapper retrieves all matching records. When `page` is supplied, it returns the selected upstream page.

### 3. Meter Geography

```http
GET /api/v1/meters/J100000/geo
```

Returns the geographical coordinates associated with the requested meter when available.

### 4. Meter Energy Readings

```http
GET /api/v1/meters/J100000/energy
```

Returns the energy readings available for the requested meter. Observed fields include the timestamp, kWh, kVAh, and `voltR` values.

### 5. List Transformers

```http
GET /api/v1/transformers
```

Retrieve a selected page:

```http
GET /api/v1/transformers?page=2
```

The `page` parameter must be greater than or equal to 1.

## Error Handling

The wrapper translates selected upstream failures into HTTP responses from the public API.

- **404 Not Found:** Used by the geography and energy endpoints when the upstream request returns a 404.
- **502 Bad Gateway:** Used when the wrapper encounters applicable upstream HTTP errors or request failures.
- **422 Unprocessable Entity:** FastAPI returns this for invalid request parameters, such as a page number below the allowed minimum.

The exact error response depends on the endpoint and the failure encountered.

## Running Tests

Run the automated test suite from the project root:

```powershell
python -m pytest -v
```

The tests cover meter retrieval and pagination, transformer retrieval, geography, energy readings, and selected error-handling cases. The tests use mocked upstream responses where appropriate, so those cases do not require live portal requests.

## Upstream Protocol

The upstream portal uses an authenticated session. The client maintains the session and sends requests to the portal's endpoints.

Observed upstream behavior, request details, pagination, response structures, and known limitations are documented separately in [`PROTOCOL.md`](PROTOCOL.md).

## Design Decisions and Limitations

The wrapper separates the public REST API from the upstream portal client. The FastAPI application exposes the public endpoints, while `client.py` handles communication with the portal.

The implementation depends on the portal's existing authentication flow and response formats. Changes to the upstream portal may require corresponding changes to the client.

Some behavior of the legacy portal has been verified through observed requests and responses; unverified behavior should not be treated as part of the API contract.

