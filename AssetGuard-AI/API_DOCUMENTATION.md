# AssetGuard AI — API Documentation

## Overview

AssetGuard AI is a Flask-based REST backend that provides:

- User authentication and role-based access control
- Shared location management
- Asset and load-capacity management
- Engineering load compliance evaluation
- Bulk import of AI-generated asset JSON payloads
- Email alert configuration and delivery logs

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
11. [Alert APIs](#alert-apis)
12. [AI JSON Import Workflow](#ai-json-import-workflow)

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

| Role            | Description                                          |
| --------------- | ---------------------------------------------------- |
| `System_Admin`  | Full access, including user management and AI import |
| `Asset_Manager` | Can create and manage assets and load capacities     |
| `Contractors`   | Read-only access; can run load evaluations           |

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

| Code                        | Meaning                                                    |
| --------------------------- | ---------------------------------------------------------- |
| `200 OK`                    | Successful read or operation without new resource creation |
| `201 Created`               | Successful creation that produced a new record             |
| `400 Bad Request`           | Validation error or business rule violation                |
| `401 Unauthorized`          | Missing or invalid credentials                             |
| `403 Forbidden`             | Insufficient role permissions                              |
| `404 Not Found`             | Resource does not exist                                    |
| `409 Conflict`              | Duplicate resource violation                               |
| `500 Internal Server Error` | Unexpected server failure                                  |

---

## Enum Reference

### Load Capacity Names

Each capacity name is bound to exactly one allowed metric (enforced at creation and update).

| `name`                         | Required `metric` |
| ------------------------------ | ----------------- |
| `max point load`               | `kN`              |
| `max axle load`                | `t`               |
| `max uniform distributor load` | `kPa`             |
| `max displacement size`        | `t`               |

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

| `equipment`              | Load Parameter Label     | Metric | Matched Capacity Name          |
| ------------------------ | ------------------------ | ------ | ------------------------------ |
| `Crane with outriggers`  | Max Outrigger Load       | `kN`   | `max point load`               |
| `Mobile crane`           | Max Axle Load            | `t`    | `max axle load`                |
| `Heavy vehicle`          | Max Axle Load            | `t`    | `max axle load`                |
| `Elevated Work Platform` | Max Wheel Load           | `kN`   | `max point load`               |
| `Storage Load`           | Uniform Distributor Load | `kPa`  | `max uniform distributor load` |
| `Vessel`                 | Displacement             | `t`    | `max displacement size`        |

### Timestamp Format

Timestamps are returned as ISO 8601 strings without microseconds, e.g. `"2026-05-07T14:30:00+08:00"`.

> **Note:** The login endpoint (`POST /auth/login`) returns timestamps in UTC with microseconds (`"2026-05-07T06:30:00.123456+00:00"`). This is a known inconsistency — all other endpoints use local timezone without microseconds.

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
      "role": "System_Admin",
      "isFirstLogin": false,
      "createdAt": "2026-05-06T10:00:00.123456+00:00",
      "updatedAt": "2026-05-07T06:30:00.654321+00:00"
    }
  }
}
```

When `isFirstLogin` is `true`, the client should redirect the user to the initial password-setup screen and call `POST /auth/set-initial-password` before allowing access to the rest of the application.

**Possible errors:**

| Status | Code                  | Description                           |
| ------ | --------------------- | ------------------------------------- |
| `400`  | `validation_error`    | `email` or `password` is missing      |
| `401`  | `invalid_credentials` | Email not found or password incorrect |

---

### POST `/api/v1/auth/set-initial-password`

Set a personal password on the user's first login and clear the `isFirstLogin` flag.

**Permissions:** Any authenticated user whose `isFirstLogin` is `true`.

**Request body:**

```json
{
  "newPassword": "myNewSecurePassword123"
}
```

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "message": "Password set successfully. You can now use your new password."
  }
}
```

**Possible errors:**

| Status | Code               | Description                                                            |
| ------ | ------------------ | ---------------------------------------------------------------------- |
| `400`  | `validation_error` | `newPassword` is missing or blank                                      |
| `400`  | `not_first_login`  | `isFirstLogin` is already `false`; use `/auth/change-password` instead |
| `401`  | `missing_token`    | No Bearer token provided                                               |

---

### POST `/api/v1/auth/change-password`

Change the password of the currently authenticated user.

**Permissions:** Any authenticated user.

**Request body:**

