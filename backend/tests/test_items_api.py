import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from app.core.database import init_db, engine, Base


async def reset_db():
    await init_db()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.mark.asyncio
async def test_items_crud_with_components():
    await reset_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create item with 1.21 components
        item_payload = {
            "id": "celestial_bow",
            "material": "BOW",
            "display_name": "<aqua><bold>Celestial Bow</bold></aqua>",
            "lore": ["<gray>Shoots light arrows</gray>"],
            "custom_model_data": 20005,
            "item_flags": ["HIDE_ATTRIBUTES"],
            "amount": 1,
            "components": {
                "minecraft:attribute_modifiers": [
                    {"type": "generic.attack_damage", "amount": 8.5, "slot": "mainhand"}
                ],
                "minecraft:enchantments": {"infinity": 1, "power": 5}
            },
            "export_format": "native"
        }
        res = await client.post("/api/items", json=item_payload)
        assert res.status_code == 200
        saved = res.json()
        assert saved["id"] == "celestial_bow"
        assert saved["components"]["minecraft:enchantments"]["power"] == 5

        # List items
        list_res = await client.get("/api/items")
        assert list_res.status_code == 200
        items = list_res.json()
        assert len(items) == 1
        assert items[0]["components"]["minecraft:enchantments"]["infinity"] == 1

        # Create revision from current
        rev_res = await client.post("/api/revisions")
        assert rev_res.status_code == 200
        rev_data = rev_res.json()
        assert rev_data["revision_number"] == 1
        assert rev_data["items_count"] == 1
