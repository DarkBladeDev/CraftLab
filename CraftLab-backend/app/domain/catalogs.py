from typing import Optional, List, Dict, Any

VANILLA_CATEGORIES = [
    "combat",
    "tools",
    "armor",
    "blocks",
    "items",
    "food",
    "redstone",
]

VANILLA_ITEMS: List[Dict[str, Any]] = [
    # Combat
    {"id": "DIAMOND_SWORD", "name": "Diamond Sword", "category": "combat", "stack_size": 1},
    {"id": "NETHERITE_SWORD", "name": "Netherite Sword", "category": "combat", "stack_size": 1},
    {"id": "IRON_SWORD", "name": "Iron Sword", "category": "combat", "stack_size": 1},
    {"id": "GOLDEN_SWORD", "name": "Golden Sword", "category": "combat", "stack_size": 1},
    {"id": "STONE_SWORD", "name": "Stone Sword", "category": "combat", "stack_size": 1},
    {"id": "WOODEN_SWORD", "name": "Wooden Sword", "category": "combat", "stack_size": 1},
    {"id": "BOW", "name": "Bow", "category": "combat", "stack_size": 1},
    {"id": "CROSSBOW", "name": "Crossbow", "category": "combat", "stack_size": 1},
    {"id": "TRIDENT", "name": "Trident", "category": "combat", "stack_size": 1},
    {"id": "SHIELD", "name": "Shield", "category": "combat", "stack_size": 1},
    {"id": "MACE", "name": "Mace (1.21)", "category": "combat", "stack_size": 1},
    {"id": "WIND_CHARGE", "name": "Wind Charge (1.21)", "category": "combat", "stack_size": 64},
    {"id": "ARROW", "name": "Arrow", "category": "combat", "stack_size": 64},
    {"id": "SPECTRAL_ARROW", "name": "Spectral Arrow", "category": "combat", "stack_size": 64},

    # Tools
    {"id": "DIAMOND_PICKAXE", "name": "Diamond Pickaxe", "category": "tools", "stack_size": 1},
    {"id": "NETHERITE_PICKAXE", "name": "Netherite Pickaxe", "category": "tools", "stack_size": 1},
    {"id": "IRON_PICKAXE", "name": "Iron Pickaxe", "category": "tools", "stack_size": 1},
    {"id": "DIAMOND_AXE", "name": "Diamond Axe", "category": "tools", "stack_size": 1},
    {"id": "NETHERITE_AXE", "name": "Netherite Axe", "category": "tools", "stack_size": 1},
    {"id": "DIAMOND_SHOVEL", "name": "Diamond Shovel", "category": "tools", "stack_size": 1},
    {"id": "NETHERITE_SHOVEL", "name": "Netherite Shovel", "category": "tools", "stack_size": 1},
    {"id": "DIAMOND_HOE", "name": "Diamond Hoe", "category": "tools", "stack_size": 1},
    {"id": "NETHERITE_HOE", "name": "Netherite Hoe", "category": "tools", "stack_size": 1},
    {"id": "FISHING_ROD", "name": "Fishing Rod", "category": "tools", "stack_size": 1},
    {"id": "FLINT_AND_STEEL", "name": "Flint and Steel", "category": "tools", "stack_size": 1},
    {"id": "SHEARS", "name": "Shears", "category": "tools", "stack_size": 1},
    {"id": "SPYGLASS", "name": "Spyglass", "category": "tools", "stack_size": 1},
    {"id": "BRUSH", "name": "Brush (Archeology)", "category": "tools", "stack_size": 1},

    # Armor
    {"id": "NETHERITE_HELMET", "name": "Netherite Helmet", "category": "armor", "stack_size": 1},
    {"id": "NETHERITE_CHESTPLATE", "name": "Netherite Chestplate", "category": "armor", "stack_size": 1},
    {"id": "NETHERITE_LEGGINGS", "name": "Netherite Leggings", "category": "armor", "stack_size": 1},
    {"id": "NETHERITE_BOOTS", "name": "Netherite Boots", "category": "armor", "stack_size": 1},
    {"id": "DIAMOND_HELMET", "name": "Diamond Helmet", "category": "armor", "stack_size": 1},
    {"id": "DIAMOND_CHESTPLATE", "name": "Diamond Chestplate", "category": "armor", "stack_size": 1},
    {"id": "DIAMOND_LEGGINGS", "name": "Diamond Leggings", "category": "armor", "stack_size": 1},
    {"id": "DIAMOND_BOOTS", "name": "Diamond Boots", "category": "armor", "stack_size": 1},
    {"id": "IRON_CHESTPLATE", "name": "Iron Chestplate", "category": "armor", "stack_size": 1},
    {"id": "ELYTRA", "name": "Elytra", "category": "armor", "stack_size": 1},
    {"id": "TURTLE_HELMET", "name": "Turtle Helmet", "category": "armor", "stack_size": 1},

    # Building / Blocks
    {"id": "STONE", "name": "Stone", "category": "blocks", "stack_size": 64},
    {"id": "COBBLESTONE", "name": "Cobblestone", "category": "blocks", "stack_size": 64},
    {"id": "OAK_PLANKS", "name": "Oak Planks", "category": "blocks", "stack_size": 64},
    {"id": "OBSIDIAN", "name": "Obsidian", "category": "blocks", "stack_size": 64},
    {"id": "ANVIL", "name": "Anvil", "category": "blocks", "stack_size": 64},
    {"id": "ENCHANTING_TABLE", "name": "Enchanting Table", "category": "blocks", "stack_size": 64},
    {"id": "BEACON", "name": "Beacon", "category": "blocks", "stack_size": 64},
    {"id": "CRAFTER", "name": "Crafter (1.21)", "category": "blocks", "stack_size": 64},
    {"id": "VAULT", "name": "Vault (1.21)", "category": "blocks", "stack_size": 64},
    {"id": "TRIAL_SPAWNER", "name": "Trial Spawner (1.21)", "category": "blocks", "stack_size": 64},
    {"id": "COPPER_BLOCK", "name": "Copper Block", "category": "blocks", "stack_size": 64},
    {"id": "TUFF", "name": "Tuff", "category": "blocks", "stack_size": 64},

    # Items / Ingredients
    {"id": "DIAMOND", "name": "Diamond", "category": "items", "stack_size": 64},
    {"id": "EMERALD", "name": "Emerald", "category": "items", "stack_size": 64},
    {"id": "NETHERITE_INGOT", "name": "Netherite Ingot", "category": "items", "stack_size": 64},
    {"id": "GOLD_INGOT", "name": "Gold Ingot", "category": "items", "stack_size": 64},
    {"id": "IRON_INGOT", "name": "Iron Ingot", "category": "items", "stack_size": 64},
    {"id": "NETHERITE_UPGRADE_SMITHING_TEMPLATE", "name": "Netherite Upgrade Template", "category": "items", "stack_size": 64},
    {"id": "HEAVY_CORE", "name": "Heavy Core (1.21)", "category": "items", "stack_size": 64},
    {"id": "TRIAL_KEY", "name": "Trial Key (1.21)", "category": "items", "stack_size": 64},
    {"id": "OMINOUS_TRIAL_KEY", "name": "Ominous Trial Key (1.21)", "category": "items", "stack_size": 64},
    {"id": "BREEZE_ROD", "name": "Breeze Rod (1.21)", "category": "items", "stack_size": 64},
    {"id": "FEATHER", "name": "Feather", "category": "items", "stack_size": 64},
    {"id": "STICK", "name": "Stick", "category": "items", "stack_size": 64},
    {"id": "BLAZE_ROD", "name": "Blaze Rod", "category": "items", "stack_size": 64},
    {"id": "ENDER_PEARL", "name": "Ender Pearl", "category": "items", "stack_size": 16},
    {"id": "TOTEM_OF_UNDYING", "name": "Totem of Undying", "category": "items", "stack_size": 1},
    {"id": "NETHER_STAR", "name": "Nether Star", "category": "items", "stack_size": 64},

    # Food
    {"id": "GOLDEN_APPLE", "name": "Golden Apple", "category": "food", "stack_size": 64},
    {"id": "ENCHANTED_GOLDEN_APPLE", "name": "Enchanted Golden Apple", "category": "food", "stack_size": 64},
    {"id": "COOKED_BEEF", "name": "Steak", "category": "food", "stack_size": 64},
    {"id": "GOLDEN_CARROT", "name": "Golden Carrot", "category": "food", "stack_size": 64},
    {"id": "BREAD", "name": "Bread", "category": "food", "stack_size": 64},

    # Redstone
    {"id": "REDSTONE", "name": "Redstone Dust", "category": "redstone", "stack_size": 64},
    {"id": "REDSTONE_TORCH", "name": "Redstone Torch", "category": "redstone", "stack_size": 64},
    {"id": "REPEATER", "name": "Redstone Repeater", "category": "redstone", "stack_size": 64},
    {"id": "COMPARATOR", "name": "Redstone Comparator", "category": "redstone", "stack_size": 64},
    {"id": "PISTON", "name": "Piston", "category": "redstone", "stack_size": 64},
    {"id": "STICKY_PISTON", "name": "Sticky Piston", "category": "redstone", "stack_size": 64},
    {"id": "OBSERVER", "name": "Observer", "category": "redstone", "stack_size": 64},
    {"id": "HOPPER", "name": "Hopper", "category": "redstone", "stack_size": 64},
    {"id": "DROPPER", "name": "Dropper", "category": "redstone", "stack_size": 64},
    {"id": "DISPENSER", "name": "Dispenser", "category": "redstone", "stack_size": 64},
]


