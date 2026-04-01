# AssetGuard AI Workspace

This workspace contains **two separate Python projects**:

- `AssetGuard AI/` — the main Flask backend
  - stores locations, assets, load capacities, and evaluation logs
  - imports AI-generated asset JSON into the main database
- `gjp-assetguard-extraction-tool/` — the AI extraction tool
  - converts PDF / image engineering documents into extracted criteria and asset JSON payloads

## Important

These two projects are **independent**.

- Do **not** install both projects into the same virtual environment
- Do **not** run dependency installation from the workspace root
- Create **one venv per subproject**

---

## Project Docs

| Project | README | API Reference |
|---------|--------|---------------|
| Main backend | `AssetGuard AI/README.md` | `AssetGuard AI/API_DOCUMENTATION.md` |
| AI extraction tool | `gjp-assetguard-extraction-tool/README.md` | — |

---

## Git Usage Rules

This workspace contains two subprojects tracked in the same Git repository.

### Basic rules

- Always create a feature branch before making changes
- Do not push directly to `main`
- Keep commits focused and small
- Review `git diff` before committing
- Prefer separate commits when backend and AI-tool changes are unrelated

### Recommended workflow

```bash
git checkout main
git pull origin main
git checkout -b <your-branch-name>
```

After making changes:

```bash
git status
git diff
git add .
git commit -m "feat: short summary"
git push -u origin <your-branch-name>
```

### Virtual environments and generated files

- Do not commit either project's virtual environment (`venv/`)
- Do not commit `.env` files
- Do not commit service-account JSON credentials
- Do not commit AI-generated files under `gjp-assetguard-extraction-tool/uploads/`
- Do not commit local SQLite database files unless explicitly required

### Before opening a Pull Request

- Confirm the correct subproject was changed
- Confirm both projects still use their own virtual environments
- Re-check `.gitignore` if new local-only files were created
- Update the relevant README or API docs when behaviour changes

### Avoid

- Mixing unrelated refactors into one commit
- Renaming project folders casually
- Editing secrets directly into tracked files
- Committing large generated artifacts
- Force-pushing shared branches unless the team explicitly agrees

---

## Quick Start

### Requirements

- Python 3.11+
- `pip`

---

## 1. Main Backend — `AssetGuard AI`

### Set up the virtual environment

**Windows (PowerShell):**

```powershell
cd "D:/{your path}/AssetGuard AI"
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

**macOS / Linux:**

```bash
cd "/path/to/AssetGuard AI"
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

### Environment variables (optional)

Create an `.env` file (or export variables) in the `AssetGuard AI/` folder to override defaults:

```env
# Token signing secret — change in production
SECRET_KEY=your-strong-secret-key

# SQLite (default) or any SQLAlchemy-compatible URI
DATABASE_URL=sqlite:///assetguard.db

# Bearer token lifetime in seconds (default 86400 = 24 h)
TOKEN_EXPIRES_SECONDS=86400

# Directory where the AI tool writes JSON upload files
# Defaults to ../gjp-assetguard-extraction-tool/uploads relative to this project
AI_JSON_UPLOADS_DIR=/path/to/gjp-assetguard-extraction-tool/uploads
```

### Initialise and run

```bash
# Apply database migrations
python -m flask --app assetguard_app.py db upgrade

# Seed demo users and sample assets
python -m flask --app assetguard_app.py seed

# Start the development server
python -m flask --app assetguard_app.py run --port 5000
```

Backend base URL:

```
http://127.0.0.1:5000/api/v1
```

### Demo accounts (created by `seed`)

| Role | Email | Password |
|------|-------|----------|
| `System_Admin` | `admin@demo.com` | `admin123` |
| `Asset_Manager` | `manager@demo.com` | `manager123` |
| `Contractors` | `contractor@demo.com` | `contractor123` |

### Seeded data

The `seed` command creates one location — **Port of Bunbury** — with six assets, each pre-loaded with four load capacity rows:

| Asset | max point load (kN) | max axle load (t) | max UDL (kPa) | max displacement (t) |
|-------|--------------------:|------------------:|--------------:|---------------------:|
| Berth 2 | 1 200 | 90.0 | 42 | 65 000 |
| Berth 3 | 1 500 | 95.0 | 45 | 70 000 |
| Berth 5 | 1 000 | 87.4 | 40 | 68 100 |
| Berth 8 | 2 642 | 87.4 | 40 | 72 000 |
| Berth 9 | 2 200 | 100.0 | 48 | 76 000 |
| Hardstand A | 800 | 70.0 | 35 | 30 000 |

Running `seed` a second time is safe — existing records are updated rather than duplicated.

---

## 2. AI Extraction Tool — `gjp-assetguard-extraction-tool`

### Set up the virtual environment

**Windows (PowerShell):**

```powershell
cd "D:/{your path}/gjp-assetguard-extraction-tool"
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

**macOS / Linux:**

```bash
cd "/path/to/gjp-assetguard-extraction-tool"
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

### Configure `.env`

Create `gjp-assetguard-extraction-tool/.env`:

```env
# Google Cloud service account JSON path (for OCR / GCS workflow)
GOOGLE_APPLICATION_CREDENTIALS=./your-service-account.json

# Google Cloud Storage bucket for OCR
GCP_BUCKET_NAME=your-gcs-bucket-name

# Gemini API key (extraction)
GEMINI_API_KEY=your-gemini-api-key

# Optional — only required when using the GPT extraction flow
OPENAI_API_KEY=your-openai-api-key
```

### Run

```bash
python app.py
```

Typical local URL:

```
http://127.0.0.1:5001
```

---

## Recommended Local Workflow

