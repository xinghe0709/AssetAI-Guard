# AssetGuard AI (Flask backend)

REST API for asset load compliance checks aligned with the customer **GJP** data model: **Location → Asset → Load capacity** rows, plus evaluations keyed by **equipment type** (six PDF options) and **load parameter** (`kN` / `t` / `kPa` per mapping). Multi-tenant by `company_id`, RBAC roles, and signed Bearer tokens (itsdangerous).

Stack: **Flask**, **Flask-SQLAlchemy**, **Flask-Migrate** (Alembic).  
`bulk-import` and async email are intentionally not implemented (placeholders).

---

## Prerequisites

- **Python 3.11+** (3.12 recommended)
- `pip` (bundled with Python on Windows/macOS installers)

Verify:

```bash
python --version
python -m pip --version
```

---

## Project layout

| Path | Role |
|------|------|
| `app/controllers/` | HTTP routes (Blueprints) |
| `app/services/` | Business logic |
| `app/models/` | SQLAlchemy models |
| `app/utils/` | Auth, responses, errors, equipment mapping (PDF) |
| `migrations/` | Alembic revisions |
| `assetguard_app.py` | WSGI entry (`app` for Flask CLI) |
| `LEARNING_GUIDE.md` | Short reading order |

---

## Get the project with Git

If the project is not on your machine yet, clone it first:

```bash
git clone https://github.com/xinghe0709/AssetAI-Guard.git
cd AssetAI-Guard
```

Check remotes:

```bash
git remote -v
```

---

## Git workflow and branch rules

> Team policy: **do not push directly to `main`**.  
> Always push to your own branch and open a Pull Request.

### 1) Update local `main`

```bash
git checkout main
git pull origin main
```

### 2) Create your working branch

```bash
git checkout -b <yourname>
```

Example:

```bash
git checkout -b xinghe
```

### 3) Commit changes

```bash
git status
git add .
git commit -m "feat: add bulk import integration skeleton"
```

### 4) Push your branch

```bash
git push -u origin <yourname>
```

### 5) Create Pull Request

- Base branch: `main`
- Compare branch: your feature branch
- Add reviewers and merge only after review/checks pass

### Common Git commands for daily work

```bash
# Show current status
git status

# List local and remote branches
git branch
git branch -r

# Switch branch
git checkout <branch-name>

# Fetch latest remote refs without merging
git fetch origin

# Rebase your branch on latest main (optional)
git checkout <your-branch>
git fetch origin
git rebase origin/main

# View concise history
git log --oneline --graph --decorate -20
```

---

## Database schema overview

Core tables (plus `alembic_version`):

### 1) `companies`

- Tenant root record.
- Key columns:
  - `id` (PK)
  - `name` (unique)
- Purpose: multi-tenant boundary for users, locations, and assets.

### 2) `users`

- Login subjects with RBAC role.
- Key columns:
  - `id` (PK)
  - `email` (unique, indexed)
  - `password_hash`
  - `role` (`System_Admin` / `Asset_Manager` / `Contractors`)
  - `company_id` (FK -> `companies.id`, indexed)
- Purpose: authentication, authorization, and tenant scoping.

### 3) `locations`

- Named site / area under a tenant (e.g. port).
- Key columns:
  - `id` (PK)
  - `company_id` (FK -> `companies.id`, indexed)
  - `name` (unique per company)
- Purpose: groups assets (berths, pads, etc.).

### 4) `assets`

- Asset row under a location (name only at asset level).
- Key columns:
  - `id` (PK)
  - `company_id` (FK -> `companies.id`, indexed)
  - `location_id` (FK -> `locations.id`, indexed)
  - `name`
- Purpose: identity of the structure being evaluated; capacities live in child rows.

### 5) `load_capacities`

- Named limits for an asset (PDF “load capacity” lines).
- Key columns:
  - `id` (PK)
  - `asset_id` (FK -> `assets.id`, indexed)
  - `name` (e.g. `max point load`, `max wheel load`)
  - `metric` (`kN`, `t`, or `kPa`)
  - `max_load` (float, > 0)
  - `details` (optional text)
- Purpose: thresholds matched by equipment → capacity name mapping during evaluation.

### 6) `evaluation_logs`

- Audit trail for each check.
- Key columns:
  - `id` (PK)
  - `asset_id`, `user_id` (FKs, indexed)
  - `equipment` (one of the six PDF equipment strings)
  - `equipment_model` (optional)
  - `load_parameter_value`, `load_parameter_metric` (from mapping + user input)
  - `matched_capacity_name` (which `load_capacities.name` was used)
  - `status` (`Compliant` / `Non-Compliant`)
  - `overload_percentage`
  - `remark` (optional)
  - `evaluated_at` (UTC, indexed)

### 7) `alembic_version`

- Migration bookkeeping (Alembic).

### Relationships summary

- `companies (1) -> (N) users`
- `companies (1) -> (N) locations`
- `locations (1) -> (N) assets`
- `companies (1) -> (N) assets` (tenant FK on asset)
- `assets (1) -> (N) load_capacities`
- `users (1) -> (N) evaluation_logs`
- `assets (1) -> (N) evaluation_logs`

