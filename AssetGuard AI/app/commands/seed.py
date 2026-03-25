import click
from flask import Flask

from app.extensions import db
from app.models import Asset, Company, LoadCapacity, Location, User
from app.models.user import UserRole


def register_seed_command(app: Flask) -> None:
    """Register `flask seed`: demo company, users, Port of Bunbury + sample assets (PDF)."""

    @app.cli.command("seed")
    @click.option("--company", "company_name", default="Demo Company", show_default=True)
    @click.option("--admin-email", default="admin@demo.com", show_default=True)
    @click.option("--admin-password", default="admin123", show_default=True)
    @click.option("--manager-email", default="manager@demo.com", show_default=True)
    @click.option("--manager-password", default="manager123", show_default=True)
    @click.option("--contractor-email", default="contractor@demo.com", show_default=True)
    @click.option("--contractor-password", default="contractor123", show_default=True)
    def seed_command(
        company_name: str,
        admin_email: str,
        admin_password: str,
        manager_email: str,
        manager_password: str,
        contractor_email: str,
        contractor_password: str,
    ):
        company = Company.query.filter_by(name=company_name).first()
        if company is None:
            company = Company(name=company_name)
            db.session.add(company)
            db.session.commit()

        def upsert_user(email: str, password: str, role: UserRole):
            user = User.query.filter_by(email=email).first()
            if user is None:
                user = User(email=email, company_id=company.id, role=role)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                return user, True

            user.company_id = company.id
            user.role = role
            user.set_password(password)
            db.session.commit()
            return user, False

        admin, admin_created = upsert_user(admin_email, admin_password, UserRole.SYSTEM_ADMIN)
        manager, manager_created = upsert_user(manager_email, manager_password, UserRole.ASSET_MANAGER)
        contractor, contractor_created = upsert_user(
            contractor_email, contractor_password, UserRole.CONTRACTORS
        )

        loc = Location.query.filter_by(name="Port of Bunbury").first()
        if loc is None:
            loc = Location(name="Port of Bunbury")
            db.session.add(loc)
            db.session.commit()

        def upsert_asset_with_capacities(asset_name: str, caps: list[dict]):
            asset = Asset.query.filter_by(
                company_id=company.id, location_id=loc.id, name=asset_name
            ).first()
            if asset is None:
                asset = Asset(company_id=company.id, location_id=loc.id, name=asset_name)
                db.session.add(asset)
                db.session.flush()
            else:
                LoadCapacity.query.filter_by(asset_id=asset.id).delete()
                db.session.flush()

            for c in caps:
                db.session.add(
                    LoadCapacity(
                        asset_id=asset.id,
                        name=c["name"],
                        metric=c["metric"],
                        max_load=c["max_load"],
                        details=c.get("details"),
                    )
                )
            db.session.commit()
            return asset

        berth5_caps = [
            {"name": "max point load", "metric": "kN", "max_load": 1000.0, "details": "for crane outriggers / EWP wheels"},
            {"name": "max axle load", "metric": "t", "max_load": 87.4, "details": "for heavy vehicles"},
            {"name": "max uniform distributor load", "metric": "kPa", "max_load": 40.0},
            {"name": "max displacement size", "metric": "t", "max_load": 68100.0},
        ]
        berth8_caps = [
            {"name": "max point load", "metric": "kN", "max_load": 2642.0, "details": "for crane outriggers / EWP wheels"},
            {"name": "max axle load", "metric": "t", "max_load": 87.4, "details": "for heavy vehicles"},
            {"name": "max uniform distributor load", "metric": "kPa", "max_load": 40.0},
            {"name": "max displacement size", "metric": "t", "max_load": 72000.0},
        ]
        berth2_caps = [
            {"name": "max point load", "metric": "kN", "max_load": 1200.0, "details": "for crane outriggers / EWP wheels"},
            {"name": "max axle load", "metric": "t", "max_load": 90.0, "details": "for heavy vehicles"},
            {"name": "max uniform distributor load", "metric": "kPa", "max_load": 42.0},
            {"name": "max displacement size", "metric": "t", "max_load": 65000.0},
        ]
        berth3_caps = [
            {"name": "max point load", "metric": "kN", "max_load": 1500.0, "details": "for crane outriggers / EWP wheels"},
            {"name": "max axle load", "metric": "t", "max_load": 95.0, "details": "for heavy vehicles"},
            {"name": "max uniform distributor load", "metric": "kPa", "max_load": 45.0},
            {"name": "max displacement size", "metric": "t", "max_load": 70000.0},
        ]
        berth9_caps = [
            {"name": "max point load", "metric": "kN", "max_load": 2200.0, "details": "for crane outriggers / EWP wheels"},
            {"name": "max axle load", "metric": "t", "max_load": 100.0, "details": "for heavy vehicles"},
            {"name": "max uniform distributor load", "metric": "kPa", "max_load": 48.0},
            {"name": "max displacement size", "metric": "t", "max_load": 76000.0},
        ]
        hardstand_a_caps = [
            {"name": "max point load", "metric": "kN", "max_load": 800.0, "details": "for crane outriggers / EWP wheels"},
            {"name": "max axle load", "metric": "t", "max_load": 70.0, "details": "for heavy vehicles"},
            {"name": "max uniform distributor load", "metric": "kPa", "max_load": 35.0},
            {"name": "max displacement size", "metric": "t", "max_load": 30000.0},
        ]

        upsert_asset_with_capacities("Berth 5", berth5_caps)
        upsert_asset_with_capacities("Berth 8", berth8_caps)
        upsert_asset_with_capacities("Berth 2", berth2_caps)
        upsert_asset_with_capacities("Berth 3", berth3_caps)
        upsert_asset_with_capacities("Berth 9", berth9_caps)
        upsert_asset_with_capacities("Hardstand A", hardstand_a_caps)

        click.echo(f"Company: {company.id} {company.name}")
        click.echo(f"Location: {loc.id} {loc.name}")
        click.echo(f"Admin: {admin.email} ({'created' if admin_created else 'updated'})")
        click.echo(f"Manager: {manager.email} ({'created' if manager_created else 'updated'})")
        click.echo(f"Contractor: {contractor.email} ({'created' if contractor_created else 'updated'})")
        click.echo("Assets seeded: Berth 2/3/5/8/9, Hardstand A (each with 4 capacity rows)")
