# AssetGuard AI — API Documentation

## Overview

AssetGuard AI is a Flask-based REST backend that provides:

- User authentication and role-based access control
- Shared location management
- Asset and load-capacity management
- Engineering load compliance evaluation
- Bulk import of AI-generated asset JSON payloads

**Base path** for all application APIs:

```
/api/v1
```

---

## Table of Contents

1. [Authentication](#authentication)
2. [Roles & Permissions](#roles--permissions)
3. [Standard Response Format](#standard-response-format)
4. [HTTP Status Codes](#http-status-codes)
5. [Enum Reference](#enum-reference)
6. [Health](#health)
7. [Auth APIs](#auth-apis)
8. [Location APIs](#location-apis)
9. [Asset APIs](#asset-apis)
10. [Evaluation APIs](#evaluation-apis)
11. [AI JSON Import Workflow](#ai-json-import-workflow)

---

## Authentication

The API uses **Bearer token** authentication.

1. Call `POST /api/v1/auth/login` with your credentials.
2. Copy the `token` from the response.
3. Include it in every subsequent request:

```http
Authorization: Bearer <token>
```

---

## Roles & Permissions

| Role | Description |
|------|-------------|
| `System_Admin` | Full access, including user management and AI import |
| `Asset_Manager` | Can create and manage assets and load capacities |
| `Contractors` | Read-only access; can run load evaluations |

---

## Standard Response Format

### Success

```json
{
  "success": true,
  "data": {}
}
```

Some success responses also include a `message` field:

```json
{
  "success": true,
  "message": "Operation completed",
  "data": {}
}
```

### Error

```json
{
  "success": false,
  "message": "Human-readable error description",
  "code": "machine_readable_error_code"
}
```

Some error responses include an additional `details` field with more context.

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200 OK` | Successful read or operation without new resource creation |
| `201 Created` | Successful creation that produced a new record |
| `400 Bad Request` | Validation error or business rule violation |
| `401 Unauthorized` | Missing or invalid credentials |
| `403 Forbidden` | Insufficient role permissions |
| `404 Not Found` | Resource does not exist |
| `409 Conflict` | Duplicate resource violation |
| `500 Internal Server Error` | Unexpected server failure |

---

## Enum Reference

### Load Capacity Names

Each capacity name is bound to exactly one allowed metric (enforced at creation and update).

| `name` | Required `metric` |
|--------|-------------------|
| `max point load` | `kN` |
| `max axle load` | `t` |
| `max uniform distributor load` | `kPa` |
| `max displacement size` | `t` |

### Load Metrics

- `kN`
- `t`
- `kPa`

### User Roles

- `System_Admin`
- `Asset_Manager`
- `Contractors`

### Equipment Types

Equipment types are mapped internally to the relevant load capacity.

| `equipment` | Load Parameter Label | Metric | Matched Capacity Name |
|-------------|----------------------|--------|-----------------------|
| `Crane with outriggers` | Max Outrigger Load | `kN` | `max point load` |
| `Mobile crane` | Max Axle Load | `t` | `max axle load` |
| `Heavy vehicle` | Max Axle Load | `t` | `max axle load` |
| `Elevated Work Platform` | Max Wheel Load | `kN` | `max point load` |
| `Storage Load` | Uniform Distributor Load | `kPa` | `max uniform distributor load` |
| `Vessel` | Displacement | `t` | `max displacement size` |

---

## Health

### GET `/api/v1/health`

Simple server liveness check. No authentication required.

**Response `200`:**

```json
{
  "status": "ok"
}
```

---

## Auth APIs

### POST `/api/v1/auth/login`

Sign in with email and password.

**Request body:**

```json
{
  "email": "admin@demo.com",
  "password": "admin123"
}
```

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "token": "<bearer_token>",
    "user": {
      "id": 1,
      "email": "admin@demo.com",
      "role": "System_Admin"
    }
  }
}
```

**Possible errors:**

| Status | Code | Description |
|--------|------|-------------|
| `400` | `validation_error` | `email` or `password` is missing |
| `401` | `invalid_credentials` | Email not found or password incorrect |

---

### POST `/api/v1/auth/users`

Create a new user account.

**Permissions:** `System_Admin` only.

**Request body:**

```json
{
  "email": "manager2@demo.com",
  "password": "manager456",
  "role": "Asset_Manager"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `email` | string | Yes | Must be unique |
| `password` | string | Yes | |
| `role` | string | Yes | One of `System_Admin`, `Asset_Manager`, `Contractors` |

**Response `201`:**

```json
{
  "success": true,
  "data": {
    "id": 5,
    "email": "manager2@demo.com",
    "role": "Asset_Manager"
  }
}
```

**Possible errors:**

| Status | Code | Description |
|--------|------|-------------|
| `400` | `validation_error` | Required field missing or role value is invalid |
| `403` | — | Caller is not `System_Admin` |
| `409` | `email_exists` | Email address already registered |

---

## Location APIs

### GET `/api/v1/locations/`

Return all shared locations.

**Permissions:** Any authenticated user.

**Response `200`:**

```json
{
  "success": true,
  "data": [
    { "id": 1, "name": "Berth 5" },
    { "id": 2, "name": "Berth 8" }
  ]
}
```

---

### POST `/api/v1/locations/`

Create a new location.

**Permissions:** `System_Admin`, `Asset_Manager`.

**Request body:**

```json
{
  "name": "North Wharf"
}
```

**Response `201`:**

```json
{
  "success": true,
  "data": {
    "id": 3,
    "name": "North Wharf"
  }
}
```

**Possible errors:**

| Status | Code | Description |
|--------|------|-------------|
| `400` | `validation_error` | `name` is missing or blank |
| `403` | — | Caller lacks permission |
| `409` | `location_exists` | Location name already exists |

---

## Asset APIs

### GET `/api/v1/assets/`

List assets for a specific location, including their load capacities.

**Permissions:** Any authenticated user.

**Query parameters:**

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `locationId` | integer | Yes | — | |
| `page` | integer | No | `1` | Must be ≥ 1 |
| `pageSize` | integer | No | `20` | Must be 1–200 |
| `q` | string | No | — | Case-insensitive substring filter on asset name |

**Example request:**

```http
GET /api/v1/assets/?locationId=1&page=1&pageSize=20
Authorization: Bearer <token>
```

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 10,
        "name": "Berth 5 Deck",
        "locationId": 1,
        "loadCapacities": [
          {
            "id": 21,
            "name": "max point load",
            "metric": "kN",
            "maxLoad": 1200.0,
            "details": "outrigger"
          }
        ]
      }
    ],
    "page": 1,
    "pageSize": 20,
    "total": 1,
    "pages": 1
  }
}
```

**Possible errors:**

| Status | Code | Description |
|--------|------|-------------|
| `400` | `validation_error` | `locationId` missing or pagination parameters out of range |
| `404` | `location_not_found` | No location with the given ID |

---

### GET `/api/v1/assets/all`

List all assets across all locations (without load capacities).

**Permissions:** Any authenticated user.

**Query parameters:**

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `page` | integer | No | `1` | Must be ≥ 1 |
| `pageSize` | integer | No | `20` | Must be 1–200 |
| `q` | string | No | — | Case-insensitive substring filter on asset name |

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 10,
        "name": "Berth 5 Deck",
        "locationId": 1
      }
    ],
    "page": 1,
    "pageSize": 20,
    "total": 1,
    "pages": 1
  }
}
```

**Possible errors:**

| Status | Code | Description |
|--------|------|-------------|
| `400` | `validation_error` | Pagination parameters out of range |

---

### POST `/api/v1/assets/`

Create an asset with one or more load capacities.

**Permissions:** `System_Admin`, `Asset_Manager`.

**Request body:**

```json
{
  "locationName": "Berth 5",
  "name": "Imported Deck Asset",
  "loadCapacities": [
    {
      "name": "max point load",
      "metric": "kN",
      "maxLoad": 1200,
      "details": "Max Outrigger Load: 1200 kN"
    },
    {
      "name": "max axle load",
      "metric": "t",
      "maxLoad": 85,
      "details": "Max Axle Load: 85 t"
    }
  ]
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `locationName` | string | Yes | See location-resolution behaviour below |
| `name` | string | Yes | Must be unique within the resolved location |
| `loadCapacities` | array | Yes | At least one entry required |
| `loadCapacities[].name` | string | Yes | See [Load Capacity Names](#load-capacity-names) enum |
| `loadCapacities[].metric` | string | Yes | Must match the required metric for the given name |
| `loadCapacities[].maxLoad` | number | Yes | Must be > 0 |
| `loadCapacities[].details` | string | No | Free-text annotation |

**Location resolution:**

The service attempts to fuzzy-match `locationName` against existing locations (normalised whitespace, punctuation, and casing). If the best-match score reaches the internal threshold, the existing location is reused. Otherwise a new location is created automatically.

**Capacity-metric pairing:**

Each `loadCapacities[].name` is bound to a single allowed metric. Providing a mismatched pair (e.g. `"max point load"` with metric `"t"`) returns a `400 invalid_capacity_metric_pair` error. See the [Enum Reference](#enum-reference) table.

**Duplicate protection:**

- Duplicate `name` values within the same `loadCapacities` array → `409 duplicate_capacity`.
- An asset with the same `(locationId, name)` already exists → `409 asset_already_exists`.

**Response `201`:**

```json
{
  "success": true,
  "data": {
    "id": 11,
    "name": "Imported Deck Asset",
    "locationId": 1,
    "loadCapacities": [
      {
        "id": 31,
        "name": "max point load",
        "metric": "kN",
        "maxLoad": 1200.0,
        "details": "Max Outrigger Load: 1200 kN"
      },
      {
        "id": 32,
        "name": "max axle load",
        "metric": "t",
        "maxLoad": 85.0,
        "details": "Max Axle Load: 85 t"
      }
    ]
  }
}
```

**Possible errors:**

| Status | Code | Description |
|--------|------|-------------|
| `400` | `validation_error` | Required field missing or `maxLoad` is not a positive number |
| `400` | `invalid_metric` | Metric value outside the allowed enum |
| `400` | `invalid_capacity_name` | Capacity name outside the allowed enum |
| `400` | `invalid_capacity_metric_pair` | Metric does not match the required metric for the capacity name |
| `403` | — | Caller lacks permission |
| `409` | `asset_already_exists` | Asset with same name already exists at the resolved location |
| `409` | `duplicate_capacity` | Same capacity name appears more than once in `loadCapacities` |

---

### POST `/api/v1/assets/import-json-uploads`

Batch-import all `*.json` asset-payload files found in the configured AI uploads directory.

**Permissions:** `System_Admin` only.

**Request body (optional):**

```json
{
  "directoryPath": "D:/path/to/gjp-assetguard-extraction-tool/uploads"
}
```

If `directoryPath` is omitted, the server uses the value of `AI_JSON_UPLOADS_DIR` from its configuration (defaults to the `gjp-assetguard-extraction-tool/uploads` folder alongside the server).

**How it works:**

1. Scans the directory for `*.json` files, sorted alphabetically.
2. Parses each file and validates the payload structure.
3. Attempts to create each asset via the same logic as `POST /assets/`.
4. Returns a summary of created and rejected files in one batch response.

**Response `201`** (when at least one asset was created) **or `200`** (when no new assets were created):

```json
{
  "success": true,
  "data": {
    "directory": "D:/path/to/gjp-assetguard-extraction-tool/uploads",
    "filesScanned": 3,
    "createdCount": 1,
    "rejectedCount": 2,
    "items": [
      {
        "file": "01_design_criteria_asset_payload_valid.json",
        "asset": {
          "id": 12,
          "name": "Imported From Uploads A",
          "locationId": 1,
          "loadCapacities": [
            {
              "id": 41,
              "name": "max point load",
              "metric": "kN",
              "maxLoad": 321.0,
              "details": null
            }
          ]
        }
      }
    ],
    "rejected": [
      {
        "file": "02_design_criteria_asset_payload_duplicate.json",
        "reason": "asset_already_exists",
        "message": "Asset with the same location and name already exists",
        "assetName": "Imported From Uploads A"
      },
      {
        "file": "03_misc_invalid.json",
        "reason": "invalid_asset_payload",
        "message": "JSON must contain locationName, name, and loadCapacities[]"
      }
    ]
  }
}
```

**Rejection reasons in `rejected[]`:**

| `reason` | Description |
|----------|-------------|
| `invalid_json` | File is not valid JSON |
| `invalid_payload` | Top-level JSON is not an object |
| `invalid_asset_payload` | Object is missing `locationName`, `name`, or `loadCapacities` |
| `asset_already_exists` | Asset with the same name already exists at the resolved location |
| `invalid_metric` | A metric value in the file is not in the allowed enum |
| `invalid_capacity_name` | A capacity name in the file is not in the allowed enum |
| `invalid_capacity_metric_pair` | Metric does not match the required metric for the capacity name |
| `duplicate_capacity` | Same capacity name appears more than once in `loadCapacities` |
| `validation_error` | Other validation failure (e.g. blank name, non-positive maxLoad) |

**Possible errors:**

| Status | Code | Description |
|--------|------|-------------|
| `400` | `validation_error` | `directoryPath` is required but not provided and no default is configured |
| `403` | — | Caller is not `System_Admin` |
| `404` | `json_uploads_dir_not_found` | The specified directory does not exist |

---

### GET `/api/v1/assets/<asset_id>/load-capacities`

List all load capacities for a single asset.

**Permissions:** `System_Admin`, `Asset_Manager`.

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "asset": {
      "id": 10,
      "name": "Berth 5 Deck",
      "locationId": 1
    },
    "items": [
      {
        "id": 21,
        "name": "max point load",
        "metric": "kN",
        "maxLoad": 1200.0,
        "details": "outrigger"
      }
    ]
  }
}
```

**Possible errors:**

| Status | Code | Description |
|--------|------|-------------|
| `403` | — | Caller lacks permission |
| `404` | `asset_not_found` | No asset with the given ID |

---

### POST `/api/v1/assets/<asset_id>/load-capacities`

Add a new load capacity row to an existing asset.

**Permissions:** `System_Admin`, `Asset_Manager`.

**Request body:**

```json
{
  "name": "max axle load",
  "metric": "t",
  "maxLoad": 80,
  "details": "temp cap"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | See [Load Capacity Names](#load-capacity-names) enum |
| `metric` | string | Yes | Must match the required metric for the given name |
| `maxLoad` | number | Yes | Must be > 0 |
| `details` | string | No | Free-text annotation |

**Response `201`:**

```json
{
  "success": true,
  "data": {
    "asset": {
      "id": 10,
      "name": "Berth 5 Deck",
      "locationId": 1
    },
    "capacity": {
      "id": 42,
      "name": "max axle load",
      "metric": "t",
      "maxLoad": 80.0,
      "details": "temp cap"
    }
  }
}
```

**Possible errors:**

| Status | Code | Description |
|--------|------|-------------|
| `400` | `validation_error` | Required field missing or `maxLoad` is not a positive number |
| `400` | `invalid_metric` | Metric value outside the allowed enum |
| `400` | `invalid_capacity_name` | Capacity name outside the allowed enum |
| `400` | `invalid_capacity_metric_pair` | Metric does not match the required metric for the capacity name |
| `403` | — | Caller lacks permission |
| `404` | `asset_not_found` | No asset with the given ID |
| `409` | `duplicate_capacity` | This capacity name already exists on the asset |

---

### PUT `/api/v1/assets/<asset_id>/load-capacities/<capacity_id>`

Update one or more fields on an existing load capacity row.

**Permissions:** `System_Admin`, `Asset_Manager`.

At least one of `name`, `metric`, `maxLoad`, or `details` must be present in the request body.

**Request body (partial update):**

```json
{
  "maxLoad": 850,
  "details": "updated cap"
}
```

**Updatable fields:**

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | Must be a valid capacity name; metric compatibility is **not** re-validated when only `name` changes |
| `metric` | string | Must be a valid metric value |
| `maxLoad` | number | Must be > 0 |
| `details` | string | Set to `null` or empty to clear |

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "asset": {
      "id": 10,
      "name": "Berth 5 Deck",
      "locationId": 1
    },
    "capacity": {
      "id": 42,
      "name": "max axle load",
      "metric": "t",
      "maxLoad": 850.0,
      "details": "updated cap"
    }
  }
}
```

**Possible errors:**

| Status | Code | Description |
|--------|------|-------------|
| `400` | `validation_error` | No updatable field provided, or `maxLoad` is not a positive number |
| `400` | `invalid_metric` | Metric value outside the allowed enum |
| `400` | `invalid_capacity_name` | Capacity name outside the allowed enum |
| `403` | — | Caller lacks permission |
| `404` | `asset_not_found` | No asset with the given ID |
| `404` | `capacity_not_found` | No load capacity with the given ID on this asset |

---

### DELETE `/api/v1/assets/<asset_id>/load-capacities/<capacity_id>`

Remove a load capacity row from an asset.

**Permissions:** `System_Admin`, `Asset_Manager`.

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "deleted": true
  }
}
```

**Possible errors:**

| Status | Code | Description |
|--------|------|-------------|
| `403` | — | Caller lacks permission |
| `404` | `asset_not_found` | No asset with the given ID |
| `404` | `capacity_not_found` | No load capacity with the given ID on this asset |

---

## Evaluation APIs

### GET `/api/v1/evaluations/equipment-options`

Return the full list of supported equipment types with their expected load parameter label and metric. Use this endpoint to populate form dropdowns dynamically.

**Permissions:** Any authenticated user.

**Response `200`:**

```json
{
  "success": true,
  "data": [
    {
      "equipment": "Crane with outriggers",
      "loadParameterLabel": "Max Outrigger Load",
      "metric": "kN"
    },
    {
      "equipment": "Mobile crane",
      "loadParameterLabel": "Max Axle Load",
      "metric": "t"
    },
    {
      "equipment": "Heavy vehicle",
      "loadParameterLabel": "Max Axle Load",
      "metric": "t"
    },
    {
      "equipment": "Elevated Work Platform",
      "loadParameterLabel": "Max Wheel Load",
      "metric": "kN"
    },
    {
      "equipment": "Storage Load",
      "loadParameterLabel": "Uniform Distributor Load",
      "metric": "kPa"
    },
    {
      "equipment": "Vessel",
      "loadParameterLabel": "Displacement",
      "metric": "t"
    }
  ]
}
```

---

### POST `/api/v1/evaluations/check`

Evaluate whether a proposed load complies with the selected asset's stored capacity. The result is logged and can be retrieved via the history endpoint.

**Permissions:** Any authenticated user.

**Request body:**

```json
{
  "locationId": 1,
  "assetId": 10,
  "equipment": "Crane with outriggers",
  "equipmentModel": "LTM 1100",
  "loadParameterValue": 500,
  "remark": "Pre-lift check"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `locationId` | integer | Yes | Must match the asset's location |
| `assetId` | integer | Yes | |
| `equipment` | string | Yes | Must be a valid equipment type (see [Equipment Types](#equipment-types)) |
| `loadParameterValue` | number | Yes | Must be > 0 |
| `equipmentModel` | string | No | Free-text model/identifier |
| `remark` | string | No | Free-text note saved with the log entry |

**Evaluation logic:**

The service maps the `equipment` string to the required capacity name and metric, then looks up the matching `LoadCapacity` row on the asset. It compares `loadParameterValue` against `maxLoad`:

- If `loadParameterValue ≤ maxLoad` → **`Compliant`**, `overloadPercentage = 0.0`
- If `loadParameterValue > maxLoad` → **`Non-Compliant`**, `overloadPercentage = (value − maxLoad) / maxLoad`

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "asset": {
      "id": 10,
      "name": "Berth 5 Deck",
      "locationId": 1
    },
    "equipment": "Crane with outriggers",
    "equipmentModel": "LTM 1100",
    "loadParameterValue": 500.0,
    "loadParameterMetric": "kN",
    "matchedCapacityName": "max point load",
    "capacityMaxLoad": 1200.0,
    "status": "Compliant",
    "overloadPercentage": 0.0,
    "remark": "Pre-lift check"
  }
}
```

**Response fields:**

| Field | Type | Description |
|-------|------|-------------|
| `asset` | object | Asset summary |
| `equipment` | string | Equipment type used |
| `equipmentModel` | string \| null | Equipment model/identifier |
| `loadParameterValue` | number | Submitted load value |
| `loadParameterMetric` | string | Metric derived from equipment type |
| `matchedCapacityName` | string | The capacity name that was checked |
| `capacityMaxLoad` | number | The stored maximum load |
| `status` | string | `"Compliant"` or `"Non-Compliant"` |
| `overloadPercentage` | number | `0.0` when compliant; ratio of excess over max load otherwise (e.g. `0.25` = 25% over limit) |
| `remark` | string \| null | Remark as saved |

**Possible errors:**

| Status | Code | Description |
|--------|------|-------------|
| `400` | `validation_error` | Required field missing or value is not a valid number |
| `400` | `invalid_load_value` | `loadParameterValue` is zero or negative |
| `400` | `invalid_equipment` | `equipment` is not one of the supported types |
| `400` | `asset_location_mismatch` | The asset does not belong to the supplied `locationId` |
| `400` | `capacity_not_found` | The asset has no capacity row for the equipment's required capacity name |
| `400` | `capacity_metric_mismatch` | Stored capacity metric does not match the equipment's expected metric |
| `404` | `asset_not_found` | No asset with the given ID |

---

### GET `/api/v1/evaluations/history`

List all past evaluation log entries, most recent first.

**Permissions:** `System_Admin`, `Asset_Manager`.

**Query parameters:**

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `page` | integer | No | `1` | Must be ≥ 1 |
| `pageSize` | integer | No | `20` | Must be 1–200 |

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 7,
        "assetId": 10,
        "assetName": "Berth 5 Deck",
        "equipment": "Crane with outriggers",
        "equipmentModel": "LTM 1100",
        "loadParameterValue": 500.0,
        "loadParameterMetric": "kN",
        "matchedCapacityName": "max point load",
        "status": "Compliant",
        "overloadPercentage": 0.0,
        "remark": "Pre-lift check",
        "evaluatedAt": "2026-03-24T12:34:56Z"
      }
    ],
    "page": 1,
    "pageSize": 20,
    "total": 1,
    "pages": 1
  }
}
```

**Possible errors:**

| Status | Code | Description |
|--------|------|-------------|
| `400` | `validation_error` | Pagination parameters out of range |
| `403` | — | Caller is `Contractors` (insufficient permission) |

---

## AI JSON Import Workflow

The AI extraction module (`gjp-assetguard-extraction-tool`) generates one JSON file per detected asset. Each file must conform to this schema:

```json
{
  "locationName": "Berth 5",
  "name": "Berth 5 Deck",
  "loadCapacities": [
    {
      "name": "max point load",
      "metric": "kN",
      "maxLoad": 1200,
      "details": "Max Outrigger Load: 1200 kN"
    },
    {
      "name": "max axle load",
      "metric": "t",
      "maxLoad": 85,
      "details": "Max Axle Load: 85 t"
    }
  ]
}
```

When `POST /api/v1/assets/import-json-uploads` is called:

1. All `*.json` files in the uploads directory are read in alphabetical order.
2. Each file is validated (structure, enum values, metric–name pairing, positive `maxLoad`).
3. Valid files that are not duplicates are imported as new assets.
4. A single batch response is returned with per-file outcomes.

The server's `AI_JSON_UPLOADS_DIR` configuration key sets the default directory. This can be overridden per-request using the `directoryPath` body field.
