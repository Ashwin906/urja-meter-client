# PROTOCOL.md

# Urja Meter Ops Portal — Protocol Notes

## 1. Overview

This document describes the observed HTTP behavior of the legacy Urja Meter Ops portal at:

`https://urja-ops.flockenergy.tech`

The portal provides meter search and pagination, meter geographic coordinates, energy readings, and transformer data. The observations were collected using Firefox Developer Tools and validated through an HTTPX-based Python client.

This document records the upstream portal's observed behavior. The public REST API exposed by this project is a separate interface and may use different routes or response conventions.

### Evidence classification

- **Verified:** Directly observed in browser Network responses and/or successfully tested through the Python client.
- **Partially verified:** The endpoint works, but not all response fields or behaviors have been recorded.
- **Unverified:** Additional investigation is required before making a definitive claim.

## 2. Authentication

### 2.1 Login request

- **Method:** `POST`
- **Path:** `/login`
- **Content type:** `application/x-www-form-urlencoded`
- **Form fields:**
  - `email`
  - `password`

### 2.2 Successful login response

The browser's successful login request returned HTTP `200` with a JSON response containing:

```json
{
  "type": "redirect",
  "status": 303,
  "location": "/meters"
}
```

The `status` value in this JSON represents an application-level redirect instruction. The actual HTTP response status observed was `200`, not `303`.

The response also set a session cookie named `__Secure-better-auth.session_token`. The browser showed the cookie with `HttpOnly`, `Secure`, and `SameSite=Lax` attributes.

The session cookie value is sensitive and must not be included in this document, source code, logs, or version control.

### 2.3 Request validation

A Python login request initially returned HTTP `403` with the message:

`Cross-site POST form submissions are forbidden`

The successful browser request included these headers:

- `Origin`
- `Referer`
- `Content-Type`
- `x-sveltekit-action`

Adding the observed `Origin`, `Referer`, and `x-sveltekit-action` headers to the Python POST request resolved the login failure in the tested environment.

The Python client uses a persistent HTTPX client to retain cookies between requests. A `GET /login` request returned HTTP `200` but did not set a cookie in the tested session.

**Status: Verified in the tested environment.**

## 3. Meter Search and Pagination

### 3.1 Endpoint

- **Method:** `GET`
- **Path:** `/portal/meters/search`

Example request:

`GET /portal/meters/search?q=&page=1`

### 3.2 Query parameters

| Parameter | Observed behavior |
|---|---|
| `q` | Search query; an empty value retrieves the unfiltered list |
| `page` | Selects the requested result page |

The first page returned 20 records. The response reported 403 matching records and a page size of 20.

### 3.3 Response structure

The observed response includes:

| Field | Description |
|---|---|
| `data` | Array of meter records |
| `total` | Total number of matching records |
| `page` | Current page number |
| `pageSize` | Number of records per page |

Example structure:

```json
{
  "data": [
    {
      "meterId": "J100000",
      "serialNo": "SE33962",
      "make": "HPL",
      "phaseType": "single",
      "installStatus": "Decommissioned",
      "dtCode": "DT-001"
    }
  ],
  "total": 403,
  "page": 1,
  "pageSize": 20
}
```

The example illustrates the observed field names; the complete response contains multiple records.

### 3.4 Verified search behavior

A request with `q=J100000` returned one matching meter:

- `total`: `1`
- `page`: `1`
- `pageSize`: `20`
- Number of records in `data`: `1`

A request for page 2 with an empty query returned another page containing 20 records, while the reported total remained 403.

The Python client successfully retrieved all 403 records by iterating through the pages. Validation of the extracted dataset reported 403 unique meter IDs.

The portal's ordering guarantees and behavior if the dataset changes during pagination have not been independently established.

**Status: Verified.**

## 4. Meter Geographic Coordinates

### 4.1 Endpoint

- **Method:** `GET`
- **Path:** `/portal/meters/{meter_id}/geo`

Example:

`GET /portal/meters/J100000/geo`

### 4.2 Response structure

The observed successful response was:

```json
{
  "data": {
    "latitude": "26.938961002479868",
    "longitude": "75.83095696146852"
  }
}
```

Both coordinate values were returned as strings.

The coordinates are specific to the observed meter and should not be treated as representative values for other meters.

**Status: Verified.**

## 5. Meter Energy Readings

### 5.1 Endpoint

- **Method:** `GET`
- **Path:** `/portal/meters/{meter_id}/energy`

Example:

`GET /portal/meters/J100000/energy`

### 5.2 Response structure

The response contains a `data` array of energy readings. For meter `J100000`, the observed response contained 337 records.

The fields observed in each reading were:

| Field | Description | Observed type |
|---|---|---|
| `timestamp` | Reading timestamp | String |
| `kwh` | Energy reading in kWh, as represented by the field name | String |
| `kvah` | Energy reading in kVAh, as represented by the field name | String |
| `voltR` | R-phase voltage field | String |

Example reading:

```json
{
  "timestamp": "23/06/2026 23:30",
  "kwh": "48438.74",
  "kvah": "52313.84",
  "voltR": "226"
}
```

The observed timestamps use the format `DD/MM/YYYY HH:mm`, with readings spaced at 30-minute intervals in the inspected dataset.

The inspected data ranged from `23/06/2026 23:30` through `30/06/2026 23:30`.

The timestamp does not include an explicit timezone. No timezone should be inferred from the string alone.

The observed values are strings. Any numeric conversion or timestamp normalization performed by the wrapper should be documented separately.

