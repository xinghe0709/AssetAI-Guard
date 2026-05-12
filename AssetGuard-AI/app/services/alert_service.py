from __future__ import annotations

import smtplib
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Any

from flask import current_app
from sqlalchemy import select

from app.extensions import db
from app.models.evaluation_log import EvaluationLog, EvaluationStatus
from app.models.load_capacity import LoadCapacity


class _SafeDict(dict):
    """Returns the placeholder itself for missing keys instead of raising KeyError."""
    def __missing__(self, key):
        return f"{{{key}}}"


def _format_sent_at(dt: datetime) -> str:
    """Format as 'May 9, 2026, 06:43 PM' in local time."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local_dt = dt.astimezone()
    return f"{local_dt:%B} {local_dt.day}, {local_dt.year}, {local_dt:%I:%M %p}"


@dataclass
class _DemoEmailStore:
    preferences: dict[str, Any]
    logs: list[dict[str, Any]]
    next_id: int = 1


_STORE = _DemoEmailStore(
    preferences={
        "escalationThresholdPercent": 20,
        "digestTimeUtc": "09:00",
        "recipientsCsv": "asset.manager@demo.com,safety@demo.com",
        "sendOnNonCompliant": True,
    },
    logs=[],
)


_DEFAULT_TEMPLATE = {
    "subject": "[AssetGuard] {status} - {assetName} ({equipment})",
    "body": (
        "Equipment {equipment} ({equipmentModel}) was evaluated against "
        "asset {assetName} and found to be {status}.\n\n"
        "Capacity: {capacityName} = {capacityMaxLoad} {loadParameterMetric}\n"
        "Measured Load: {loadParameterValue} {loadParameterMetric}\n"
        "Overload: {overloadPercent}%\n\n"
        "Please review the evaluation and take corrective action."
    ),
}


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
    def _get_template_dict() -> dict[str, str]:
        from app.models.email_template import EmailTemplate

        row = EmailTemplate.query.first()
        if row:
            return {"subject": row.subject, "body": row.body}
        return dict(_DEFAULT_TEMPLATE)

    @staticmethod
    def get_template() -> dict[str, str]:
        return AlertService._get_template_dict()

    @staticmethod
    def update_template(payload: dict[str, Any]) -> dict[str, str]:
        from app.models.email_template import EmailTemplate

        row = EmailTemplate.query.first()
        if row is None:
            row = EmailTemplate(subject="", body="")
            db.session.add(row)
        for key in ("subject", "body"):
            if key in payload and isinstance(payload[key], str):
                setattr(row, key, payload[key])
        db.session.commit()
        return {"subject": row.subject, "body": row.body}

    @staticmethod
    def get_logs(*, limit: int = 100) -> list[dict[str, Any]]:
        entries: list[tuple[str, dict[str, Any]]] = []

        for item in _STORE.logs:
            sort_key = item.get("_sort_ts", "")
            entries.append((sort_key, AlertService._normalize_memory(item)))

        stmt = (
            select(EvaluationLog)
            .where(EvaluationLog.status == EvaluationStatus.NON_COMPLIANT)
            .order_by(EvaluationLog.evaluated_at.desc(), EvaluationLog.id.desc())
            .limit(max(limit, 100))
        )
        for log in EvaluationLog.query.session.scalars(stmt):
            entries.append(
                (log.evaluated_at.isoformat(), AlertService._normalize_db(log))
            )

        entries.sort(key=lambda e: e[0], reverse=True)
        return [entry[1] for entry in entries[:limit]]

    @staticmethod
    def _normalize_memory(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": f"EV-{item['id']:04d}",
            "channel": item.get("assetName") or "Unknown Asset",
            "recipient": item.get("recipient"),
            "status": item.get("deliveryStatus", "Pending"),
            "maxPlanned": item.get("maxPlanned", "-"),
            "overCap": item.get("overCap", "-"),
            "sentAt": item.get("sentAt"),
        }

    @staticmethod
    def _normalize_db(log: EvaluationLog) -> dict[str, Any]:
        capacity = (
            LoadCapacity.query.filter_by(
                asset_id=log.asset_id,
                name=log.matched_capacity_name,
            ).first()
        )
        if capacity:
            max_load = f"{int(capacity.max_load):,}{log.load_parameter_metric}"
        else:
            max_load = "-"
        planned = f"{int(log.load_parameter_value):,}{log.load_parameter_metric}"
        return {
            "id": f"EV-{log.id:04d}",
            "channel": log.asset.name if log.asset else "Unknown Asset",
            "recipient": log.user.email if log.user else "N/A",
            "status": log.email_status or (
                "Delivered" if log.status.value == "Compliant" else "Pending"
            ),
            "maxPlanned": f"{max_load} / {planned}",
            "overCap": f"{round(log.overload_percentage * 100, 1)}%",
            "sentAt": _format_sent_at(log.evaluated_at),
        }

    @staticmethod
    def send_test_email(*, recipient_email: str) -> dict[str, Any]:
        template_vars = {
            "status": "Test",
            "assetName": "Test Asset",
            "equipment": "Test Equipment",
            "equipmentModel": "Test Model",
            "capacityName": "max point load",
            "capacityMaxLoad": "1,000",
            "loadParameterValue": "500",
            "loadParameterMetric": "kN",
            "overloadPercent": 0,
        }
        tpl = AlertService._get_template_dict()
        safe_vars = _SafeDict(template_vars)
        subject = tpl["subject"].format_map(safe_vars)
        body = tpl["body"].format_map(safe_vars)

        delivery_status = "Delivered"
        error = None
        try:
            AlertService._send_email_smtp(recipient=recipient_email, subject=subject, body=body)
        except Exception as exc:
            delivery_status = "Failed"
            error = str(exc)

        return AlertService._append_log(
            asset_name="Test Asset",
            status="Delivered",
            recipient=recipient_email,
            delivery_status=delivery_status,
            error=error,
            max_planned="1,000kN / 500kN",
            over_cap="0%",
        )

    @staticmethod
    def notify_non_compliant(
        *,
        asset_name: str,
        status: str,
        overload_percent: float,
        recipient_email: str,
        equipment: str,
        equipment_model: str | None,
        capacity_name: str,
        capacity_max_load: float,
        load_parameter_value: float,
        load_parameter_metric: str,
        force: bool = False,
    ) -> tuple[str, str | None] | None:
        """Send non-compliance email. Returns (delivery_status, error_message) or None if skipped."""
        if status != "Non-Compliant":
            return None
        if not force and not _STORE.preferences.get("sendOnNonCompliant", True):
            return None

        template_vars = {
            "status": status,
            "assetName": asset_name,
            "equipment": equipment,
            "equipmentModel": equipment_model or "N/A",
            "capacityName": capacity_name,
            "capacityMaxLoad": f"{int(capacity_max_load):,}",
            "loadParameterValue": f"{int(load_parameter_value):,}",
            "loadParameterMetric": load_parameter_metric,
            "overloadPercent": round(overload_percent * 100, 2),
        }
        tpl = AlertService._get_template_dict()
        safe_vars = _SafeDict(template_vars)
        subject = tpl["subject"].format_map(safe_vars)
        body = tpl["body"].format_map(safe_vars)

        try:
            AlertService._send_email_smtp(recipient=recipient_email, subject=subject, body=body)
            return ("Delivered", None)
        except Exception as exc:
            return ("Failed", str(exc))

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
            "_sort_ts": datetime.now(timezone.utc).isoformat(),
            "sentAt": _format_sent_at(datetime.now(timezone.utc)),
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