```json
{
  "currentPassword": "admin123",
  "newPassword": "newSecurePassword456"
}
```

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "message": "Password changed successfully"
  }
}
```

**Possible errors:**

| Status | Code                  | Description                                                                 |
| ------ | --------------------- | --------------------------------------------------------------------------- |
| `400`  | `validation_error`    | `currentPassword` or `newPassword` is missing, blank, or new equals current |
| `401`  | `missing_token`       | No Bearer token provided                                                    |
| `401`  | `invalid_credentials` | `currentPassword` does not match the user's actual password                 |

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

**Response `201`:**

```json
{
  "success": true,
  "data": {
    "id": 5,
    "email": "manager2@demo.com",
    "role": "Asset_Manager",
    "isFirstLogin": true,
    "createdAt": "2026-05-07T14:30:00+08:00",
    "updatedAt": "2026-05-07T14:30:00+08:00"
  }
}
```

**Possible errors:**

| Status | Code               | Description                                     |
| ------ | ------------------ | ----------------------------------------------- |
| `400`  | `validation_error` | Required field missing or role value is invalid |
| `403`  | —                  | Caller is not `System_Admin`                    |
| `409`  | `email_exists`     | Email address already registered                |

---

### GET `/api/v1/auth/users`

List all users with pagination.

**Permissions:** `System_Admin` only.

**Query parameters:**

| Parameter  | Type    | Required | Default | Notes         |
| ---------- | ------- | -------- | ------- | ------------- |
| `page`     | integer | No       | `1`     | Must be ≥ 1   |
| `pageSize` | integer | No       | `20`    | Must be 1–200 |

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "email": "admin@demo.com",
        "role": "System_Admin",
        "isFirstLogin": false,
        "createdAt": "2026-05-06T10:00:00+08:00",
        "updatedAt": "2026-05-07T14:30:00+08:00"
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

| Status | Code               | Description                        |
| ------ | ------------------ | ---------------------------------- |
| `400`  | `validation_error` | Pagination parameters out of range |
| `403`  | —                  | Caller is not `System_Admin`       |

---

### PUT `/api/v1/auth/users/<user_id>`

Update a user's email, role, or password.

**Permissions:** `System_Admin` only.

**Request body (partial update):**

```json
{
  "email": "newemail@demo.com",
  "role": "Asset_Manager",
  "password": "newPassword123"
}
```

At least one of `email`, `role`, or `password` must be present. When `password` is provided the user's `isFirstLogin` flag is reset to `true`.

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "id": 5,
    "email": "newemail@demo.com",
    "role": "Asset_Manager",
    "isFirstLogin": true,
    "createdAt": "2026-05-06T08:00:00+08:00",
    "updatedAt": "2026-05-07T14:35:00+08:00"
  }
}
```

**Possible errors:**

| Status | Code               | Description                                           |
| ------ | ------------------ | ----------------------------------------------------- |
| `400`  | `validation_error` | No updatable field provided, or role value is invalid |
| `403`  | —                  | Caller is not `System_Admin`                          |
| `404`  | `user_not_found`   | No user with the given ID                             |
| `409`  | `email_exists`     | Email address already registered                      |

---

### DELETE `/api/v1/auth/users/<user_id>`

Delete a user account. The caller cannot delete their own account.

**Permissions:** `System_Admin` only.

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

| Status | Code                 | Description                                              |
| ------ | -------------------- | -------------------------------------------------------- |
| `400`  | `cannot_delete_self` | Attempted to delete the authenticated user's own account |
| `403`  | —                    | Caller is not `System_Admin`                             |
| `404`  | `user_not_found`     | No user with the given ID                                |

---

## Location APIs

### GET `/api/v1/locations/`

Return all shared locations. Not paginated.

**Permissions:** Any authenticated user.

**Response `200`:**

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Berth 5",
      "createdAt": "2026-05-06T10:00:00+08:00",
      "updatedAt": "2026-05-07T12:00:00+08:00"
    },
    {
      "id": 2,
      "name": "Berth 8",
      "createdAt": "2026-05-06T10:30:00+08:00",
      "updatedAt": "2026-05-06T10:30:00+08:00"
    }
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
    "name": "North Wharf",
    "createdAt": "2026-05-07T14:30:00+08:00",
    "updatedAt": "2026-05-07T14:30:00+08:00"
  }
}
```

**Possible errors:**

| Status | Code               | Description                  |
| ------ | ------------------ | ---------------------------- |
| `400`  | `validation_error` | `name` is missing or blank   |
| `403`  | —                  | Caller lacks permission      |
| `409`  | `location_exists`  | Location name already exists |

---

### PUT `/api/v1/locations/<location_id>`

Rename an existing location.

**Permissions:** `System_Admin`, `Asset_Manager`.

**Request body:**

```json
{
  "name": "South Wharf"
}
```

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "id": 3,
    "name": "South Wharf",
    "createdAt": "2026-05-07T14:30:00+08:00",
    "updatedAt": "2026-05-07T14:35:00+08:00"
  }
}
```

**Possible errors:**

| Status | Code                 | Description                            |
| ------ | -------------------- | -------------------------------------- |
| `400`  | `validation_error`   | `name` is missing or blank             |
| `403`  | —                    | Caller lacks permission                |
| `404`  | `location_not_found` | Location does not exist                |
| `409`  | `location_exists`    | Another location already has this name |

