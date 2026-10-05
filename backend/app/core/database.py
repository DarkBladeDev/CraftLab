from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

DATABASE_URL = "sqlite+aiosqlite:///./mcp.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        def check_and_migrate(connection):
            from sqlalchemy import inspect, text
            inspector = inspect(connection)
            if "items" in inspector.get_table_names():
                columns = [col["name"] for col in inspector.get_columns("items")]
                if "components" not in columns:
                    connection.execute(text("ALTER TABLE items ADD COLUMN components JSON DEFAULT '{}'"))

        await conn.run_sync(check_and_migrate)

