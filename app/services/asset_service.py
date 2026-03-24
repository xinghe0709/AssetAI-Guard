from sqlalchemy import select

from app.extensions import db
from app.models import Asset, LoadCapacity, Location
from app.utils.equipment_mapping import normalize_capacity_name, normalize_metric
from app.utils.errors import ApiError


class AssetService:
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
        location_id: int,
        name: str,
        load_capacities: list[dict],
    ):
        loc = Location.query.filter_by(id=location_id).first()
        if loc is None:
            raise ApiError("Location not found", 404, code="location_not_found")

        n = (name or "").strip()
        if not n:
            raise ApiError("name is required", 400, code="validation_error")
        if not load_capacities:
            raise ApiError("loadCapacities must contain at least one entry", 400, code="validation_error")

        asset = Asset(company_id=company_id, location_id=location_id, name=n)
        db.session.add(asset)
        db.session.flush()

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
        try:
            max_f = float(max_load)
        except (TypeError, ValueError) as e:
            raise ApiError("maxLoad must be a number", 400, code="validation_error") from e
        if max_f <= 0:
            raise ApiError("maxLoad must be greater than 0", 400, code="validation_error")

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