---

### DELETE `/api/v1/locations/<location_id>`

Delete a location. Fails if assets still reference it.

**Permissions:** `System_Admin` only.

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

| Status | Code                  | Description                                          |
| ------ | --------------------- | ---------------------------------------------------- |
| `403`  | —                     | Caller lacks permission                              |
| `404`  | `location_not_found`  | Location does not exist                              |
| `409`  | `location_has_assets` | Cannot delete — assets still reference this location |

---

## Asset APIs

### GET `/api/v1/assets/`

List assets for a specific location, including their load capacities.

**Permissions:** Any authenticated user.

**Query parameters:**

| Parameter    | Type    | Required | Default | Notes                                           |
| ------------ | ------- | -------- | ------- | ----------------------------------------------- |
| `locationId` | integer | Yes      | —       |                                                 |
| `page`       | integer | No       | `1`     | Must be ≥ 1                                     |
| `pageSize`   | integer | No       | `20`    | Must be 1–200                                   |
| `q`          | string  | No       | —       | Case-insensitive substring filter on asset name |

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
        "createdAt": "2026-05-06T10:00:00+08:00",
        "updatedAt": "2026-05-07T12:00:00+08:00",
        "loadCapacities": [
          {
            "id": 21,
            "name": "max point load",
            "metric": "kN",
            "maxLoad": 1200.0,
            "details": "outrigger",
            "createdAt": "2026-05-06T10:00:00+08:00",
            "updatedAt": "2026-05-06T10:00:00+08:00"
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

| Status | Code                 | Description                                                |
| ------ | -------------------- | ---------------------------------------------------------- |
| `400`  | `validation_error`   | `locationId` missing or pagination parameters out of range |
| `404`  | `location_not_found` | No location with the given ID                              |

---

### GET `/api/v1/assets/all`

List all assets across all locations (without load capacities).

**Permissions:** Any authenticated user.

**Query parameters:**

| Parameter  | Type    | Required | Default | Notes                                           |
| ---------- | ------- | -------- | ------- | ----------------------------------------------- |
| `page`     | integer | No       | `1`     | Must be ≥ 1                                     |
| `pageSize` | integer | No       | `20`    | Must be 1–200                                   |
| `q`        | string  | No       | —       | Case-insensitive substring filter on asset name |

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
        "createdAt": "2026-05-06T10:00:00+08:00",
        "updatedAt": "2026-05-07T12:00:00+08:00"
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

| Status | Code               | Description                        |
| ------ | ------------------ | ---------------------------------- |
| `400`  | `validation_error` | Pagination parameters out of range |

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

**Location resolution:**

The service attempts to fuzzy-match `locationName` against existing locations (normalised whitespace, punctuation, and casing). If the best-match score reaches the internal threshold, the existing location is reused. Otherwise a new location is created automatically.

**Capacity-metric pairing:**

Each `loadCapacities[].name` is bound to a single allowed metric. Providing a mismatched pair returns a `400 invalid_capacity_metric_pair` error. See the [Enum Reference](#enum-reference) table.

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
    "createdAt": "2026-05-07T14:30:00+08:00",
    "updatedAt": "2026-05-07T14:30:00+08:00",
    "loadCapacities": [
      {
        "id": 31,
        "name": "max point load",
        "metric": "kN",
        "maxLoad": 1200.0,
        "details": "Max Outrigger Load: 1200 kN",
        "createdAt": "2026-05-07T14:30:00+08:00",
        "updatedAt": "2026-05-07T14:30:00+08:00"
      },
      {
        "id": 32,
        "name": "max axle load",
        "metric": "t",
        "maxLoad": 85.0,
        "details": "Max Axle Load: 85 t",
        "createdAt": "2026-05-07T14:30:00+08:00",
        "updatedAt": "2026-05-07T14:30:00+08:00"
      }
    ]
  }
}
```

**Possible errors:**

| Status | Code                           | Description                                                     |
| ------ | ------------------------------ | --------------------------------------------------------------- |
| `400`  | `validation_error`             | Required field missing or `maxLoad` is not a positive number    |
| `400`  | `invalid_metric`               | Metric value outside the allowed enum                           |
| `400`  | `invalid_capacity_name`        | Capacity name outside the allowed enum                          |
| `400`  | `invalid_capacity_metric_pair` | Metric does not match the required metric for the capacity name |
| `403`  | —                              | Caller lacks permission                                         |
| `409`  | `asset_already_exists`         | Asset with same name already exists at the resolved location    |
| `409`  | `duplicate_capacity`           | Same capacity name appears more than once in `loadCapacities`   |

---

### PUT `/api/v1/assets/<asset_id>`

Update an asset's name and/or location.

**Permissions:** `System_Admin`, `Asset_Manager`.

**Request body (partial update):**

```json
{
  "name": "Renamed Asset",
  "locationName": "North Wharf"
}
```

At least one of `name` or `locationName` must be present. When `locationName` is provided, the same fuzzy-matching and auto-creation logic used by `POST /assets/` applies.

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "id": 11,
    "name": "Renamed Asset",
    "locationId": 3,
    "createdAt": "2026-05-07T14:30:00+08:00",
    "updatedAt": "2026-05-07T14:45:00+08:00",
    "loadCapacities": [
      {
        "id": 31,
        "name": "max point load",
        "metric": "kN",
        "maxLoad": 1200.0,
        "details": null,
        "createdAt": "2026-05-07T14:30:00+08:00",
        "updatedAt": "2026-05-07T14:30:00+08:00"
      }
    ]
  }
}
```

**Possible errors:**

| Status | Code                   | Description                                                      |
| ------ | ---------------------- | ---------------------------------------------------------------- |
| `400`  | `validation_error`     | No updatable field provided or name is blank                     |
| `403`  | —                      | Caller lacks permission                                          |
| `404`  | `asset_not_found`      | No asset with the given ID                                       |
| `409`  | `asset_already_exists` | Asset with the same name already exists at the resolved location |

---

### DELETE `/api/v1/assets/<asset_id>`

Delete an asset and all its associated load capacities and evaluation logs.

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

| Status | Code              | Description                |
| ------ | ----------------- | -------------------------- |
| `403`  | —                 | Caller lacks permission    |
| `404`  | `asset_not_found` | No asset with the given ID |

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
      "locationId": 1,
      "createdAt": "2026-05-06T10:00:00+08:00",
      "updatedAt": "2026-05-07T12:00:00+08:00"
    },
    "items": [
      {
        "id": 21,
        "name": "max point load",
        "metric": "kN",
        "maxLoad": 1200.0,
        "details": "outrigger",
        "createdAt": "2026-05-06T10:00:00+08:00",
        "updatedAt": "2026-05-06T10:00:00+08:00"
      }
    ]
  }
}
```

**Possible errors:**

| Status | Code              | Description                |
| ------ | ----------------- | -------------------------- |
| `403`  | —                 | Caller lacks permission    |
| `404`  | `asset_not_found` | No asset with the given ID |

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

**Response `201`:**

```json
{
  "success": true,
  "data": {
    "asset": {
      "id": 10,
      "name": "Berth 5 Deck",
      "locationId": 1,
      "createdAt": "2026-05-06T10:00:00+08:00",
      "updatedAt": "2026-05-07T14:50:00+08:00"
    },
    "capacity": {
      "id": 42,
      "name": "max axle load",
      "metric": "t",
      "maxLoad": 80.0,
      "details": "temp cap",
      "createdAt": "2026-05-07T14:50:00+08:00",
      "updatedAt": "2026-05-07T14:50:00+08:00"
    }
  }
}
```

**Possible errors:**

| Status | Code                           | Description                                                     |
| ------ | ------------------------------ | --------------------------------------------------------------- |
| `400`  | `validation_error`             | Required field missing or `maxLoad` is not a positive number    |
| `400`  | `invalid_metric`               | Metric value outside the allowed enum                           |
| `400`  | `invalid_capacity_name`        | Capacity name outside the allowed enum                          |
| `400`  | `invalid_capacity_metric_pair` | Metric does not match the required metric for the capacity name |
| `403`  | —                              | Caller lacks permission                                         |
| `404`  | `asset_not_found`              | No asset with the given ID                                      |
| `409`  | `duplicate_capacity`           | This capacity name already exists on the asset                  |

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

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "asset": {
      "id": 10,
      "name": "Berth 5 Deck",
      "locationId": 1,
      "createdAt": "2026-05-06T10:00:00+08:00",
      "updatedAt": "2026-05-07T14:55:00+08:00"
    },
    "capacity": {
      "id": 42,
      "name": "max axle load",
      "metric": "t",
      "maxLoad": 850.0,
      "details": "updated cap",
      "createdAt": "2026-05-07T14:50:00+08:00",
      "updatedAt": "2026-05-07T14:55:00+08:00"
    }
  }
}
```

