import click
from flask import Flask

from app.extensions import db
from app.models import Company, User
from app.models.user import UserRole


def register_seed_command(app: Flask) -> None:
    """
    Register `flask seed`: upsert one demo company and three role accounts for API testing.

    Idempotent: safe to run multiple times (updates passwords and roles).
    """

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

        click.echo(f"Company: {company.id} {company.name}")
        click.echo(f"Admin: {admin.email} ({'created' if admin_created else 'updated'})")
        click.echo(f"Manager: {manager.email} ({'created' if manager_created else 'updated'})")
        click.echo(f"Contractor: {contractor.email} ({'created' if contractor_created else 'updated'})")