**Status: Verified for the inspected meter.** The same record count and time range are not guaranteed for every meter.

## 6. Transformer Data

### 6.1 Endpoint

- **Method:** `GET`
- **Path:** `/portal/dts`

Example:

`GET /portal/dts?page=1`

The successful browser request returned HTTP `200` with content type `application/json`.

An earlier request to `/portal/transformers/dts?page=1` returned HTTP `404` with an HTML response. The verified route for transformer listing is `/portal/dts`.

### 6.2 Observed fields

Transformer records were observed to contain fields including:

- `code`
- `name`
- `feederCode`
- `capacityKva`

The response contains a `data` array.

The transformer page displayed 20 records in the observed listing. The complete set of pagination metadata and the behavior for invalid page numbers should be confirmed against the actual JSON responses before being documented as protocol guarantees.

The Python client successfully retrieves transformer data and supports full extraction through its `get_all_transformers()` method.

**Status: Endpoint and listed fields verified.** Complete response schema and pagination guarantees require confirmation.

## 7. Meter Detail Page

### 7.1 Endpoint

- **Method:** `GET`
- **Path:** `/meters/{meter_id}`
- **Response:** HTML document

Example:

`GET /meters/J100000`

### 7.2 Observed page content

The meter detail page for `J100000` displays the following nameplate fields:

- Meter ID
- Serial No
- Make
- Phase Type
- Installation Status
- Installation Type

The page also displays the distribution hierarchy:

Zone → Circle → Division → Subdivision → Substation → Feeder → Distribution Transformer.

For the inspected meter, the displayed hierarchy was Jaipur Zone 1 (Z-01), Circle 1 (C-01), Division 1 (D-01), Subdivision 1 (SD-01), Substation 1 (SS-01), Feeder 1 (F-001), and Malviya Nagar DT 1 (DT-001).

The page displays geographic coordinates. A separate request to `/portal/meters/{meter_id}/geo` returns latitude and longitude as JSON.

### 7.3 Data access limitations

The observed detail-page request returns HTML. The inspected Network view showed the document request and the geography JSON request; it did not establish a separate JSON endpoint containing the complete nameplate and hierarchy.

Therefore, this section documents the rendered page behavior and does not claim that a dedicated JSON detail endpoint exists.

**Status: HTML page and displayed fields verified; dedicated JSON detail endpoint unverified.**
## 8. Bulk Meter Export

The portal provides an interface action labelled "Export all meters".

The downloaded JSON file inspected during development contained 403 meter records and 403 unique meter IDs. The records included meter metadata and hierarchy/geographic information.

The export file was used to inspect and validate the dataset. The exact HTTP request or internal mechanism responsible for producing the export has not been conclusively recorded in this document.

The export data is not the same as the energy time-series response.

**Status: Export output verified; underlying request mechanism unverified.**

## 9. Error Handling and Observed Failures

### 9.1 Authentication failure

A Python login POST initially returned HTTP `403` with:

`Cross-site POST form submissions are forbidden`

The issue was resolved in the tested client by matching relevant request headers observed in the successful browser request.

### 9.2 Incorrect transformer path

The request:

`GET /portal/transformers/dts?page=1`

returned HTTP `404` with an HTML response.

The corrected request:

`GET /portal/dts?page=1`

returned HTTP `200` with JSON.

### 9.3 Public API behavior

The wrapper has been tested for successful meter listing, meter search, meter pagination, geography, energy readings, and transformer listing.

The wrapper currently maps upstream HTTP failures to HTTP `502` in the relevant routes. This is the wrapper's error-handling policy, not an observed upstream status code.

The full behavior for invalid IDs, expired sessions, upstream timeouts, malformed JSON, and upstream rate limits still needs systematic testing and documentation.

## 10. Public API Versus Upstream API

The wrapper's public endpoints are designed for consumers of this project. They must not be confused with the upstream portal routes documented above.

The implemented public endpoints include:

| Public endpoint | Purpose |
|---|---|
| `GET /health` | Health check |
| `GET /api/v1/meters` | List meters, with optional search and pagination |
| `GET /api/v1/meters/{meter_id}/geo` | Retrieve meter coordinates |
| `GET /api/v1/meters/{meter_id}/energy` | Retrieve meter energy readings |
| `GET /api/v1/transformers` | Retrieve transformer data |

A dedicated public meter-detail endpoint should only be documented as implemented if its behavior is confirmed in the actual application.

## 11. Known Limitations and Open Questions

The following items require additional verification:

1. The exact JSON endpoint, if any, for complete meter details and hierarchy.
2. The complete transformer response schema and pagination metadata.
3. Whether the upstream service guarantees stable ordering across pages.
4. The timezone, if any, intended for energy timestamps.
5. The precise upstream responses for invalid meter IDs and invalid page numbers.
6. The upstream behavior for expired sessions, throttling, and temporary service failures.
7. The exact mechanism behind the bulk meter export action.

These unknowns should remain explicit until confirmed through additional observation or testing.

## 12. Reproducibility and Security

- Authenticate using credentials supplied through the application's configuration or environment variables.
- Do not commit passwords, session tokens, or cookie values.
- Use the persistent HTTPX client to maintain the authenticated session.
- Validate upstream response structures before using them.
- During bulk extraction, propagate failures instead of returning an incomplete dataset as complete.
- Record upstream behavior from actual HTTP requests and responses rather than inferring undocumented guarantees.
