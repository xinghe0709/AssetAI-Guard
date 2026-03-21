# AssetGuard AI (Flask backend)

REST API for asset load compliance checks, multi-tenant by `company_id`, RBAC roles, and signed Bearer tokens (itsdangerous).  
**Load units in the API and database are English only:** `kg`, `ton` (metric ton; aliases `t`, `tons`), `lb` (aliases `lbs`, `pound`, `pounds`).

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
| `app/utils/` | Auth, responses, errors, unit conversion |
| `migrations/` | Alembic revisions |
| `assetguard_app.py` | WSGI entry (`app` for Flask CLI) |
| `LEARNING_GUIDE.md` | Short reading order |

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
- Scope: health, login, create user, create/list asset, evaluate, history, RBAC, validation errors, bulk-import placeholder

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

### 5 — List assets (any logged-in user)

```http
GET {{BASE}}/assets/?page=1&pageSize=20
Authorization: Bearer {{contractor_token}}
```

Expect: `200`, `data.items` array

---

### 6 — Create asset (manager or admin) — **English unit only**

```http
POST {{BASE}}/assets/
Authorization: Bearer {{manager_token}}
Content-Type: application/json

{
  "assetName": "Crane A1",
  "maxLoadCapacity": 10,
  "equipmentType": "Crane",
  "unit": "ton",
  "sourceFile": "manual"
}
```

Expect: `201`, copy `data.id` → `{{asset_id}}`

Invalid unit example (expect `400`, code `invalid_asset_unit`):

```json
{ "assetName": "X", "maxLoadCapacity": 1, "unit": "grams" }
```

---

### 7 — Evaluate load (conversion + remark)

Asset `unit` is `ton`; submit planned load in **kg** (converted internally):

```http
POST {{BASE}}/evaluations/check
Authorization: Bearer {{contractor_token}}
Content-Type: application/json

{
  "assetId": {{asset_id}},
  "plannedLoad": 9500,
  "evaluationUnit": "kg",
  "remark": "Pre-lift check"
}
```

Expect: `200`, `data.status` `Compliant` or `Non-Compliant`

Missing `evaluationUnit` (expect `400`):

```json
{ "assetId": 1, "plannedLoad": 100 }
```

Unsupported unit (expect `400`, `invalid_evaluation_unit`):

```json
{ "assetId": 1, "plannedLoad": 100, "evaluationUnit": "kN" }
```

---

### 8 — Evaluation history

```http
GET {{BASE}}/evaluations/history?page=1&pageSize=20
Authorization: Bearer {{contractor_token}}
```

Expect: `200`, each item includes `plannedLoad`, `submittedPlannedLoad`, `submittedUnit`, `remark`, `evaluatedAt`

---

### 9 — RBAC: contractor must not create assets (expect `403`)

```http
POST {{BASE}}/assets/
Authorization: Bearer {{contractor_token}}
Content-Type: application/json

{
  "assetName": "Should Fail",
  "maxLoadCapacity": 1
}
```

---

### 10 — RBAC: contractor must not create users (expect `403`)

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

### 11 — Bulk import placeholder (expect `501`)

```http
POST {{BASE}}/assets/bulk-import
Authorization: Bearer {{manager_token}}
```

---

### 12 — Validation samples

**12a** Invalid pagination (expect `400`):

```http
GET {{BASE}}/assets/?page=0&pageSize=20
Authorization: Bearer {{contractor_token}}
```

**12b** Login missing fields (expect `400`):

```http
POST {{BASE}}/auth/login
Content-Type: application/json

{ "email": "a@b.com" }
```

**12c** Negative planned load after passing type checks (expect `400`):

```http
POST {{BASE}}/evaluations/check
Authorization: Bearer {{contractor_token}}
Content-Type: application/json

{
  "assetId": {{asset_id}},
  "plannedLoad": -1,
  "evaluationUnit": "kg"
}
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
