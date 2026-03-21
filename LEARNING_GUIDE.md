# AssetGuard AI — Code Reading Guide

Suggested order: follow the **Controller → Service → Model** flow.

## 1) How the app starts

- `assetguard_app.py` — exposes `app` for `flask --app assetguard_app.py ...`
- `app/__init__.py` — `create_app()`: config, db/migrate, blueprints, error handlers, `seed` CLI

## 2) API shape

- `app/utils/responses.py` — `ok()` / `err()` envelopes
- `app/utils/errors.py` — `ApiError` and global handlers

## 3) Auth and RBAC

- `app/utils/auth.py` — token issue/verify, `AuthContext`, `require_auth`, `require_roles`

## 4) Main flows

- **Evaluation:** `evaluation_controller.py` → `evaluation_service.py` → `asset.py`, `evaluation_log.py`
- **Assets:** `asset_controller.py` → `asset_service.py`
- **Auth:** `auth_controller.py` → `auth_service.py` → `user.py`

## 5) Demo data

- `app/commands/seed.py` — `flask seed` (upsert company + admin/manager/contractor users)

## 6) Practice

- Log in → create asset (manager/admin) → `POST /evaluations/check` with `evaluationUnit` (English: `kg`, `ton`, `lb`) → `GET /evaluations/history`
- Try missing token (401), contractor creating asset (403), invalid unit (400)
