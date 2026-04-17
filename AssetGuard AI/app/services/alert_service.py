from __future__ import annotations

import smtplib
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Any

from flask import current_app


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class _DemoEmailStore:
    preferences: dict[str, Any]
    template: dict[str, str]
    logs: list[dict[str, Any]]
    next_id: int = 1


_STORE = _DemoEmailStore(
    preferences={
        "escalationThresholdPercent": 20,
        "digestTimeUtc": "09:00",
        "recipientsCsv": "asset.manager@demo.com,safety@demo.com",
        "sendOnNonCompliant": True,
    },
    template={
        "subject": "[AssetGuard] {status} - {assetName}",
        "body": "Evaluation result: {status}\nAsset: {assetName}\nOverload: {overloadPercent}%",
    },
    logs=[],
)


class AlertService:
    """Lightweight demo notification service with in-memory prefs/template/log history."""

    @staticmethod
    def get_preferences() -> dict[str, Any]:
        return dict(_STORE.preferences)

    @staticmethod
    def update_preferences(payload: dict[str, Any]) -> dict[str, Any]:
        for key in ("escalationThresholdPercent", "digestTimeUtc", "recipientsCsv", "sendOnNonCompliant"):
            if key in payload:
                _STORE.preferences[key] = payload[key]
        return dict(_STORE.preferences)

    @staticmethod
    def get_template() -> dict[str, str]:
        return dict(_STORE.template)

    @staticmethod
    def update_template(payload: dict[str, Any]) -> dict[str, str]:
        for key in ("subject", "body"):
            if key in payload and isinstance(payload[key], str):
                _STORE.template[key] = payload[key]
        return dict(_STORE.template)

    @staticmethod
    def get_logs(*, limit: int = 100) -> list[dict[str, Any]]:
        return _STORE.logs[:limit]

    @staticmethod
    def notify_non_compliant(*, asset_name: str, status: str, overload_percent: float) -> None:
        if status != "Non-Compliant":
            return
        if not _STORE.preferences.get("sendOnNonCompliant", True):
            return

        recipients = [
            item.strip() for item in str(_STORE.preferences.get("recipientsCsv", "")).split(",") if item.strip()
        ]
        if not recipients:
            return

        for recipient in recipients:
            subject = _STORE.template["subject"].format(status=status, assetName=asset_name)
            body = _STORE.template["body"].format(
                status=status,
                assetName=asset_name,
                overloadPercent=round(overload_percent * 100, 2),
            )

            delivery_status = "Delivered"
            error = None
            try:
                AlertService._send_email_smtp(recipient=recipient, subject=subject, body=body)
            except Exception as exc:  # demo logging path
                delivery_status = "Failed"
                error = str(exc)

            _STORE.logs.insert(
                0,
                {
                    "id": _STORE.next_id,
                    "sentAt": _utc_iso_now(),
                    "assetName": asset_name,
                    "evaluationStatus": status,
                    "recipient": recipient,
                    "deliveryStatus": delivery_status,
                    "errorMessage": error,
                },
            )
            _STORE.next_id += 1

    @staticmethod
    def _send_email_smtp(*, recipient: str, subject: str, body: str) -> None:
        host = current_app.config.get("SMTP_HOST")
        port = int(current_app.config.get("SMTP_PORT", 587))
        username = current_app.config.get("SMTP_USERNAME")
        password = current_app.config.get("SMTP_PASSWORD")
        from_email = current_app.config.get("SMTP_FROM_EMAIL")
        use_tls = bool(current_app.config.get("SMTP_USE_TLS", True))
        suppress_send = bool(current_app.config.get("SMTP_SUPPRESS_SEND", True))

        # Demo default: do not send real email if SMTP_SUPPRESS_SEND=true.
        if suppress_send or not host or not from_email:
            return

        msg = EmailMessage()
        msg["From"] = from_email
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP(host, port, timeout=10) as smtp:
            if use_tls:
                smtp.starttls()
            if username and password:
                smtp.login(username, password)
            smtp.send_message(msg)
