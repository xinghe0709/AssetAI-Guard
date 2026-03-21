from sqlalchemy import select

from app.extensions import db
from app.models import Asset
from app.utils.errors import ApiError
from app.utils.load_units import normalize_load_unit


class AssetService:
    @staticmethod
    def list_assets(*, company_id: int, page: int, page_size: int, q: str | None):
        """
        List assets for a tenant with optional name search.

        - company_id is the tenant boundary; every query must include it.
        - q uses ilike for fuzzy match (DB collation rules apply on MySQL).
        - Pagination via db.paginate (Flask-SQLAlchemy 3.x).
        """
        stmt = select(Asset).where(Asset.company_id == company_id)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(Asset.asset_name.ilike(like))

        stmt = stmt.order_by(Asset.id.desc())
        pagination = db.paginate(stmt, page=page, per_page=page_size, error_out=False)

        items = [
            {
                "id": a.id,
                "assetName": a.asset_name,
                "equipmentType": a.equipment_type,
                "maxLoadCapacity": a.max_load_capacity,
                "unit": a.unit,
                "sourceFile": a.source_file,
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
        asset_name: str,
        equipment_type: str | None,
        max_load_capacity: float,
        unit: str | None,
        source_file: str | None,
    ):
        """
        Create an asset.

        - max_load_capacity must be > 0.
        - unit must be English (kg, ton/t, lb) if provided; defaults to kg.
        - RBAC is enforced in the controller; company_id comes from the token.
        """
        if max_load_capacity <= 0:
            raise ApiError("maxLoadCapacity must be greater than 0", 400, code="invalid_max_load_capacity")

        unit_raw = (unit or "").strip() or "kg"
        try:
            unit_canon = normalize_load_unit(unit_raw)
        except ValueError as e:
            raise ApiError(str(e), 400, code="invalid_asset_unit") from e

        asset = Asset(
            company_id=company_id,
            asset_name=asset_name,
            equipment_type=equipment_type,
            max_load_capacity=max_load_capacity,
            unit=unit_canon,
            source_file=source_file,
        )
        db.session.add(asset)
        db.session.commit()
        return {
            "id": asset.id,
            "assetName": asset.asset_name,
            "equipmentType": asset.equipment_type,
            "maxLoadCapacity": asset.max_load_capacity,
            "unit": asset.unit,
            "sourceFile": asset.source_file,
        }
