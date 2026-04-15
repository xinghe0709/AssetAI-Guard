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

## Optional backend wiring

Set backend base URL via env:

```bash
VITE_API_BASE_URL=http://127.0.0.1:5000/api/v1
```

Current API paths expected by this UI:

- `GET /alerts/email-logs`
- `PUT /alerts/email-preferences`
- `PUT /alerts/email-template`

If these endpoints are not available yet, the page still works with mock logs and local state.
