# AssetGuard AI Workspace

This workspace contains **two separate Python projects**:

- `AssetGuard AI/`
  - the main Flask backend
  - stores locations, assets, load capacities, and evaluation logs
  - imports AI-generated asset JSON into the main database
- `gjp-assetguard-extraction-tool/`
  - the AI extraction tool
  - converts PDF/image engineering documents into extracted criteria and asset JSON payloads

## Important

These two projects are **independent**.

- Do **not** install both projects into the same virtual environment
- Do **not** run dependency installation from the workspace root
- Create **one venv per subproject**

## Project docs

### Main backend

- `AssetGuard AI/README.md`
- `AssetGuard AI/API_DOCUMENTATION.md`
-

### AI extraction tool

- `gjp-assetguard-extraction-tool/README.md`

## Git Usage Rules

This workspace contains two subprojects, but they are tracked in the same Git repository.

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

- Do not commit either project's virtual environment
- Do not commit `.env` files
- Do not commit service-account JSON credentials
- Do not commit AI-generated files under `gjp-assetguard-extraction-tool/uploads/`
- Do not commit local SQLite database files unless explicitly required

### Before opening a Pull Request

- Make sure the correct subproject was changed
- Make sure both projects still use their own virtual environments
- Re-check `.gitignore` if new local-only files were created
- Update the relevant README or API docs when behavior changes

### Avoid

- Mixing unrelated refactors into one commit
- Renaming project folders casually
- Editing secrets directly into tracked files
- Committing large generated artifacts
- Force-pushing shared branches unless the team explicitly agrees

## Quick Start

### Requirements

- Python 3.11+
- `pip`

## Virtual Environments

### 1. Main backend: `AssetGuard AI`

Create the virtual environment inside `AssetGuard AI/`.

Windows:

```powershell
cd "D:/{your path}/AssetGuard AI group11/AssetGuard AI"
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS / Linux:

```bash
cd "/path/to/AssetGuard AI group11/AssetGuard AI"
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

Run the backend:

```bash
python -m flask --app assetguard_app.py db upgrade
python -m flask --app assetguard_app.py seed
python -m flask --app assetguard_app.py run --port 5000
```

Backend base URL:

```text
http://127.0.0.1:5000/api/v1
```

Demo users:

| Role | Email | Password |
|------|-------|----------|
| System_Admin | `admin@demo.com` | `admin123` |
| Asset_Manager | `manager@demo.com` | `manager123` |
| Contractors | `contractor@demo.com` | `contractor123` |

### 2. AI extraction tool: `gjp-assetguard-extraction-tool`

Create a different virtual environment inside `gjp-assetguard-extraction-tool/`.

Windows:

```powershell
cd "D:/{your path}/AssetGuard AI group11/gjp-assetguard-extraction-tool"
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS / Linux:

```bash
cd "/path/to/AssetGuard AI group11/gjp-assetguard-extraction-tool"
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

Before starting the AI tool, configure its own `.env` file in:

```text
gjp-assetguard-extraction-tool/.env
```

Required environment variables:

```env
GOOGLE_APPLICATION_CREDENTIALS=./your-service-account.json
GCP_BUCKET_NAME=your-gcs-bucket-name
GEMINI_API_KEY=your-gemini-api-key
```

Optional when using GPT flow:

```env
OPENAI_API_KEY=your-openai-api-key
```

What these are used for:

- `GOOGLE_APPLICATION_CREDENTIALS`: Google Cloud service account JSON path
- `GCP_BUCKET_NAME`: Google Cloud Storage bucket for OCR workflow
- `GEMINI_API_KEY`: Gemini extraction
- `OPENAI_API_KEY`: GPT extraction

Run the AI tool:

```bash
python app.py
```

Typical local URL:

```text
http://127.0.0.1:5001
```

## Recommended local workflow

1. Start `AssetGuard AI` in its own virtual environment.
2. Start `gjp-assetguard-extraction-tool` in its own virtual environment.
3. Use the AI tool to generate asset JSON into `gjp-assetguard-extraction-tool/uploads/`.
4. Use the main backend API to import those JSON files into the main SQLite database.

## Common API workflow

### 1. Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "admin@demo.com",
  "password": "admin123"
}
```

Use the returned token in later requests:

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
  "locationName": "Berth 5",
  "name": "Berth 9",
  "loadCapacities": [
    {
      "name": "max point load",
      "metric": "kN",
      "maxLoad": 1000,
      "details": "per spec"
    }
  ]
}
```

Notes:

- `locationName` is matched against existing locations using tolerant matching
- if no close match exists, a new location is created automatically
- duplicate assets in the same `company + location + name` return `409 asset_already_exists`

### 4. Import AI-generated JSON files

Admin only:

```http
POST /api/v1/assets/import-json-uploads
Authorization: Bearer <admin_token>
Content-Type: application/json

{}
```

Optional explicit path:

```json
{
  "directoryPath": "D:/下载/AssetGuard AI group11/gjp-assetguard-extraction-tool/uploads"
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
  "equipmentModel": "Mobile crane 50t",
  "loadParameterValue": 500,
  "remark": "Pre-lift check"
}
```

### 6. View evaluation history

Admin or manager:

```http
GET /api/v1/evaluations/history?page=1&pageSize=20
Authorization: Bearer <manager_or_admin_token>
```

## Common routes

### Auth

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/users` (`System_Admin` only)

### Locations

- `GET /api/v1/locations/`
- `POST /api/v1/locations/` (`System_Admin`, `Asset_Manager`)

### Assets

- `GET /api/v1/assets/?locationId=...`
- `GET /api/v1/assets/all?page=1&pageSize=20`
- `POST /api/v1/assets/` (`System_Admin`, `Asset_Manager`)
- `POST /api/v1/assets/import-json-uploads` (`System_Admin` only)
- `GET /api/v1/assets/<asset_id>/load-capacities`
- `POST /api/v1/assets/<asset_id>/load-capacities`
- `PUT /api/v1/assets/<asset_id>/load-capacities/<capacity_id>`
- `DELETE /api/v1/assets/<asset_id>/load-capacities/<capacity_id>`

### Evaluations

- `GET /api/v1/evaluations/equipment-options`
- `POST /api/v1/evaluations/check`
- `GET /api/v1/evaluations/history?page=1&pageSize=20`

## Validation rules

### Allowed load capacity names

- `max point load`
- `max axle load`
- `max uniform distributor load`
- `max displacement size`

### Allowed metrics

- `kN`
- `t`
- `kPa`

## Automated tests

Run:

```bash
python -m unittest tests.test_api_flow -v
```

Current expected result:

- `Ran 2 tests ...`
- `OK`

## Utility scripts

- `view_db.py` prints the current SQLite tables and key records

## License

MIT. See `LICENSE`.
