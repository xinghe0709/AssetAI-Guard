from __future__ import annotations

import smtplib
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Any

from flask import current_app
from sqlalchemy import select

from app.models.evaluation_log import EvaluationLog
from app.models.load_capacity import LoadCapacity


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
        "body": "Evaluation result: {status}\\nAsset: {assetName}\\nOverload: {overloadPercent}%",
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
        normalized: list[dict[str, Any]] = []
        for item in _STORE.logs[:limit]:
            normalized.append(
                {
                    "id": f"EV-{item['id']:04d}",
                    "channel": item.get("assetName") or "Unknown Asset",
                    "recipient": item.get("recipient"),
                    "status": item.get("deliveryStatus", "Pending"),
                    "maxPlanned": item.get("maxPlanned", "-"),
                    "overCap": item.get("overCap", "-"),
                    "sentAt": item.get("sentAt"),
                }
            )

        remaining = max(limit - len(normalized), 0)
        if remaining == 0:
            return normalized[:limit]

        stmt = (
            select(EvaluationLog)
            .order_by(EvaluationLog.evaluated_at.desc(), EvaluationLog.id.desc())
            .limit(remaining)
        )
        eval_logs = list(EvaluationLog.query.session.scalars(stmt))

        for log in eval_logs:
            capacity = (
                LoadCapacity.query.filter_by(
                    asset_id=log.asset_id,
                    name=log.matched_capacity_name,
                ).first()
            )
            max_load = f"{int(capacity.max_load) if capacity else '-'}{log.load_parameter_metric if capacity else ''}"
            planned = f"{int(log.load_parameter_value)}{log.load_parameter_metric}"
            normalized.append(
                {
                    "id": f"EV-{log.id:04d}",
                    "channel": log.asset.name if log.asset else "Unknown Asset",
                    "recipient": "ops.team@assetguard.io",
                    "status": "Failed" if log.status.value == "Non-Compliant" else "Delivered",
                    "maxPlanned": f"{max_load} / {planned}",
                    "overCap": f"{round(log.overload_percentage * 100, 1)}%",
                    "sentAt": log.evaluated_at.replace(microsecond=0).isoformat(),
                }
            )
        return normalized[:limit]

    @staticmethod
    def send_test_email() -> dict[str, Any]:
        recipients = [
            item.strip() for item in str(_STORE.preferences.get("recipientsCsv", "")).split(",") if item.strip()
        ]
        if not recipients:
            raise ValueError("No recipients configured in email preferences")

        recipient = recipients[0]
        asset_name = "Template Test Asset"
        status = "Delivered"
        subject = _STORE.template["subject"].format(status="Test", assetName=asset_name)
        body = _STORE.template["body"].format(status="Test", assetName=asset_name, overloadPercent=0)

        delivery_status = "Delivered"
        error = None
        try:
            AlertService._send_email_smtp(recipient=recipient, subject=subject, body=body)
        except Exception as exc:
            delivery_status = "Failed"
            error = str(exc)

        return AlertService._append_log(
            asset_name=asset_name,
            status=status,
            recipient=recipient,
            delivery_status=delivery_status,
            error=error,
            max_planned="1200kg / 1200kg",
            over_cap="0%",
        )

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
            except Exception as exc:
                delivery_status = "Failed"
                error = str(exc)

            AlertService._append_log(
                asset_name=asset_name,
                status=status,
                recipient=recipient,
                delivery_status=delivery_status,
                error=error,
                max_planned="-",
                over_cap=f"{round(overload_percent * 100, 1)}%",
            )

    @staticmethod
    def _append_log(
        *,
        asset_name: str,
        status: str,
        recipient: str,
        delivery_status: str,
        error: str | None,
        max_planned: str,
        over_cap: str,
    ) -> dict[str, Any]:
        log = {
            "id": _STORE.next_id,
            "sentAt": _utc_iso_now(),
            "assetName": asset_name,
            "evaluationStatus": status,
            "recipient": recipient,
            "deliveryStatus": delivery_status,
            "errorMessage": error,
            "maxPlanned": max_planned,
            "overCap": over_cap,
        }
        _STORE.logs.insert(0, log)
        _STORE.next_id += 1
        return {
            "id": f"EV-{log['id']:04d}",
            "channel": log["assetName"],
            "recipient": log["recipient"],
            "status": log["deliveryStatus"],
            "maxPlanned": log["maxPlanned"],
            "overCap": log["overCap"],
            "sentAt": log["sentAt"],
        }

    @staticmethod
    def _send_email_smtp(*, recipient: str, subject: str, body: str) -> None:
        host = current_app.config.get("SMTP_HOST")
        port = int(current_app.config.get("SMTP_PORT", 587))
        username = current_app.config.get("SMTP_USERNAME")
        password = current_app.config.get("SMTP_PASSWORD")
        from_email = current_app.config.get("SMTP_FROM_EMAIL")
        use_tls = bool(current_app.config.get("SMTP_USE_TLS", True))
        suppress_send = bool(current_app.config.get("SMTP_SUPPRESS_SEND", True))

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
