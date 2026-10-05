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
        assert "discovered_catalog_items" in tables
        assert "revisions" in tables
        assert "deployments" in tables
        assert "pack_sources" in tables
        assert "compiled_packs" in tables

        # Verify components column exists in items table
        pragma_items = await conn.execute(text("PRAGMA table_info(items);"))
        item_cols = {row[1] for row in pragma_items.fetchall()}
        assert "components" in item_cols

