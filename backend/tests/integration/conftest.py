from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.db.session import Base, get_db
from app.main import app
from app.models.department import Department
from app.models.role import Role

TEST_DATABASE_URL = "postgresql+asyncpg://eka_user:eka_pass@localhost:5432/eka_db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
test_async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def seed_data(db: AsyncSession) -> None:
    roles = await db.execute(text("SELECT COUNT(*) FROM roles"))
    if roles.scalar() == 0:
        db.add_all([Role(name="Admin"), Role(name="Manager"), Role(name="Employee")])
    depts = await db.execute(text("SELECT COUNT(*) FROM departments"))
    if depts.scalar() == 0:
        db.add_all([Department(name="Finance"), Department(name="HR"), Department(name="Engineering")])
    await db.commit()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    async with test_async_session() as session:
        await seed_data(session)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with test_async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_async_session() as session:
        yield session
        await session.close()