**Possible errors:**

| Status | Code                    | Description                                                        |
| ------ | ----------------------- | ------------------------------------------------------------------ |
| `400`  | `validation_error`      | No updatable field provided, or `maxLoad` is not a positive number |
| `400`  | `invalid_metric`        | Metric value outside the allowed enum                              |
| `400`  | `invalid_capacity_name` | Capacity name outside the allowed enum                             |
| `403`  | —                       | Caller lacks permission                                            |
| `404`  | `asset_not_found`       | No asset with the given ID                                         |
| `404`  | `capacity_not_found`    | No load capacity with the given ID on this asset                   |

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

| Status | Code                 | Description                                      |
| ------ | -------------------- | ------------------------------------------------ |
| `403`  | —                    | Caller lacks permission                          |
| `404`  | `asset_not_found`    | No asset with the given ID                       |
| `404`  | `capacity_not_found` | No load capacity with the given ID on this asset |

---

## Evaluation APIs

### GET `/api/v1/evaluations/equipment-options`

Return the full list of supported equipment types with their expected load parameter label and metric.

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

Evaluate whether a proposed load complies with the selected asset's stored capacity. The result is logged and can be retrieved via the history endpoint. A log entry is created with `evaluated_at` but the response does NOT include the timestamp.

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

| Field                | Type    | Required | Notes                                                                    |
| -------------------- | ------- | -------- | ------------------------------------------------------------------------ |
| `locationId`         | integer | Yes      | Must match the asset's location                                          |
| `assetId`            | integer | Yes      |                                                                          |
| `equipment`          | string  | Yes      | Must be a valid equipment type (see [Equipment Types](#equipment-types)) |
| `loadParameterValue` | number  | Yes      | Must be > 0                                                              |
| `equipmentModel`     | string  | No       | Free-text model/identifier                                               |
| `remark`             | string  | No       | Free-text note saved with the log entry                                  |

**Evaluation logic:**

The service maps the `equipment` string to the required capacity name and metric, then looks up the matching `LoadCapacity` row on the asset. It compares `loadParameterValue` against `maxLoad`:

- If `loadParameterValue ≤ maxLoad` → **`Compliant`**, `overloadPercentage = 0.0`
- If `loadParameterValue > maxLoad` → **`Non-Compliant`**, `overloadPercentage = (value − maxLoad) / maxLoad`

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "id": 7,
    "emailStatus": null,
    "emailError": null,
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

> **Note:** This endpoint does not return `evaluatedAt`, `createdAt`, or `updatedAt` in the response. Use `GET /evaluations/history` to retrieve logged timestamps. Emails are **not** sent automatically — use `POST /evaluations/<id>/notify` or the UI **Send Email Alert** button to manually send.

**Response fields:**

| Field                 | Type           | Description                                                                                    |
| --------------------- | -------------- | ---------------------------------------------------------------------------------------------- |
| `id`                  | integer        | Evaluation log ID (use with `/evaluations/<id>/notify` to manually send email)                 |
| `emailStatus`         | string \| null | `null` until email is sent; then `"Delivered"` or `"Failed"`                                  |
| `emailError`          | string \| null | SMTP error message if `emailStatus` is `"Failed"`                                             |
| `asset`               | object         | Asset summary (without timestamps)                                                             |
| `equipment`           | string         | Equipment type used                                                                            |
| `equipmentModel`      | string \| null | Equipment model/identifier                                                                     |
| `loadParameterValue`  | number         | Submitted load value                                                                           |
| `loadParameterMetric` | string         | Metric derived from equipment type                                                             |
| `matchedCapacityName` | string         | The capacity name that was checked                                                             |
| `capacityMaxLoad`     | number         | The stored maximum load                                                                        |
| `status`              | string         | `"Compliant"` or `"Non-Compliant"`                                                             |
| `overloadPercentage`  | number         | Raw decimal: `0.0` when compliant; ratio of excess over max load otherwise (e.g. `0.25` = 25%) |
| `remark`              | string \| null | Remark as saved                                                                                |

**Possible errors:**

| Status | Code                       | Description                                                              |
| ------ | -------------------------- | ------------------------------------------------------------------------ |
| `400`  | `validation_error`         | Required field missing or value is not a valid number                    |
| `400`  | `invalid_load_value`       | `loadParameterValue` is zero or negative                                 |
| `400`  | `invalid_equipment`        | `equipment` is not one of the supported types                            |
| `400`  | `asset_location_mismatch`  | The asset does not belong to the supplied `locationId`                   |
| `400`  | `capacity_not_found`       | The asset has no capacity row for the equipment's required capacity name |
| `400`  | `capacity_metric_mismatch` | Stored capacity metric does not match the equipment's expected metric    |
| `404`  | `asset_not_found`          | No asset with the given ID                                               |

---

### GET `/api/v1/evaluations/history`

List all past evaluation log entries, most recent first.

**Permissions:** `System_Admin`, `Asset_Manager`.

**Query parameters:**

| Parameter   | Type    | Required | Default | Notes                                                       |
| ----------- | ------- | -------- | ------- | ----------------------------------------------------------- |
| `page`      | integer | No       | `1`     | Must be ≥ 1                                                 |
| `pageSize`  | integer | No       | `20`    | Must be 1–200                                               |
| `assetId`   | integer | No       | —       | Filter by asset ID                                          |
| `equipment` | string  | No       | —       | Filter by exact equipment type name                         |
| `status`    | string  | No       | —       | Filter by `"Compliant"` or `"Non-Compliant"`                |
| `fromDate`  | string  | No       | —       | Filter records on or after this date (format: `YYYY-MM-DD`) |
| `toDate`    | string  | No       | —       | Filter records before this date (format: `YYYY-MM-DD`)      |

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
        "capacityMaxLoad": 1200.0,
        "capacityMetric": "kN",
        "capacityMaxLoadDisplay": "1200 kN / 500 kN",
        "status": "Compliant",
        "overloadPercentage": 0.0,
        "remark": "Pre-lift check",
        "evaluatedAt": "2026-03-24T12:34:56+08:00"
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

| Status | Code               | Description                                                                      |
| ------ | ------------------ | -------------------------------------------------------------------------------- |
| `400`  | `validation_error` | Pagination parameters out of range, invalid date format, or invalid status value |
| `403`  | —                  | Caller is `Contractors` (insufficient permission)                                |

---

### GET `/api/v1/evaluations/history/user/<user_id>`

List evaluation log entries for a specific user, most recent first. Supports the same filters and pagination as the general history endpoint.

**Permissions:** `System_Admin`, `Asset_Manager`.

**Path parameters:**

| Parameter | Type    | Required | Notes                                            |
| --------- | ------- | -------- | ------------------------------------------------ |
| `user_id` | integer | Yes      | ID of the user whose evaluation logs to retrieve |

**Query parameters:**

| Parameter   | Type    | Required | Default | Notes                                                       |
| ----------- | ------- | -------- | ------- | ----------------------------------------------------------- |
| `page`      | integer | No       | `1`     | Must be ≥ 1                                                 |
| `pageSize`  | integer | No       | `20`    | Must be 1–200                                               |
| `assetId`   | integer | No       | —       | Filter by asset ID                                          |
| `equipment` | string  | No       | —       | Filter by exact equipment type name                         |
| `status`    | string  | No       | —       | Filter by `"Compliant"` or `"Non-Compliant"`                |
| `fromDate`  | string  | No       | —       | Filter records on or after this date (format: `YYYY-MM-DD`) |
| `toDate`    | string  | No       | —       | Filter records before this date (format: `YYYY-MM-DD`)      |

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
        "capacityMaxLoad": 1200.0,
        "capacityMetric": "kN",
        "capacityMaxLoadDisplay": "1200 kN / 500 kN",
        "status": "Compliant",
        "overloadPercentage": 0.0,
        "remark": "Pre-lift check",
        "evaluatedAt": "2026-03-24T12:34:56+08:00"
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

| Status | Code               | Description                                                                      |
| ------ | ------------------ | -------------------------------------------------------------------------------- |
| `400`  | `validation_error` | Pagination parameters out of range, invalid date format, or invalid status value |
| `403`  | —                  | Caller is `Contractors` (insufficient permission)                                |

---

### GET `/api/v1/evaluations/dashboard-summary`

Return aggregated evaluation statistics for the dashboard, including totals, overload stats, equipment breakdown, top assets, and recent evaluations.

**Permissions:** `System_Admin`, `Asset_Manager`.

**Query parameters:**

| Parameter | Type    | Required | Default | Notes                                                            |
| --------- | ------- | -------- | ------- | ---------------------------------------------------------------- |
| `limit`   | integer | No       | `10`    | Maximum 100. Controls `recentEvaluations` and `topAssets` count. |

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "totals": {
      "evaluations": 42,
      "compliant": 35,
      "nonCompliant": 7,
      "complianceRatePercentage": 83.33
    },
    "overloadStats": {
      "averageOverloadPercentage": 12.5,
      "maxOverloadPercentage": 45.0
    },
    "equipmentStats": [
      { "equipment": "Crane with outriggers", "evaluationCount": 20 },
      { "equipment": "Mobile crane", "evaluationCount": 15 }
    ],
    "topAssets": [
      { "assetName": "Berth 5 Deck", "evaluationCount": 12 },
      { "assetName": "Berth 8 Platform", "evaluationCount": 8 }
    ],
    "recentEvaluations": [
      {
        "id": 7,
        "assetName": "Berth 5 Deck",
        "equipment": "Crane with outriggers",
        "status": "Compliant",
        "loadParameterValue": 500.0,
        "loadParameterMetric": "kN",
        "overloadPercentage": 0.0,
        "evaluatedAt": "2026-05-07T14:30:00+08:00"
      }
    ]
  }
}
```

> **Note:** `overloadPercentage` in this endpoint is **already multiplied by 100** (i.e. `25.0` means 25%), unlike `POST /evaluations/check` and `GET /evaluations/history` where it is a raw decimal (`0.25` means 25%). This is a known inconsistency.

**Possible errors:**

| Status | Code               | Description             |
| ------ | ------------------ | ----------------------- |
| `400`  | `validation_error` | Invalid limit value     |
| `403`  | —                  | Caller lacks permission |

---

### POST `/api/v1/evaluations/<id>/notify`

Manually send an email alert for an existing evaluation. Uses the evaluation's stored data (asset, equipment, load values) and the current email template. The delivery result is persisted to the evaluation log's `email_status` and `email_error` columns.

**Permissions:** Any authenticated user.

**Path parameters:**

| Parameter | Type    | Required | Description       |
| --------- | ------- | -------- | ----------------- |
| `id`      | integer | Yes      | Evaluation log ID |

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "emailStatus": "Delivered",
    "emailError": null
  }
}
```