### Migration note (upgrade from older revisions)

Revision `e1f2a3b4c5d6_gjp_pdf_schema_locations_capacities` **drops and recreates** legacy `assets` and `evaluation_logs` to match the GJP model. **Back up** or accept data loss on those tables before `flask db upgrade` on an existing database.

### Tenant isolation model

- Every asset query/write is scoped by `company_id`.
- Auth token payload includes `company_id`, and controllers pass it into services.
- This prevents cross-tenant reads/writes in normal API flows.

---

## Run on **Windows** (PowerShell)

### 1) Open a terminal in the project root

Example: `D:\path\to\AssetGuard AI group11`

### 2) Create and activate a virtual environment (first time only)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If script execution is blocked:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate again.

### 3) Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4) Apply database migrations

Creates/updates tables. With the default SQLite URL, the file is usually under `instance/assetguard.db` (Flask instance folder).

```powershell
python -m flask --app assetguard_app.py db upgrade
```

### 5) Pre-fill demo users (seed)

```powershell
python -m flask --app assetguard_app.py seed
```

Default accounts (printed in the terminal):

| Role | Email | Password |
|------|-------|----------|
| System_Admin | `admin@demo.com` | `admin123` |
| Asset_Manager | `manager@demo.com` | `manager123` |
| Contractors | `contractor@demo.com` | `contractor123` |

### 6) Start the server

```powershell
python -m flask --app assetguard_app.py run --port 5000
```

Health check: **GET** `http://127.0.0.1:5000/api/v1/health` → `{"status":"ok"}`

---

## Run on **macOS** (Terminal / zsh)

### 1) `cd` to the project root

```bash
cd "/path/to/AssetGuard AI group11"
```

### 2) Create and activate venv (first time only)

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3) Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4) Migrate and seed

```bash
python -m flask --app assetguard_app.py db upgrade
python -m flask --app assetguard_app.py seed
```

### 5) Run

```bash
python -m flask --app assetguard_app.py run --port 5000
```

---

## First-time database setup (if you clone without migrations applied)

If this repo already contains `migrations/versions/*.py`, you normally only need:

```bash
python -m flask --app assetguard_app.py db upgrade
python -m flask --app assetguard_app.py seed
```

Only run `db init` / `db migrate` when you are **authoring new migrations** from scratch (not typical for this template).

---

## Environment variables (optional)

| Variable | Purpose | Default |
|----------|---------|---------|
| `DATABASE_URL` | SQLAlchemy URI | `sqlite:///assetguard.db` (often resolved under `instance/`) |
| `SECRET_KEY` | Token signing secret | `dev-secret-change-me` (**change in production**) |
| `TOKEN_EXPIRES_SECONDS` | Bearer token TTL | `86400` |

---

## API base URL

All JSON APIs (except health) are under:

`http://127.0.0.1:5000/api/v1`

Set header for protected routes:

```http
Authorization: Bearer <token_from_login>
Content-Type: application/json
```

---

## Automated API tests

The repo includes an end-to-end automated API flow test:

- Test file: `tests/test_api_flow.py`
- Framework: Python built-in `unittest` + Flask `test_client`
- Scope: health, login, create user, list locations, list assets by `locationId`, equipment options, evaluate (`equipment` + `loadParameterValue`), history, RBAC, validation errors, bulk-import placeholder

### Run on Windows (PowerShell)

```powershell
.\venv\Scripts\Activate.ps1
python -m unittest tests.test_api_flow -v
```

### Run on macOS (zsh/bash)

```bash
source venv/bin/activate
python -m unittest tests.test_api_flow -v
```

Expected result:

- `Ran 1 test ...`
- `OK`

Notes:

- This test does **not** require starting `flask run`; it uses Flask's in-process test client.
- The test creates an isolated temporary SQLite database and runs `seed` automatically.
- Keep the manual Postman suite below for deployment smoke tests and real network validation.

---

## Full manual test suite (copy into Postman / curl)

Replace `BASE` and tokens as needed:

```http
BASE=http://127.0.0.1:5000/api/v1
```

### 0 — Health (no auth)

```http
GET {{BASE}}/health
```

Expect: `200`, body `{"status":"ok"}`

---

### 1 — Login as admin

```http
POST {{BASE}}/auth/login
Content-Type: application/json

{
  "email": "admin@demo.com",
  "password": "admin123"
}
```

Expect: `200`, copy `data.token` → `{{admin_token}}`

---

### 2 — Login as manager

```http
POST {{BASE}}/auth/login
Content-Type: application/json

{
  "email": "manager@demo.com",
  "password": "manager123"
}
```

Expect: `200` → `{{manager_token}}`

---

### 3 — Login as contractor

```http
POST {{BASE}}/auth/login
Content-Type: application/json

{
  "email": "contractor@demo.com",
  "password": "contractor123"
}
```

Expect: `200` → `{{contractor_token}}`

---

### 4 — Create user (admin only)

