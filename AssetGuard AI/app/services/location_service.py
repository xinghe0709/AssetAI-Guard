from sqlalchemy import select

from app.extensions import db
from app.models import Location
from app.utils.errors import ApiError


class LocationService:
    @staticmethod
    def list_locations() -> list[dict]:
        stmt = select(Location).order_by(Location.name)
        rows = db.session.scalars(stmt).all()
        return [{"id": loc.id, "name": loc.name} for loc in rows]

    @staticmethod
    def create_location(*, name: str) -> dict:
        n = (name or "").strip()
        if not n:
            raise ApiError("name is required", 400, code="validation_error")
        if Location.query.filter_by(name=n).first():
            raise ApiError("Location name already exists", 409, code="location_exists")
        loc = Location(name=n)
        db.session.add(loc)
        db.session.commit()
        return {"id": loc.id, "name": loc.name}
