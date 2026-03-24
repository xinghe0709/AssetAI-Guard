# AssetGuard AI API Documentation

## Overview

AssetGuard AI is a Flask-based backend for:

- user authentication and role-based access control
- shared location management
- asset and load-capacity management
- engineering load evaluation
- importing AI-generated asset JSON payloads into the database

Base path for all application APIs:

```text
/api/v1
```

Health check endpoint:

```text
/api/v1/health
```

## Authentication

The API uses Bearer token authentication.

1. Call `POST /api/v1/auth/login`
2. Copy the returned `token`
3. Send it in the `Authorization` header:

```http
Authorization: Bearer <token>
```

## Roles

Supported roles:

- `System_Admin`
- `Asset_Manager`
- `Contractors`

## Standard Response Format

Successful responses use this envelope:

```json
{
  "success": true,
  "data": {}
}
```

Some successful responses may also include a `message`:

```json
{
  "success": true,
  "message": "Operation completed",
  "data": {}
}
```

Error responses use this envelope:

```json
{
  "success": false,
  "message": "Human readable error message",
  "code": "machine_readable_error_code"
}
```

Some error responses may also include `details`.

## Common HTTP Status Codes

- `200 OK` for successful reads or successful operations without new resource creation
- `201 Created` for successful creation/import that produced new records
- `400 Bad Request` for validation errors
- `401 Unauthorized` for missing or invalid credentials
- `403 Forbidden` for insufficient permissions
- `404 Not Found` for missing resources
- `409 Conflict` for duplicate resources
- `500 Internal Server Error` for unexpected failures

## Health

### GET `/health`

Simple server health check.

Response:

```json
{
  "status": "ok"
}
```

## Auth APIs

### POST `/auth/login`

Sign in using email and password.

Request body:

```json
{
  "email": "admin@demo.com",
  "password": "admin123"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "token": "<bearer_token>",
    "user": {
      "id": 1,
      "email": "admin@demo.com",
      "role": "System_Admin",
      "companyId": 1
    }
  }
}
```

Possible errors:

- `400 validation_error` if email or password is missing
- `401 invalid_credentials` if login fails

### POST `/auth/users`

Create a user in the current tenant. `System_Admin` only.

Request body:

```json
{
  "email": "manager2@demo.com",
  "password": "manager456",
  "role": "Asset_Manager"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "id": 5,
    "email": "manager2@demo.com",
    "role": "Asset_Manager",
    "companyId": 1
  }
}
```

Possible errors:

- `400 validation_error` if required fields are missing or role is invalid
- `403` if caller is not `System_Admin`
- `409 email_exists` if the email already exists

## Location APIs

### GET `/locations/`

List all shared locations.

Authentication:

- any authenticated user

Response:

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Berth 5"
    },
    {
      "id": 2,
      "name": "Berth 8"
    }
  ]
}
```

### POST `/locations/`

Create a new location.

Permissions:

- `System_Admin`
- `Asset_Manager`

Request body:

```json
{
  "name": "North Wharf"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "id": 3,
    "name": "North Wharf"
  }
}
```

Possible errors:

- `400 validation_error` if `name` is missing
- `403` if caller lacks permission
- `409 location_exists` if the location name already exists

## Asset APIs

### GET `/assets/`

List assets for a specific location in the current tenant.

Query parameters:

- `locationId` required integer
- `page` optional integer, default `1`
- `pageSize` optional integer, default `20`, max `200`
- `q` optional asset name search string

Example:

```http
GET /api/v1/assets/?locationId=1&page=1&pageSize=20
Authorization: Bearer <token>
```

Response:

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

Possible errors:

- `400 validation_error` if `locationId` is missing or pagination is invalid
- `404 location_not_found` if the location does not exist

### GET `/assets/all`

List all assets visible to the current company.

Query parameters:

- `page` optional integer, default `1`
- `pageSize` optional integer, default `20`, max `200`
- `q` optional asset name search string

Response:

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

### POST `/assets/`

Create an asset with load capacities.

Permissions:

- `System_Admin`
- `Asset_Manager`

Request body:

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

Location behavior:

- the service tries to match `locationName` against existing location names
- small differences such as spacing, punctuation, or casing may still resolve to an existing location
- if no sufficiently close match is found, a new location is created automatically

Duplicate protection:

- if an asset with the same `company_id + location_id + name` already exists, the API returns `409 conflict`

Allowed `loadCapacities[].name` values:

- `max point load`
- `max axle load`
- `max uniform distributor load`
- `max displacement size`

Allowed `loadCapacities[].metric` values:

- `kN`
- `t`
- `kPa`

Response:

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
      }
    ]
  }
}
```