| field         | type           | description                                                  |
| ------------- | -------------- | ------------------------------------------------------------ |
| emailStatus   | string         | `"Delivered"`, `"Failed"`, or `"Skipped"`                   |
| emailError    | string \| null | SMTP error message if `emailStatus` is `"Failed"`           |

**Possible errors:**

| Status | Code              | Description                   |
| ------ | ----------------- | ----------------------------- |
| `404`  | `not_found`       | Evaluation log does not exist |
| `404`  | `asset_not_found` | Associated asset not found    |

---

## Alert APIs

All alert endpoints require **System Admin** or **Asset Manager** role.

Email sending is **manual only**. Users click **Send Email Alert** on the Evaluation page after a Non-Compliant result. The evaluation response includes `emailStatus` and `emailError` fields showing the delivery outcome.

---

### GET `/api/v1/alerts/email-logs`

Return recent email delivery log entries. **Only Non-Compliant evaluations are shown.**

**Permissions:** `System_Admin`, `Asset_Manager`.

**Query parameters:**

| Parameter | Type    | Required | Default | Notes       |
| --------- | ------- | -------- | ------- | ----------- |
| `limit`   | integer | No       | `100`   | Maximum 500 |

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "EV-0001",
        "channel": "Berth 5 Deck",
        "recipient": "contractor@demo.com",
        "status": "Delivered",
        "maxPlanned": "1,200kN / 1,500kN",
        "overCap": "25.0%",
        "sentAt": "May 9, 2026, 06:43 PM"
      }
    ]
  }
}
```

**Response item fields:**

| field       | type   | description                                                     |
| ----------- | ------ | --------------------------------------------------------------- |
| id          | string | Log ID (e.g. `EV-0001`)                                         |
| channel     | string | Asset name                                                      |
| recipient   | string | Recipient email address                                         |
| status      | string | `"Delivered"`, `"Failed"`, `"Pending"`, or `"Skipped"`         |
| maxPlanned  | string | Formatted "max capacity / measured load"                        |
| overCap     | string | Overload percentage                                             |
| sentAt      | string | Formatted local timestamp (e.g. `"May 9, 2026, 06:43 PM"`)     |

---

### GET `/api/v1/alerts/email-preferences`

Return the current email alert configuration.

**Permissions:** `System_Admin`, `Asset_Manager`.

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "escalationThresholdPercent": 20,
    "digestTimeUtc": "09:00",
    "recipientsCsv": "asset.manager@demo.com,safety@demo.com",
    "sendOnNonCompliant": true
  }
}
```

