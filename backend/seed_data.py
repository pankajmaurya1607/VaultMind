"""Seed the database with initial roles, departments, and an admin user.

Usage: python seed_data.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.auth.jwt import hash_password
from app.config.settings import settings
from app.db.session import Base
from app.models.department import Department
from app.models.role import Role
from app.models.user import User


def seed():
    engine = create_engine(settings.DATABASE_URL_SYNC)

    Base.metadata.create_all(engine)

    with Session(engine) as db:
        roles = ["Admin", "Manager", "Employee"]
        for role_name in roles:
            existing = db.query(Role).filter(Role.name == role_name).first()
            if not existing:
                db.add(Role(name=role_name))
                print(f"Created role: {role_name}")

        departments = ["Finance", "HR", "Engineering", "Sales", "Marketing"]
        for dept_name in departments:
            existing = db.query(Department).filter(Department.name == dept_name).first()
            if not existing:
                db.add(Department(name=dept_name))
                print(f"Created department: {dept_name}")

        db.commit()

        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        eng_dept = db.query(Department).filter(Department.name == "Engineering").first()

        if admin_role and eng_dept:
            existing_admin = db.query(User).filter(User.email == "admin@eka.com").first()
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
                print("Created admin user: admin@eka.com / admin123")

    print("Seed complete!")


if __name__ == "__main__":
    seed()
