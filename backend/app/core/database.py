from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings

DATABASE_URL = settings.database_url

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    from app.models import entities  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        def check_and_migrate(connection):
            from sqlalchemy import inspect, text
            inspector = inspect(connection)
            if "items" in inspector.get_table_names():
                columns = [col["name"] for col in inspector.get_columns("items")]
                if "components" not in columns:
                    connection.execute(text("ALTER TABLE items ADD COLUMN components JSON DEFAULT '{}'"))
                if "item_model" not in columns:
                    connection.execute(text("ALTER TABLE items ADD COLUMN item_model VARCHAR DEFAULT NULL"))
            if "revisions" in inspector.get_table_names():
                rev_columns = [col["name"] for col in inspector.get_columns("revisions")]
                if "blocks_snapshot" not in rev_columns:
                    connection.execute(text("ALTER TABLE revisions ADD COLUMN blocks_snapshot JSON DEFAULT '[]'"))

        await conn.run_sync(check_and_migrate)