| field                      | type    | description                                                |
| -------------------------- | ------- | ---------------------------------------------------------- |
| escalationThresholdPercent | integer | Overload % threshold for escalation                        |
| digestTimeUtc              | string  | Scheduled digest time (HH:MM UTC)                          |
| recipientsCsv              | string  | Comma-separated default recipients                         |
| sendOnNonCompliant         | boolean | Informational (auto-send is disabled; email is manual only) |

---

### PUT `/api/v1/alerts/email-preferences`

Update email alert configuration. Partial update — only send the fields you want to change.

**Permissions:** `System_Admin`, `Asset_Manager`.

**Request body (any subset):**

```json
{
  "escalationThresholdPercent": 15,
  "sendOnNonCompliant": false
}
```

| field                      | type    | description                             |
| -------------------------- | ------- | --------------------------------------- |
| escalationThresholdPercent | integer | Overload threshold percentage           |
| digestTimeUtc              | string  | HH:MM format                            |
| recipientsCsv              | string  | Comma-separated email addresses         |
| sendOnNonCompliant         | boolean | Informational toggle (does not control auto-send) |

**Response `200`:** Same shape as `GET /alerts/email-preferences`.

---

### GET `/api/v1/alerts/email-template`

Return the current email template stored in the database. Falls back to the built-in default if no template has been saved.

