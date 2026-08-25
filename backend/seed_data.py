"""Seed the database with initial roles, departments, and an admin user.

Prerequisite: schema must exist (run `python migrate.py` / `alembic upgrade head` first).

Usage: python seed_data.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.jwt import hash_password
from app.db.sync_engine import get_sync_engine
from app.models.department import Department
from app.models.role import Role
from app.models.user import User


def _first(db: Session, model, name: str):
    return db.execute(select(model).where(model.name == name)).scalar_one_or_none()


def seed():
    engine = get_sync_engine()

    with Session(engine) as db:
        roles = ["Admin", "Manager", "Employee"]
        for role_name in roles:
            if not _first(db, Role, role_name):
                db.add(Role(name=role_name))
                print(f"Created role: {role_name}")

        departments = ["Finance", "HR", "Engineering", "Sales", "Marketing"]
        for dept_name in departments:
            if not _first(db, Department, dept_name):
                db.add(Department(name=dept_name))
                print(f"Created department: {dept_name}")

        db.commit()

        admin_role = _first(db, Role, "Admin")
        eng_dept = _first(db, Department, "Engineering")

        if admin_role and eng_dept:
            existing_admin = db.execute(
                select(User).where(User.email == "admin@eka.com")
            ).scalar_one_or_none()
            if not existing_admin:
                admin_user = User(
                    name="Admin User",
                    email="admin@eka.com",
                    password_hash=hash_password("admin123"),
                    department_id=eng_dept.id,
                    role_id=admin_role.id,
                )
                db.add(admin_user)
                db.commit()
                print("Created admin user: admin@eka.com (change this password immediately)")

    print("Seed complete!")


if __name__ == "__main__":
    seed()
