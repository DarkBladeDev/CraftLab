import pytest
from app.domain.catalogs import VanillaCatalogService


def test_vanilla_catalog_categories():
    categories = VanillaCatalogService.get_categories()
    assert "combat" in categories
    assert "tools" in categories
    assert "armor" in categories
    assert "blocks" in categories


def test_vanilla_catalog_filtering():
    combat_items = VanillaCatalogService.search(category="combat")
    assert len(combat_items) > 0
    assert all(item["category"] == "combat" for item in combat_items)
    assert any(item["id"] == "DIAMOND_SWORD" for item in combat_items)
    assert any(item["id"] == "MACE" for item in combat_items)


def test_vanilla_catalog_search():
    sword_results = VanillaCatalogService.search(search="sword")
    assert len(sword_results) > 0
    assert all("sword" in item["id"].lower() or "sword" in item["name"].lower() for item in sword_results)

    # 1.21 specific search
    crafter = VanillaCatalogService.search(search="crafter")
    assert len(crafter) == 1
    assert crafter[0]["id"] == "CRAFTER"


from app.core.database import init_db, AsyncSessionLocal, engine, Base
from app.models.entities import TargetModel
from app.domain.catalogs import upsert_discovered_items, get_discovered_items_for_target


async def reset_db():
    await init_db()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.mark.asyncio
async def test_upsert_and_query_discovered_items():
    await reset_db()
    async with AsyncSessionLocal() as db:
        # Create a test target
        target = TargetModel(
            id="target-catalog-test",
            name="Test Target",
            secret="test-secret",
            status="online"
        )
        db.add(target)
        await db.commit()

        # Upsert items from Oraxen
        oraxen_items = [
            {
                "id": "plasma_sword",
                "material": "DIAMOND_SWORD",
                "display_name": "<aqua>Plasma Sword</aqua>",
                "lore": ["<gray>High tech weapon</gray>"],
                "custom_model_data": 10500,
                "raw_properties": {"Pack": {"model": "custom/weapons/plasma"}}
            },
            {
                "id": "dark_helmet",
                "material": "NETHERITE_HELMET",
                "display_name": "<dark_purple>Dark Helmet</dark_purple>",
                "custom_model_data": 10501,
            }
        ]

        saved = await upsert_discovered_items(db, "target-catalog-test", "oraxen", oraxen_items)
        assert len(saved) == 2

        # Query all
        all_items = await get_discovered_items_for_target(db, "target-catalog-test")
        assert len(all_items) == 2

        # Query filtered by source
        filtered_source = await get_discovered_items_for_target(db, "target-catalog-test", source="oraxen")
        assert len(filtered_source) == 2

        empty_nexo = await get_discovered_items_for_target(db, "target-catalog-test", source="nexo")
        assert len(empty_nexo) == 0

        # Query search
        search_res = await get_discovered_items_for_target(db, "target-catalog-test", search="plasma")
        assert len(search_res) == 1
        assert search_res[0].item_id == "plasma_sword"
        assert search_res[0].custom_model_data == 10500