1. Start `AssetGuard AI` in its own virtual environment.
2. Start `gjp-assetguard-extraction-tool` in its own virtual environment.
3. Use the AI tool to process PDF / image documents and generate asset JSON files into `gjp-assetguard-extraction-tool/uploads/`.
4. Call `POST /api/v1/assets/import-json-uploads` on the main backend to import those files into the database.

---

## Common API Workflow

### 1. Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "admin@demo.com",
  "password": "admin123"
}
```

Use the returned `token` in all subsequent requests:

```http
Authorization: Bearer <token>
Content-Type: application/json
```

### 2. List locations

```http
GET /api/v1/locations/
Authorization: Bearer <token>
```

### 3. Create an asset

```http
POST /api/v1/assets/
Authorization: Bearer <manager_or_admin_token>
Content-Type: application/json

{
  "locationName": "Port of Bunbury",
  "name": "Berth 10",
  "loadCapacities": [
    { "name": "max point load",             "metric": "kN",  "maxLoad": 1000, "details": "per spec" },
    { "name": "max axle load",              "metric": "t",   "maxLoad": 87.4 },
    { "name": "max uniform distributor load","metric": "kPa", "maxLoad": 40   },
    { "name": "max displacement size",      "metric": "t",   "maxLoad": 68100 }
  ]
}
```

Notes:

- `locationName` is fuzzy-matched against existing locations (tolerates spacing, casing, and punctuation differences); if no close match is found a new location is created automatically.
- Duplicate `(location, asset name)` combinations return `409 asset_already_exists`.
- Each capacity name must be paired with its required metric — see the [Enum Reference](#enum-reference) below.

### 4. Import AI-generated JSON files

`System_Admin` only:

```http
POST /api/v1/assets/import-json-uploads
Authorization: Bearer <admin_token>
Content-Type: application/json

{}
```

Optional — override the upload directory:

```json
{
  "directoryPath": "D:/path/to/gjp-assetguard-extraction-tool/uploads"
}
```

### 5. Evaluate a load

```http
POST /api/v1/evaluations/check
Authorization: Bearer <token>
Content-Type: application/json

{
  "locationId": 1,
  "assetId": 1,
  "equipment": "Crane with outriggers",
  "equipmentModel": "LTM 1100-5.2",
  "loadParameterValue": 500,
  "remark": "Pre-lift check"
}
```

### 6. View evaluation history

`System_Admin` or `Asset_Manager` only:

```http
GET /api/v1/evaluations/history?page=1&pageSize=20
Authorization: Bearer <manager_or_admin_token>
```

---

## API Route Reference

### Auth

| Method | Path | Permission |
|--------|------|------------|
| `POST` | `/api/v1/auth/login` | Public |
| `POST` | `/api/v1/auth/change-password` | Any authenticated user |
| `POST` | `/api/v1/auth/users` | `System_Admin` |

### Locations

| Method | Path | Permission |
|--------|------|------------|
| `GET` | `/api/v1/locations/` | Any authenticated user |
| `POST` | `/api/v1/locations/` | `System_Admin`, `Asset_Manager` |

### Assets

| Method | Path | Permission |
|--------|------|------------|
| `GET` | `/api/v1/assets/?locationId=...` | Any authenticated user |
| `GET` | `/api/v1/assets/all` | Any authenticated user |
| `POST` | `/api/v1/assets/` | `System_Admin`, `Asset_Manager` |
| `POST` | `/api/v1/assets/import-json-uploads` | `System_Admin` |
| `GET` | `/api/v1/assets/<id>/load-capacities` | `System_Admin`, `Asset_Manager` |
| `POST` | `/api/v1/assets/<id>/load-capacities` | `System_Admin`, `Asset_Manager` |
| `PUT` | `/api/v1/assets/<id>/load-capacities/<cap_id>` | `System_Admin`, `Asset_Manager` |
| `DELETE` | `/api/v1/assets/<id>/load-capacities/<cap_id>` | `System_Admin`, `Asset_Manager` |

### Evaluations

| Method | Path | Permission |
|--------|------|------------|
| `GET` | `/api/v1/evaluations/equipment-options` | Any authenticated user |
| `POST` | `/api/v1/evaluations/check` | Any authenticated user |
| `GET` | `/api/v1/evaluations/history` | `System_Admin`, `Asset_Manager` |

---

## Enum Reference

### Capacity name → required metric

Each load capacity name is bound to exactly one allowed metric. Mismatching them returns `400 invalid_capacity_metric_pair`.

| Capacity name | Required metric |
|---------------|-----------------|
| `max point load` | `kN` |
| `max axle load` | `t` |
| `max uniform distributor load` | `kPa` |
| `max displacement size` | `t` |

### Equipment types

| `equipment` | Load parameter label | Metric | Matched capacity |
|-------------|----------------------|--------|-----------------|
| `Crane with outriggers` | Max Outrigger Load | `kN` | `max point load` |
| `Mobile crane` | Max Axle Load | `t` | `max axle load` |
| `Heavy vehicle` | Max Axle Load | `t` | `max axle load` |
| `Elevated Work Platform` | Max Wheel Load | `kN` | `max point load` |
| `Storage Load` | Uniform Distributor Load | `kPa` | `max uniform distributor load` |
| `Vessel` | Displacement | `t` | `max displacement size` |

---

## Automated Tests

Run from inside the `AssetGuard AI/` virtual environment:

```bash
python -m unittest tests.test_api_flow -v
```

Expected result:

```
Ran 2 tests in ...s

OK
```

---

## Utility Scripts

### `view_db.py`

Prints the current contents of the SQLite database — tables, locations, assets, load capacities, and asset-location joins.

```bash
python view_db.py
```

The script auto-detects the database at `instance/assetguard.db` or `assetguard.db` relative to the project root.

---

## License

MIT. See `LICENSE`.
