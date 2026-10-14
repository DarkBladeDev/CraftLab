from typing import List, Optional
import re
from pydantic import BaseModel, Field, field_validator


class ItemDefinition(BaseModel):
    id: str = Field(..., description="Unique alphanumeric identifier (slug) for the item", min_length=1, max_length=64)
    material: str = Field(..., description="Vanilla Minecraft material name, e.g. DIAMOND_SWORD")
    display_name: str = Field(..., description="Display name, supports MiniMessage or plain text", min_length=1)
    lore: List[str] = Field(default_factory=list, description="List of lore lines")
    custom_model_data: Optional[int] = Field(default=None, description="Custom model data integer for resource packs", ge=0)
    item_model: Optional[str] = Field(default=None, description="Namespaced item model identifier (e.g. 'studio:ruby_sword') for Minecraft 1.21.2+")
    item_flags: List[str] = Field(default_factory=list, description="Item flags such as HIDE_ATTRIBUTES")
    amount: int = Field(default=1, ge=1, le=64, description="Stack size count (1-64)")
    components: dict = Field(default_factory=dict, description="Minecraft 1.21 Data Components mapping")
    export_format: str = Field(default="native", description="Export target adapter: native, oraxen, nexo")
    plugin_properties: dict = Field(default_factory=dict, description="Structured plugin-specific properties")
    raw_extensions: Optional[str] = Field(default=None, description="Raw YAML/JSON extensions snippet")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9_-]+$", v):
            raise ValueError("Item id must be lowercase alphanumeric with dashes or underscores only")
        return v

    @field_validator("item_model")
    @classmethod
    def validate_item_model(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip().lower()
            if not re.match(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$", cleaned):
                raise ValueError("Item model must be a valid namespaced key (e.g. 'studio:ruby_sword')")
            return cleaned
        return v

    @field_validator("material")
    @classmethod
    def validate_material(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not re.match(r"^[A-Z0-9_]+$", cleaned):
            raise ValueError("Material must be uppercase alphanumeric with underscores (e.g. DIAMOND_SWORD)")
        return cleaned

    def to_canonical_dict(self) -> dict:
        """Returns sorted, deterministic dictionary representation for canonical hashing."""
        return {
            "amount": self.amount,
            "components": self.components,
            "custom_model_data": self.custom_model_data,
            "display_name": self.display_name,
            "export_format": self.export_format,
            "id": self.id,
            "item_flags": sorted(self.item_flags),
            "item_model": self.item_model,
            "lore": list(self.lore),
            "material": self.material,
            "plugin_properties": self.plugin_properties,
            "raw_extensions": self.raw_extensions,
        }


ARMOR_TIER_ATTRIBUTES = {
    "NETHERITE": {
        "HEAD": {"armor": 3.0, "armor_toughness": 3.0, "knockback_resistance": 0.1},
        "CHEST": {"armor": 8.0, "armor_toughness": 3.0, "knockback_resistance": 0.1},
        "LEGS": {"armor": 6.0, "armor_toughness": 3.0, "knockback_resistance": 0.1},
        "FEET": {"armor": 3.0, "armor_toughness": 3.0, "knockback_resistance": 0.1},
    },
    "DIAMOND": {
        "HEAD": {"armor": 3.0, "armor_toughness": 2.0},
        "CHEST": {"armor": 8.0, "armor_toughness": 2.0},
        "LEGS": {"armor": 6.0, "armor_toughness": 2.0},
        "FEET": {"armor": 3.0, "armor_toughness": 2.0},
    },
    "IRON": {
        "HEAD": {"armor": 2.0},
        "CHEST": {"armor": 6.0},
        "LEGS": {"armor": 5.0},
        "FEET": {"armor": 2.0},
    },
    "GOLDEN": {
        "HEAD": {"armor": 2.0},
        "CHEST": {"armor": 5.0},
        "LEGS": {"armor": 3.0},
        "FEET": {"armor": 1.0},
    },
    "CHAINMAIL": {
        "HEAD": {"armor": 2.0},
        "CHEST": {"armor": 5.0},
        "LEGS": {"armor": 4.0},
        "FEET": {"armor": 1.0},
    },
}

SLOT_TO_LEATHER_MATERIAL = {
    "HEAD": "LEATHER_HELMET",
    "CHEST": "LEATHER_CHESTPLATE",
    "LEGS": "LEATHER_LEGGINGS",
    "FEET": "LEATHER_BOOTS",
    "BODY": "LEATHER_HORSE_ARMOR",
}


def derive_hybrid_equipment_fallback(
    item: ItemDefinition,
    shader_meta: Optional[dict] = None
) -> ItemDefinition:
    """
    Synthesizes legacy pre-1.21.2 fallback attributes for an item binding minecraft:equippable:
    - Sets base material to LEATHER_* matching the target equipment slot.
    - Sets dyed_color component to the assigned shader layer index (RGB).
    - Preserves or injects compensating attribute modifiers matching the original armor tier.
    - Appends HIDE_DYE to item_flags.
    """
    equippable = item.components.get("minecraft:equippable")
    if not equippable or not isinstance(equippable, dict):
        return item

    slot = str(equippable.get("slot", "chest")).upper()
    target_leather = SLOT_TO_LEATHER_MATERIAL.get(slot, item.material)

    orig_mat = item.material.upper()
    tier = None
    if "NETHERITE" in orig_mat:
        tier = "NETHERITE"
    elif "DIAMOND" in orig_mat:
        tier = "DIAMOND"
    elif "IRON" in orig_mat:
        tier = "IRON"
    elif "GOLD" in orig_mat:
        tier = "GOLDEN"
    elif "CHAINMAIL" in orig_mat:
        tier = "CHAINMAIL"

    updated_components = dict(item.components)

    if shader_meta and "color_rgb" in shader_meta:
        updated_components["minecraft:dyed_color"] = {"rgb": int(shader_meta["color_rgb"])}

    if tier and slot in ARMOR_TIER_ATTRIBUTES.get(tier, {}):
        stats = ARMOR_TIER_ATTRIBUTES[tier][slot]
        existing_attrs = updated_components.get("minecraft:attribute_modifiers")
        if not existing_attrs:
            attr_modifiers = []
            slot_name = slot.lower()
            if "armor" in stats:
                attr_modifiers.append({
                    "type": "minecraft:generic.armor",
                    "name": "generic.armor",
                    "amount": stats["armor"],
                    "operation": "add_value",
                    "slot": slot_name
                })
            if "armor_toughness" in stats:
                attr_modifiers.append({
                    "type": "minecraft:generic.armor_toughness",
                    "name": "generic.armor_toughness",
                    "amount": stats["armor_toughness"],
                    "operation": "add_value",
                    "slot": slot_name
                })
            if "knockback_resistance" in stats:
                attr_modifiers.append({
                    "type": "minecraft:generic.knockback_resistance",
                    "name": "generic.knockback_resistance",
                    "amount": stats["knockback_resistance"],
                    "operation": "add_value",
                    "slot": slot_name
                })
            updated_components["minecraft:attribute_modifiers"] = attr_modifiers

    flags = list(item.item_flags)
    if "HIDE_DYE" not in flags:
        flags.append("HIDE_DYE")

    return ItemDefinition(
        id=item.id,
        material=target_leather,
        display_name=item.display_name,
        lore=list(item.lore),
        custom_model_data=item.custom_model_data,
        item_model=item.item_model,
        item_flags=flags,
        amount=item.amount,
        components=updated_components,
        export_format=item.export_format,
        plugin_properties=dict(item.plugin_properties),
        raw_extensions=item.raw_extensions
    )
