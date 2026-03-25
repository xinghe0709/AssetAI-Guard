import json
import re
from difflib import SequenceMatcher
from pathlib import Path

from sqlalchemy import select

from app.extensions import db
from app.models import Asset, LoadCapacity, Location
from app.utils.equipment_mapping import (
    normalize_capacity_name,
    normalize_metric,
    validate_capacity_metric_pair,
)
from app.utils.errors import ApiError


class AssetService:
    LOCATION_MATCH_THRESHOLD = 0.88

    @staticmethod
    def _normalize_location_name(raw: str) -> str:
        text = (raw or "").strip().lower()
        text = re.sub(r"[\W_]+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _location_match_score(requested_normalized: str, candidate_normalized: str) -> float:
        if not requested_normalized or not candidate_normalized:
            return 0.0
        if requested_normalized == candidate_normalized:
            return 1.0

        requested_tokens = requested_normalized.split()
        candidate_tokens = candidate_normalized.split()

        if requested_tokens and candidate_tokens:
            req_set = set(requested_tokens)
            cand_set = set(candidate_tokens)
            smaller = min(len(req_set), len(cand_set))
            overlap_score = (len(req_set & cand_set) / smaller) if smaller else 0.0
        else:
            overlap_score = 0.0

        if (
            requested_normalized in candidate_normalized
            or candidate_normalized in requested_normalized
        ) and overlap_score >= 0.8:
            return max(0.95, overlap_score)

        ratio = SequenceMatcher(None, requested_normalized, candidate_normalized).ratio()
        return max(ratio, overlap_score * 0.92)

    @staticmethod
    def _resolve_or_create_location(*, location_name: str) -> Location:
        requested_name = (location_name or "").strip()
        if not requested_name:
            raise ApiError("locationName is required", 400, code="validation_error")

        requested_normalized = AssetService._normalize_location_name(requested_name)
        if not requested_normalized:
            raise ApiError("locationName is required", 400, code="validation_error")

        locations = db.session.scalars(select(Location).order_by(Location.name)).all()
        best_match = None
        best_score = 0.0

        for loc in locations:
            candidate_normalized = AssetService._normalize_location_name(loc.name)
            score = AssetService._location_match_score(requested_normalized, candidate_normalized)
            if score > best_score:
                best_match = loc
                best_score = score

        if best_match is not None and best_score >= AssetService.LOCATION_MATCH_THRESHOLD:
            return best_match

        new_location = Location(name=requested_name)
        db.session.add(new_location)
        db.session.flush()
        return new_location

    @staticmethod
    def _get_owned_asset(*, company_id: int, asset_id: int) -> Asset:
        asset = Asset.query.filter_by(id=asset_id, company_id=company_id).first()
        if asset is None:
            raise ApiError("Asset not found or access denied", 404, code="asset_not_found")
        return asset

    @staticmethod
    def list_assets(*, company_id: int, location_id: int, page: int, page_size: int, q: str | None):
        loc = Location.query.filter_by(id=location_id).first()
        if loc is None:
            raise ApiError("Location not found", 404, code="location_not_found")

        stmt = select(Asset).where(Asset.company_id == company_id, Asset.location_id == location_id)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(Asset.name.ilike(like))
        stmt = stmt.order_by(Asset.id.desc())
        pagination = db.paginate(stmt, page=page, per_page=page_size, error_out=False)

        items = []
        for a in pagination.items:
            caps = [
                {
                    "id": c.id,
                    "name": c.name.value,
                    "metric": c.metric.value,
                    "maxLoad": c.max_load,
                    "details": c.details,
                }
                for c in sorted(a.load_capacities, key=lambda x: x.id)
            ]
            items.append(
                {
                    "id": a.id,
                    "name": a.name,
                    "locationId": a.location_id,
                    "loadCapacities": caps,
                }
            )

        return {
            "items": items,
            "page": pagination.page,
            "pageSize": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }

    @staticmethod
    def list_company_assets(*, company_id: int, page: int, page_size: int, q: str | None):
        stmt = select(Asset).where(Asset.company_id == company_id)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(Asset.name.ilike(like))
        stmt = stmt.order_by(Asset.id.desc())
        pagination = db.paginate(stmt, page=page, per_page=page_size, error_out=False)
        items = [
            {
                "id": a.id,
                "name": a.name,
                "locationId": a.location_id,
            }
            for a in pagination.items
        ]
        return {
            "items": items,
            "page": pagination.page,
            "pageSize": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }

    @staticmethod
    def create_asset(
        *,
        company_id: int,
        location_name: str,
        name: str,
        load_capacities: list[dict],
    ):
        loc = AssetService._resolve_or_create_location(location_name=location_name)

        n = (name or "").strip()
        if not n:
            raise ApiError("name is required", 400, code="validation_error")
        if not load_capacities:
            raise ApiError("loadCapacities must contain at least one entry", 400, code="validation_error")

        existing_asset = Asset.query.filter_by(
            company_id=company_id,
            location_id=loc.id,
            name=n,
        ).first()
        if existing_asset is not None:
            raise ApiError(
                "Asset with the same company, location, and name already exists",
                409,
                code="asset_already_exists",
            )

        asset = Asset(company_id=company_id, location_id=loc.id, name=n)
        db.session.add(asset)
        db.session.flush()

        seen_keys: set[str] = set()
        for row in load_capacities:
            cap_name = (row.get("name") or "").strip()
            metric_raw = row.get("metric")
            max_load = row.get("maxLoad")
            details = row.get("details")
            if not cap_name or max_load is None or metric_raw is None:
                raise ApiError("Each load capacity needs name, metric, and maxLoad", 400, code="validation_error")
            try:
                max_f = float(max_load)
            except (TypeError, ValueError) as e:
                raise ApiError("maxLoad must be a number", 400, code="validation_error") from e
            if max_f <= 0:
                raise ApiError("maxLoad must be greater than 0", 400, code="validation_error")
            cap_name = normalize_capacity_name(cap_name)
            metric = normalize_metric(str(metric_raw))
            validate_capacity_metric_pair(cap_name, metric)
            key = cap_name
            if key in seen_keys:
                raise ApiError(
                    f"Duplicate load capacity: {cap_name}",
                    409,
                    code="duplicate_capacity",
                )
            seen_keys.add(key)
            db.session.add(
                LoadCapacity(
                    asset_id=asset.id,
                    name=cap_name,
                    metric=metric,
                    max_load=max_f,
                    details=(str(details).strip() if details is not None else None) or None,
                )
            )

        db.session.commit()
        db.session.refresh(asset)
        return AssetService._asset_to_dict(asset)

    @staticmethod
    def import_assets_from_json_directory(
        *,
        company_id: int,
        directory_path: str,
    ) -> dict:
        root = Path(directory_path).expanduser()
        if not root.exists() or not root.is_dir():
            raise ApiError("JSON uploads directory does not exist", 404, code="json_uploads_dir_not_found")

        json_files = sorted(p for p in root.iterdir() if p.is_file() and p.suffix.lower() == ".json")
        if not json_files:
            return {
                "directory": str(root),
                "filesScanned": 0,
                "createdCount": 0,
                "rejectedCount": 0,
                "items": [],
                "rejected": [],
            }

        created_items = []
        rejected_items = []

        for file_path in json_files:
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    payload = json.load(f)
            except json.JSONDecodeError as e:
                rejected_items.append(
                    {"file": file_path.name, "reason": "invalid_json", "message": str(e)}
                )
                continue

            if not isinstance(payload, dict):
                rejected_items.append(
                    {"file": file_path.name, "reason": "invalid_payload", "message": "Top-level JSON must be an object"}
                )
                continue

            location_name = payload.get("locationName")
            name = payload.get("name")
            load_capacities = payload.get("loadCapacities")
            if location_name is None or name is None or not isinstance(load_capacities, list):
                rejected_items.append(
                    {
                        "file": file_path.name,
                        "reason": "invalid_asset_payload",
                        "message": "JSON must contain locationName, name, and loadCapacities[]",
                    }
                )
                continue

            try:
                created = AssetService.create_asset(
                    company_id=company_id,
                    location_name=str(location_name),
                    name=str(name),
                    load_capacities=load_capacities,
                )
                created_items.append({"file": file_path.name, "asset": created})
            except ApiError as e:
                db.session.rollback()
                rejected_items.append(
                    {
                        "file": file_path.name,
                        "reason": e.code or "validation_error",
                        "message": e.message,
                        "assetName": name,
                    }
                )

        return {
            "directory": str(root),
            "filesScanned": len(json_files),
            "createdCount": len(created_items),
            "rejectedCount": len(rejected_items),
            "items": created_items,
            "rejected": rejected_items,
        }

    @staticmethod
    def list_load_capacities(*, company_id: int, asset_id: int) -> dict:
        asset = AssetService._get_owned_asset(company_id=company_id, asset_id=asset_id)
        items = [
            {
                "id": c.id,
                "name": c.name.value,
                "metric": c.metric.value,
                "maxLoad": c.max_load,
                "details": c.details,
            }
            for c in sorted(asset.load_capacities, key=lambda x: x.id)
        ]
        return {
            "asset": {"id": asset.id, "name": asset.name, "locationId": asset.location_id},
            "items": items,
        }

    @staticmethod
    def create_load_capacity(
        *,
        company_id: int,
        asset_id: int,
        name: str,
        metric_raw: str,
        max_load: float,
        details: str | None,
    ) -> dict:
        asset = AssetService._get_owned_asset(company_id=company_id, asset_id=asset_id)
        cap_name = normalize_capacity_name(name)
        metric = normalize_metric(metric_raw)
        validate_capacity_metric_pair(cap_name, metric)
        try:
            max_f = float(max_load)
        except (TypeError, ValueError) as e:
            raise ApiError("maxLoad must be a number", 400, code="validation_error") from e
        if max_f <= 0:
            raise ApiError("maxLoad must be greater than 0", 400, code="validation_error")

        existing = LoadCapacity.query.filter_by(
            asset_id=asset.id, name=cap_name,
        ).first()
        if existing is not None:
            raise ApiError(
                f"Load capacity '{cap_name}' already exists for this asset",
                409,
                code="duplicate_capacity",
            )

        cap = LoadCapacity(
            asset_id=asset.id,
            name=cap_name,
            metric=metric,
            max_load=max_f,
            details=(str(details).strip() if details is not None else None) or None,
        )
        db.session.add(cap)
        db.session.commit()
        return {
            "asset": {"id": asset.id, "name": asset.name, "locationId": asset.location_id},
            "capacity": {
                "id": cap.id,
                "name": cap.name.value,
                "metric": cap.metric.value,
                "maxLoad": cap.max_load,
                "details": cap.details,
            },
        }

    @staticmethod
    def update_load_capacity(
        *,
        company_id: int,
        asset_id: int,
        capacity_id: int,
        name: str | None,
        metric_raw: str | None,
        max_load: float | None,
        details: str | None,
    ) -> dict:
        asset = AssetService._get_owned_asset(company_id=company_id, asset_id=asset_id)
        cap = LoadCapacity.query.filter_by(id=capacity_id, asset_id=asset_id).first()
        if cap is None:
            raise ApiError("Load capacity not found", 404, code="capacity_not_found")

        if name is not None:
            cap.name = normalize_capacity_name(name)
        if metric_raw is not None:
            cap.metric = normalize_metric(metric_raw)
        if max_load is not None:
            try:
                max_f = float(max_load)
            except (TypeError, ValueError) as e:
                raise ApiError("maxLoad must be a number", 400, code="validation_error") from e
            if max_f <= 0:
                raise ApiError("maxLoad must be greater than 0", 400, code="validation_error")
            cap.max_load = max_f
        if details is not None:
            cap.details = (str(details).strip() or None)

        db.session.commit()
        return {
            "asset": {"id": asset.id, "name": asset.name, "locationId": asset.location_id},
            "capacity": {
                "id": cap.id,
                "name": cap.name.value,
                "metric": cap.metric.value,
                "maxLoad": cap.max_load,
                "details": cap.details,
            },
        }

    @staticmethod
    def delete_load_capacity(*, company_id: int, asset_id: int, capacity_id: int) -> None:
        _ = AssetService._get_owned_asset(company_id=company_id, asset_id=asset_id)
        cap = LoadCapacity.query.filter_by(id=capacity_id, asset_id=asset_id).first()
        if cap is None:
            raise ApiError("Load capacity not found", 404, code="capacity_not_found")
        db.session.delete(cap)
        db.session.commit()

    @staticmethod
    def _asset_to_dict(asset: Asset) -> dict:
        caps = [
            {
                "id": c.id,
                "name": c.name.value,
                "metric": c.metric.value,
                "maxLoad": c.max_load,
                "details": c.details,
            }
            for c in sorted(asset.load_capacities, key=lambda x: x.id)
        ]
        return {
            "id": asset.id,
            "name": asset.name,
            "locationId": asset.location_id,
            "loadCapacities": caps,
        }
