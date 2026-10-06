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
async def test_blocks_crud():
    await reset_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create block
        block_payload = {
            "id": "oak_chair",
            "display_name": "<yellow>Oak Chair</yellow>",
            "mode": "display_prop",
            "item_model": "studio:furniture/oak_chair",
            "scale": [1.0, 1.0, 1.0],
            "translation": [0.0, 0.0, 0.0],
            "hitbox_type": "solid",
            "hitbox_offsets": [[0, 0, 0]],
            "interaction_type": "seat",
            "seat_height": 0.45,
            "hardness": 1.5,
            "tool_type": "AXE",
            "drop_item_id": "oak_chair_item"
        }
        res = await client.post("/api/v1/blocks", json=block_payload)
        assert res.status_code == 200
        saved = res.json()
        assert saved["id"] == "oak_chair"
        assert saved["interaction_type"] == "seat"

        # List blocks
        list_res = await client.get("/api/v1/blocks")
        assert list_res.status_code == 200
        blocks = list_res.json()
        assert len(blocks) == 1
        assert blocks[0]["id"] == "oak_chair"

        # Get single block
        get_res = await client.get("/api/v1/blocks/oak_chair")
        assert get_res.status_code == 200
        assert get_res.json()["display_name"] == "<yellow>Oak Chair</yellow>"

        # Update block via PUT
        block_payload["display_name"] = "<gold>Deluxe Oak Chair</gold>"
        put_res = await client.put("/api/v1/blocks/oak_chair", json=block_payload)
        assert put_res.status_code == 200
        assert put_res.json()["display_name"] == "<gold>Deluxe Oak Chair</gold>"

        # Verify revision creation with item and block
        # First add an item
        item_payload = {
            "id": "oak_chair_item",
            "material": "OAK_STAIRS",
            "display_name": "Oak Chair Item",
            "amount": 1
        }
        await client.post("/api/items", json=item_payload)

        rev_res = await client.post("/api/revisions")
        assert rev_res.status_code == 200
        rev_data = rev_res.json()
        assert rev_data["items_count"] == 1
        assert rev_data["blocks_count"] == 1

        # Delete block
        del_res = await client.delete("/api/v1/blocks/oak_chair")
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "deleted"

        # Verify 404 after delete
        not_found_res = await client.get("/api/v1/blocks/oak_chair")
        assert not_found_res.status_code == 404


@pytest.mark.asyncio
async def test_openapi_includes_blocks():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/openapi.json")
        assert res.status_code == 200
        schema = res.json()
        assert "/api/v1/blocks" in schema["paths"]
