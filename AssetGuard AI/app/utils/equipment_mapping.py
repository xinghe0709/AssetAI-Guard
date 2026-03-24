"""
Equipment type -> user load parameter label, metric, and asset LoadCapacity.name (PDF chart).
"""

from __future__ import annotations

from app.models.load_capacity import CapacityMetric, CapacityName
from app.utils.errors import ApiError

# equipment (exact string as in PDF) -> (parameter_label, metric, capacity_name_on_asset)
EQUIPMENT_RULES: dict[str, tuple[str, str, str]] = {
    "Crane with outriggers": ("Max Outrigger Load", "kN", "max point load"),
    "Mobile crane": ("Max Axle Load", "t", "max axle load"),
    "Heavy vehicle": ("Max Axle Load", "t", "max axle load"),
    "Elevated Work Platform": ("Max Wheel Load", "kN", "max point load"),
    "Storage Load": ("Uniform Distributor Load", "kPa", "max uniform distributor load"),
    "Vessel": ("Displacement", "t", "max displacement size"),
}

ALLOWED_METRICS = frozenset(m.value for m in CapacityMetric)
ALLOWED_CAPACITY_NAMES = frozenset(n.value for n in CapacityName)


def normalize_metric(raw: str) -> str:
    m = (raw or "").strip()
    if m not in ALLOWED_METRICS:
        raise ApiError(f"Invalid metric {raw!r}; allowed: kN, t, kPa", 400, code="invalid_metric")
    return m


def normalize_capacity_name(raw: str) -> str:
    n = (raw or "").strip().lower()
    if n not in ALLOWED_CAPACITY_NAMES:
        raise ApiError(
            f"Invalid load capacity name {raw!r}; allowed: {', '.join(sorted(ALLOWED_CAPACITY_NAMES))}",
            400,
            code="invalid_capacity_name",
        )
    return n


def resolve_equipment(equipment: str) -> tuple[str, str, str]:
    if equipment not in EQUIPMENT_RULES:
        raise ApiError("Invalid equipment type", 400, code="invalid_equipment")
    return EQUIPMENT_RULES[equipment]


def equipment_options() -> list[dict]:
    out = []
    for key, (param_label, metric, _cap) in EQUIPMENT_RULES.items():
        out.append(
            {
                "equipment": key,
                "loadParameterLabel": param_label,
                "metric": metric,
            }
        )
    return out