```http
POST {{BASE}}/auth/users
Authorization: Bearer {{admin_token}}
Content-Type: application/json

{
  "email": "contractor2@demo.com",
  "password": "contractor456",
  "role": "Contractors"
}
```

Expect: `201`

---

### 5 — List locations (any logged-in user)

```http
GET {{BASE}}/locations/
Authorization: Bearer {{contractor_token}}
```

Expect: `200`, `data` is an array; copy first `id` → `{{location_id}}` (seed includes **Port of Bunbury**).

---

### 6 — Create location (manager or admin)

```http
POST {{BASE}}/locations/
Authorization: Bearer {{manager_token}}
Content-Type: application/json

{
  "name": "Another site"
}
```

Expect: `201`, body includes new location `id`.

---

### 7 — List assets (any logged-in user; `locationId` required)

```http
GET {{BASE}}/assets/?locationId={{location_id}}&page=1&pageSize=20
Authorization: Bearer {{contractor_token}}
```

Expect: `200`, `data.items` array; each item has `name`, `loadCapacities`, etc. Seed includes **Berth 5** / **Berth 8** under the demo location.

---

### 8 — Equipment options (for UI / mapping)

```http
GET {{BASE}}/evaluations/equipment-options
Authorization: Bearer {{contractor_token}}
```

Expect: `200`, `data` array with the six PDF equipment labels and parameter metadata.

---

### 9 — Create asset (manager or admin)

```http
POST {{BASE}}/assets/
Authorization: Bearer {{manager_token}}
Content-Type: application/json

{
  "locationId": {{location_id}},
  "name": "Berth 9",
  "loadCapacities": [
    { "name": "max point load", "metric": "kN", "maxLoad": 1000, "details": "per spec" }
  ]
}
```

Expect: `201`, copy `data.id` → `{{asset_id}}`

Invalid capacity `metric` (expect `400`, code `invalid_metric`):

```json
{
  "locationId": 1,
  "name": "X",
  "loadCapacities": [{ "name": "max point load", "metric": "grams", "maxLoad": 1 }]
}
```

---

### 10 — Evaluate load (equipment + parameter value)

Use an `equipment` string exactly as returned by **equipment-options**. Example with seed **Berth 5** capacities:

```http
POST {{BASE}}/evaluations/check
Authorization: Bearer {{contractor_token}}
Content-Type: application/json

{
  "assetId": {{asset_id}},
  "equipment": "Crane with outriggers",
  "equipmentModel": "Mobile crane 50t",
  "loadParameterValue": 500,
  "remark": "Pre-lift check"
}
```

Expect: `200`, `data.status` `Compliant` or `Non-Compliant`, plus `loadParameterMetric`, `matchedCapacityName`, etc.

Missing `loadParameterValue` (expect `400`):

```json
{ "assetId": 1, "equipment": "Crane with outriggers" }
```

Unknown `equipment` (expect `400`, `invalid_equipment`):

```json
{ "assetId": 1, "equipment": "Not a real equipment", "loadParameterValue": 100 }
```

---

### 11 — Evaluation history

```http
GET {{BASE}}/evaluations/history?page=1&pageSize=20
Authorization: Bearer {{contractor_token}}
```

Expect: `200`, each item includes `equipment`, `loadParameterValue`, `loadParameterMetric`, `matchedCapacityName`, `status`, `remark`, `evaluatedAt`.

---

### 12 — RBAC: contractor must not create assets (expect `403`)

```http
POST {{BASE}}/assets/
Authorization: Bearer {{contractor_token}}
Content-Type: application/json

{
  "locationId": {{location_id}},
  "name": "Should Fail",
  "loadCapacities": [{ "name": "max point load", "metric": "kN", "maxLoad": 1 }]
}
```

---

### 13 — RBAC: contractor must not create users (expect `403`)

```http
POST {{BASE}}/auth/users
Authorization: Bearer {{contractor_token}}
Content-Type: application/json

{
  "email": "x@demo.com",
  "password": "123456",
  "role": "Contractors"
}
```

---

### 14 — Bulk import placeholder (expect `501`)

```http
POST {{BASE}}/assets/bulk-import
Authorization: Bearer {{manager_token}}
```

---

### 15 — Validation samples

**15a** List assets without `locationId` (expect `400`):

```http
GET {{BASE}}/assets/?page=1&pageSize=20
Authorization: Bearer {{contractor_token}}
```

**15b** Invalid pagination (expect `400`):

```http
GET {{BASE}}/assets/?locationId={{location_id}}&page=0&pageSize=20
Authorization: Bearer {{contractor_token}}
```

**15c** Login missing fields (expect `400`):

```http
POST {{BASE}}/auth/login
Content-Type: application/json

{ "email": "a@b.com" }
```

---

## Resetting the local SQLite database

Stop the app, delete the SQLite file (often `instance/assetguard.db`), then:

```bash
python -m flask --app assetguard_app.py db upgrade
python -m flask --app assetguard_app.py seed
```

---

## License

MIT — see [LICENSE](LICENSE).
