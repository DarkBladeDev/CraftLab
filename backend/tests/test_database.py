import pytest
from sqlalchemy import text
from app.core.database import init_db, engine, Base
import app.models.entities  # Ensure models are registered


@pytest.mark.asyncio
async def test_init_db_creates_tables():
    await init_db()
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = {row[0] for row in result.fetchall()}
        assert "targets" in tables
        assert "items" in tables
        assert "revisions" in tables
        assert "deployment_plans" in tables
        assert "deployments" in tables
