"""
Load unit conversion: **English unit strings only** — kg, ton (metric), lb.

Comparisons are done in kilograms; planned load is converted back to the asset's
stored unit for persistence and overload percentage (aligned with max_load_capacity).
"""

from __future__ import annotations

LB_TO_KG = 0.45359237
TON_TO_KG = 1000.0

# Allowed English aliases (case-insensitive). Canonical stored values: kg | ton | lb
_ALLOWED = frozenset(
    {
        "kg",
        "t",
        "ton",
        "tons",
        "lb",
        "lbs",
        "pound",
        "pounds",
    }
)


def normalize_load_unit(raw: str | None) -> str:
    """
    Normalize a unit string to 'kg', 'ton', or 'lb'.

    Only English tokens are accepted (e.g. kg, t, ton, lb, lbs, pound, pounds).
    """
    if raw is None:
        raise ValueError("Unit is required")
    s = str(raw).strip()
    if not s:
        raise ValueError("Unit is required")

    lower = s.lower()
    if lower not in _ALLOWED:
        raise ValueError(
            f"Unsupported unit {raw!r}. Use English only: kg, ton (or t), or lb (or lbs)."
        )

    if lower == "kg":
        return "kg"
    if lower in ("t", "ton", "tons"):
        return "ton"
    if lower in ("lb", "lbs", "pound", "pounds"):
        return "lb"

    raise ValueError(f"Unsupported unit: {raw!r}")


def value_to_kg(value: float, unit: str) -> float:
    """Convert a numeric value from the given canonical unit to kilograms."""
    u = normalize_load_unit(unit)
    if u == "kg":
        return float(value)
    if u == "ton":
        return float(value) * TON_TO_KG
    if u == "lb":
        return float(value) * LB_TO_KG
    raise ValueError(f"Internal error: unknown unit {u!r}")


def value_from_kg(value_kg: float, target_unit: str) -> float:
    """Convert kilograms to the target canonical unit."""
    u = normalize_load_unit(target_unit)
    if u == "kg":
        return float(value_kg)
    if u == "ton":
        return float(value_kg) / TON_TO_KG
    if u == "lb":
        return float(value_kg) / LB_TO_KG
    raise ValueError(f"Internal error: unknown unit {u!r}")
