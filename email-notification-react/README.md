# Email Notification React Module

This folder contains a standalone React UI for the **email notification scope only**.

## Features

- Email notification preferences form
- Email template editor
- Alerts & communication logs table
- Bearer-token based sync buttons for backend integration
- Mock fallback logs for local UI iteration

## Run locally

```bash
cd email-notification-react
npm install
npm run dev
```

Open the Vite URL (usually `http://127.0.0.1:5173`).

## If `http://127.0.0.1:5173` is blank

Check these in order:

1. Confirm dev server is really running in this folder:

```bash
cd email-notification-react
npm run dev
```

2. Confirm browser console has no module/dependency errors.
   If you see `Cannot find module 'react'` / `react-dom` / `@vitejs/plugin-react`, dependencies were not installed:

```bash
rm -rf node_modules package-lock.json
npm install
npm run dev
```

3. Confirm the terminal still shows Vite listening on `5173`.
   This project is configured with fixed `5173` + strict port in `vite.config.js`.

4. Hard refresh browser cache (`Ctrl+Shift+R` / `Cmd+Shift+R`).

## Optional backend wiring

Set backend base URL via env:

```bash
VITE_API_BASE_URL=http://127.0.0.1:5000/api/v1
```

Current API paths expected by this UI:

- `GET /alerts/email-logs`
- `PUT /alerts/email-preferences`
- `PUT /alerts/email-template`

Current backend already provides a lightweight demo implementation for these paths.
By default backend uses `SMTP_SUPPRESS_SEND=true` (records logs without real outbound email).
If these endpoints are not available yet, the page still works with mock logs and local state.