**Permissions:** `System_Admin`, `Asset_Manager`.

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "subject": "[AssetGuard] {status} - {assetName} ({equipment})",
    "body": "Equipment {equipment} ({equipmentModel}) was evaluated against asset {assetName} and found to be {status}.\n\nCapacity: {capacityName} = {capacityMaxLoad} {loadParameterMetric}\nMeasured Load: {loadParameterValue} {loadParameterMetric}\nOverload: {overloadPercent}%\n\nPlease review the evaluation and take corrective action."
  }
}
```

**Available template placeholders:**

| Placeholder            | Source                  | Example value          |
| ---------------------- | ----------------------- | ---------------------- |
| `{status}`             | Evaluation result       | `Non-Compliant`        |
| `{assetName}`          | Asset name              | `Berth 5 Deck`         |
| `{equipment}`          | Equipment type          | `Crane with outriggers`|
| `{equipmentModel}`     | Equipment model/ID      | `LTM 1100`             |
| `{capacityName}`       | Matched capacity        | `max point load`       |
| `{capacityMaxLoad}`    | Max load (formatted)    | `1,200`                |
| `{loadParameterValue}` | Measured load (formatted)| `1,500`               |
| `{loadParameterMetric}`| Load metric             | `kN`                   |
| `{overloadPercent}`    | Overload percentage     | `25.0`                 |

---

### PUT `/api/v1/alerts/email-template`

Save a new email template to the database. Persists across server restarts. Partial update — only send the fields you want to change.

**Permissions:** `System_Admin`, `Asset_Manager`.

**Request body (any subset):**

```json
{
  "subject": "[AssetGuard] {status} - {assetName}",
  "body": "Equipment {equipment} ({equipmentModel}) was evaluated and found {status}."
}
```

**Response `200`:** Same shape as `GET /alerts/email-template`.

---

### POST `/api/v1/alerts/test-email`

Send a test email to the caller's email address using the current template (with placeholder values filled in as test data).

**Permissions:** `System_Admin`, `Asset_Manager`.

No request body required.

**Response `200`:**

```json
{
  "success": true,
  "data": {
    "id": "EV-0042",
    "channel": "Test Asset",
    "recipient": "admin@demo.com",
    "status": "Delivered",
    "maxPlanned": "1,000kN / 500kN",
    "overCap": "0%",
    "sentAt": "May 9, 2026, 06:43 PM"
  }
}
```

---

## AI JSON Import Workflow

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
          "createdAt": "2026-05-07T14:30:00+08:00",
          "updatedAt": "2026-05-07T14:30:00+08:00",
          "loadCapacities": [
            {
              "id": 41,
              "name": "max point load",
              "metric": "kN",
              "maxLoad": 321.0,
              "details": null,
              "createdAt": "2026-05-07T14:30:00+08:00",
              "updatedAt": "2026-05-07T14:30:00+08:00"
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

| `reason`                       | Description                                                      |
| ------------------------------ | ---------------------------------------------------------------- |
| `invalid_json`                 | File is not valid JSON                                           |
| `invalid_payload`              | Top-level JSON is not an object                                  |
| `invalid_asset_payload`        | Object is missing `locationName`, `name`, or `loadCapacities`    |
| `asset_already_exists`         | Asset with the same name already exists at the resolved location |
| `invalid_metric`               | A metric value in the file is not in the allowed enum            |
| `invalid_capacity_name`        | A capacity name in the file is not in the allowed enum           |
| `invalid_capacity_metric_pair` | Metric does not match the required metric for the capacity name  |
| `duplicate_capacity`           | Same capacity name appears more than once in `loadCapacities`    |
| `validation_error`             | Other validation failure (e.g. blank name, non-positive maxLoad) |

**Possible errors:**

| Status | Code                         | Description                                                               |
| ------ | ---------------------------- | ------------------------------------------------------------------------- |
| `400`  | `validation_error`           | `directoryPath` is required but not provided and no default is configured |
| `403`  | —                            | Caller is not `System_Admin`                                              |
| `404`  | `json_uploads_dir_not_found` | The specified directory does not exist                                    |

---

Each imported JSON file must conform to this schema:

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

## Known Inconsistencies

| Issue                              | Detail                                                                                                                                                                                      |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Login timestamp format**         | `POST /auth/login` returns timestamps in UTC with microseconds (`.isoformat()`). All other endpoints strip microseconds and use local timezone (`_iso()`).                                  |
| **Missing `evaluatedAt` on check** | `POST /evaluations/check` stores `evaluated_at` in the database but does not return it in the response. Use `GET /evaluations/history` to get timestamps.                                   |
| **`overloadPercentage` scale**     | `POST /evaluations/check` and `GET /evaluations/history` return raw decimal (e.g. `0.25`). `GET /evaluations/dashboard-summary` returns percentage already multiplied by 100 (e.g. `25.0`). |
| **Locations not paginated**        | `GET /locations/` returns a flat array without pagination.                                                                                                                                  |
