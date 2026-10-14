import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from main import app
from app.domain.items import (
    ItemDefinition,
    derive_hybrid_equipment_fallback,
    ARMOR_TIER_ATTRIBUTES,
    SLOT_TO_LEATHER_MATERIAL,
)
from app.domain.equipment import (
    calculate_legacy_shader_metadata,
    save_equipment_model,
    list_equipment_models,
)

client = TestClient(app)


def test_calculate_legacy_shader_metadata(tmp_path):
    eq_dir = tmp_path / "assets" / "craftlab" / "equipment"
    eq_dir.mkdir(parents=True, exist_ok=True)
    (eq_dir / "paladin.json").write_text(json.dumps({"layers": {}}), encoding="utf-8")
    (eq_dir / "ruby.json").write_text(json.dumps({"layers": {}}), encoding="utf-8")

    meta = calculate_legacy_shader_metadata(tmp_path)
    assert len(meta) == 2
    assert "craftlab:paladin" in meta
    assert "craftlab:ruby" in meta

    p_meta = meta["craftlab:paladin"]
    assert p_meta["shader_id"] == 1
    assert p_meta["slot_index"] == 1
    assert p_meta["color_rgb"] == 1
    assert p_meta["hex"] == "#000001"
    assert p_meta["total_layers"] == 2


def test_derive_hybrid_equipment_fallback(tmp_path):
    # Setup dummy equipment model in workspace
    eq_dir = tmp_path / "assets" / "craftlab" / "equipment"
    eq_dir.mkdir(parents=True, exist_ok=True)
    eq_data = {
        "layers": {
            "humanoid": [{"texture": "craftlab:paladin"}],
            "humanoid_leggings": [{"texture": "craftlab:paladin"}]
        }
    }
    (eq_dir / "paladin.json").write_text(json.dumps(eq_data), encoding="utf-8")

    meta = calculate_legacy_shader_metadata(tmp_path)
    paladin_shader = meta["craftlab:paladin"]

    # Item with NETHERITE_CHESTPLATE and equippable component
    item = ItemDefinition(
        id="paladin_chestplate",
        material="NETHERITE_CHESTPLATE",
        display_name="Paladin Plate",
        lore=["Legendary armor"],
        custom_model_data=1001,
        item_model="craftlab:paladin_chestplate",
        item_flags=["HIDE_ATTRIBUTES"],
        amount=1,
        components={
            "minecraft:equippable": {
                "slot": "chest",
                "asset_id": "craftlab:paladin"
            }
        }
    )

    fallback = derive_hybrid_equipment_fallback(item, shader_meta=paladin_shader)

    # Assert material converted to LEATHER_CHESTPLATE
    assert fallback.material == "LEATHER_CHESTPLATE"

    # Assert HIDE_DYE added
    assert "HIDE_DYE" in fallback.item_flags
    assert "HIDE_ATTRIBUTES" in fallback.item_flags

    # Assert dyed_color added
    assert "minecraft:dyed_color" in fallback.components
    assert fallback.components["minecraft:dyed_color"]["rgb"] == 1

    # Assert compensating attribute modifiers added (difference between netherite and leather chestplate)
    assert "minecraft:attribute_modifiers" in fallback.components
    modifiers = fallback.components["minecraft:attribute_modifiers"]
    types = [m["type"] for m in modifiers]
    assert "minecraft:generic.armor" in types
    assert "minecraft:generic.armor_toughness" in types
    assert "minecraft:generic.knockback_resistance" in types

    armor_mod = next(m for m in modifiers if m["type"] == "minecraft:generic.armor")
    # Netherite chestplate armor attribute: 8.0
    assert armor_mod["amount"] == 8.0
    assert armor_mod["slot"] == "chest"


def test_derive_hybrid_equipment_non_equippable():
    sword = ItemDefinition(
        id="ruby_sword",
        material="DIAMOND_SWORD",
        display_name="Ruby Sword",
        lore=[],
        amount=1,
        components={}
    )
    res = derive_hybrid_equipment_fallback(sword)
    assert res.material == "DIAMOND_SWORD"
    assert "minecraft:dyed_color" not in res.components


def test_api_hybrid_fallback_endpoint(tmp_path, monkeypatch):
    from app.domain import workspace
    monkeypatch.setattr(workspace, "get_default_workspace_dir", lambda: tmp_path)

    # Create dummy equipment
    eq_dir = tmp_path / "assets" / "craftlab" / "equipment"
    eq_dir.mkdir(parents=True, exist_ok=True)
    eq_data = {
        "layers": {
            "humanoid": [{"texture": "craftlab:valkyrie"}],
            "humanoid_leggings": [{"texture": "craftlab:valkyrie"}]
        }
    }
    (eq_dir / "valkyrie.json").write_text(json.dumps(eq_data), encoding="utf-8")

    payload = {
        "id": "valkyrie_helm",
        "material": "DIAMOND_HELMET",
        "display_name": "Valkyrie Helm",
        "lore": [],
        "custom_model_data": 5001,
        "item_flags": [],
        "amount": 1,
        "components": {
            "minecraft:equippable": {
                "slot": "head",
                "asset_id": "craftlab:valkyrie"
            }
        }
    }

    res = client.post("/api/items/hybrid-fallback", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["material"] == "LEATHER_HELMET"
    assert "HIDE_DYE" in data["item_flags"]
    assert "minecraft:dyed_color" in data["components"]
    assert data["components"]["minecraft:dyed_color"]["rgb"] == 1


def test_creative_equipment_legacy_shader_metadata(tmp_path):
    eq_layers = {
        "humanoid": [{"texture": "craftlab:paladin"}],
        "humanoid_leggings": [{"texture": "craftlab:paladin"}]
    }
    save_equipment_model(tmp_path, "paladin", eq_layers, namespace="craftlab")

    # List
    models = list_equipment_models(tmp_path, namespace="craftlab")
    assert len(models) == 1
    assert "legacy_shader" in models[0]
    assert models[0]["legacy_shader"]["shader_id"] == 1
    assert models[0]["legacy_shader"]["hex"] == "#000001"