Possible errors:

- `400 validation_error` if required fields are missing
- `400 invalid_metric` if a metric is outside the enum
- `400 invalid_capacity_name` if a capacity name is outside the enum
- `403` if caller lacks permission
- `409 asset_already_exists` if the same asset already exists in the same company and location

### POST `/assets/import-json-uploads`

Import every JSON asset payload found in the configured AI uploads directory.

Permissions:

- `System_Admin` only

Purpose:

- reads JSON files exported by the AI extraction module
- validates each file
- creates assets one by one
- returns created and rejected items in one batch response

Request body:

```json
{}
```

Optional request body with explicit directory:

```json
{
  "directoryPath": "D:/path/to/gjp-assetguard-extraction-tool/uploads"
}
```

Default directory:

- configured by `AI_JSON_UPLOADS_DIR`
- by default points to `gjp-assetguard-extraction-tool/uploads`

Response:

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
        "message": "Asset with the same company, location, and name already exists",
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

Status code behavior:

- `201` if at least one asset was created
- `200` if no new assets were created but the request itself completed

Possible errors:

- `400 validation_error` if `directoryPath` is invalid or missing when required
- `403` if caller is not `System_Admin`
- `404 json_uploads_dir_not_found` if the directory does not exist

### GET `/assets/<asset_id>/load-capacities`

List all load capacities for a single asset.

Permissions:

- `System_Admin`
- `Asset_Manager`

Response:

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

Possible errors:

- `403` if caller lacks permission
- `404 asset_not_found` if the asset does not belong to the caller's company

### POST `/assets/<asset_id>/load-capacities`

Create a new load capacity row for an asset.

Permissions:

- `System_Admin`
- `Asset_Manager`

Request body:

```json
{
  "name": "max point load",
  "metric": "kN",
  "maxLoad": 800,
  "details": "temporary cap"
}
```

Response:

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
      "name": "max point load",
      "metric": "kN",
      "maxLoad": 800.0,
      "details": "temporary cap"
    }
  }
}
```

### PUT `/assets/<asset_id>/load-capacities/<capacity_id>`

Update one or more fields on a load capacity row.

Permissions:

- `System_Admin`
- `Asset_Manager`

Allowed update fields:

- `name`
- `metric`
- `maxLoad`
- `details`

Request body example:

```json
{
  "maxLoad": 850,
  "details": "updated"
}
```

Response:

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
      "name": "max point load",
      "metric": "kN",
      "maxLoad": 850.0,
      "details": "updated"
    }
  }
}
```

### DELETE `/assets/<asset_id>/load-capacities/<capacity_id>`

Delete one load capacity row from an asset.

Permissions:

- `System_Admin`
- `Asset_Manager`

Response:

```json
{
  "success": true,
  "data": {
    "deleted": true
  }
}
```

## Evaluation APIs

### GET `/evaluations/equipment-options`

Return the supported equipment list with the expected load parameter label and metric.

Authentication:

- any authenticated user

Response:

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
      "equipment": "Storage Load",
      "loadParameterLabel": "Uniform Distributor Load",
      "metric": "kPa"
    }
  ]
}
```

### POST `/evaluations/check`

Evaluate whether a user-supplied load complies with the selected asset's stored capacity.

Authentication:

- any authenticated user

Request body:

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

Response:

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

Possible errors:

- `400 validation_error` for missing fields or bad numeric values
- `400 invalid_load_value` if the value is zero or negative
- `400 asset_location_mismatch` if the asset is not in the given location
- `400 capacity_not_found` if the asset does not have the required capacity row
- `400 capacity_metric_mismatch` if stored metric conflicts with the selected equipment type
- `404 asset_not_found` if the asset does not belong to the current company

### GET `/evaluations/history`

List evaluation history for the current company.

Permissions:

- `System_Admin`
- `Asset_Manager`

Query parameters:

- `page` optional integer, default `1`
- `pageSize` optional integer, default `20`, max `200`

Response:

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

Possible errors:

- `400 validation_error` if pagination is invalid
- `403` if caller lacks permission

## Notes for AI JSON Import Workflow

The AI extraction module is expected to generate JSON files in this shape:

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
    }
  ]
}
```

The main server will:

- validate enum values for `name` and `metric`
- resolve or create a location using `locationName`
- reject duplicate assets in the same company and location

## Current Enum Constraints

Load capacity names:

- `max point load`
- `max axle load`
- `max uniform distributor load`
- `max displacement size`

Load metrics:

- `kN`
- `t`
- `kPa`

User roles:

- `System_Admin`
- `Asset_Manager`
- `Contractors`