class VanillaCatalogService:
    @staticmethod
    def get_categories() -> List[str]:
        return VANILLA_CATEGORIES

    @staticmethod
    def search(
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        results = VANILLA_ITEMS

        if category and category.lower() != "all":
            cat_norm = category.strip().lower()
            results = [item for item in results if item["category"] == cat_norm]

        if search:
            query = search.strip().lower()
            results = [
                item for item in results
                if query in item["id"].lower() or query in item["name"].lower()
            ]

        return results


from datetime import datetime, timezone
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import DiscoveredCatalogItemModel


async def upsert_discovered_items(
    db: AsyncSession,
    target_id: str,
    source: str,
    items: List[Dict[str, Any]]
) -> List[DiscoveredCatalogItemModel]:
    """Upserts a list of discovered external items for a given target and source."""
    saved_items: List[DiscoveredCatalogItemModel] = []
    now = datetime.now(timezone.utc)

    for item_data in items:
        raw_item_id = item_data.get("id") or item_data.get("item_id")
        if not raw_item_id:
            continue

        composite_id = f"{target_id}:{source}:{raw_item_id}"
        stmt = select(DiscoveredCatalogItemModel).where(DiscoveredCatalogItemModel.id == composite_id)
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()

        if not record:
            record = DiscoveredCatalogItemModel(
                id=composite_id,
                target_id=target_id,
                source=source,
                item_id=raw_item_id,
                material=str(item_data.get("material", "DIAMOND_SWORD")).upper(),
                display_name=item_data.get("display_name") or item_data.get("displayName"),
                lore=item_data.get("lore", []),
                custom_model_data=item_data.get("custom_model_data") or item_data.get("customModelData"),
                item_flags=item_data.get("item_flags", item_data.get("itemFlags", [])),
                raw_properties=item_data.get("raw_properties", item_data.get("properties", {})),
                synced_at=now
            )
            db.add(record)
        else:
            record.material = str(item_data.get("material", record.material)).upper()
            record.display_name = item_data.get("display_name", record.display_name)
            record.lore = item_data.get("lore", record.lore)
            record.custom_model_data = item_data.get("custom_model_data", record.custom_model_data)
            record.item_flags = item_data.get("item_flags", record.item_flags)
            record.raw_properties = item_data.get("raw_properties", record.raw_properties)
            record.synced_at = now

        saved_items.append(record)

    await db.commit()
    return saved_items


async def get_discovered_items_for_target(
    db: AsyncSession,
    target_id: str,
    source: Optional[str] = None,
    search: Optional[str] = None
) -> List[DiscoveredCatalogItemModel]:
    """Retrieves discovered catalog items for a target, optionally filtered by source or text search."""
    stmt = select(DiscoveredCatalogItemModel).where(DiscoveredCatalogItemModel.target_id == target_id)

    if source and source.lower() != "all":
        stmt = stmt.where(DiscoveredCatalogItemModel.source == source.lower())

    res = await db.execute(stmt)
    records = list(res.scalars().all())

    if search:
        q = search.lower()
        records = [
            r for r in records
            if q in r.item_id.lower() or (r.display_name and q in r.display_name.lower()) or q in r.material.lower()
        ]

    return records
