import json
import pytest
from pathlib import Path
from app.domain.pack_validator import PreflightValidator
from app.domain.items import ItemDefinition


def test_preflight_no_collisions():
    item1 = ItemDefinition(
        id="ruby_sword",
        material="DIAMOND_SWORD",
        display_name="Ruby Sword",
        custom_model_data=1001
    )
    item2 = ItemDefinition(
        id="sapphire_sword",
        material="DIAMOND_SWORD",
        display_name="Sapphire Sword",
        custom_model_data=1002
    )
    item3 = ItemDefinition(
        id="ruby_pickaxe",
        material="DIAMOND_PICKAXE",
        display_name="Ruby Pickaxe",
        custom_model_data=1001  # Same CMD, but different material -> Allowed!
    )

    report = PreflightValidator.validate([item1, item2, item3])
    assert report.is_valid is True
    assert len(report.conflicts) == 0
    assert report.summary["total_cmd_indexed"] == 3


def test_preflight_studio_cmd_collision():
    item1 = ItemDefinition(
        id="ruby_sword",
        material="DIAMOND_SWORD",
        display_name="Ruby Sword",
        custom_model_data=1001
    )
    item2 = ItemDefinition(
        id="crimson_blade",
        material="DIAMOND_SWORD",
        display_name="Crimson Blade",
        custom_model_data=1001  # Collision on DIAMOND_SWORD #1001!
    )

    report = PreflightValidator.validate([item1, item2])
    assert report.is_valid is False
    assert len(report.conflicts) == 1
    conflict = report.conflicts[0]
    assert conflict.material == "DIAMOND_SWORD"
    assert conflict.custom_model_data == 1001
    assert len(conflict.items) == 2
    assert conflict.items[0].link == "/studio?item=ruby_sword"
    assert conflict.items[1].link == "/studio?item=crimson_blade"


def test_preflight_studio_and_external_pack_collision(tmp_path: Path):
    # Setup mock external pack folder
    pack_dir = tmp_path / "mock_oraxen_pack"
    models_dir = pack_dir / "assets" / "minecraft" / "models" / "item"
    models_dir.mkdir(parents=True)

    sword_model_file = models_dir / "diamond_sword.json"
    sword_model_content = {
        "parent": "item/handheld",
        "textures": {"layer0": "item/diamond_sword"},
        "overrides": [
            {
                "predicate": {"custom_model_data": 5005},
                "model": "oraxen:item/amethyst_rapier"
            }
        ]
    }
    sword_model_file.write_text(json.dumps(sword_model_content), encoding="utf-8")

    external_source = {
        "name": "Oraxen Live Pack",
        "storage_path": str(pack_dir)
    }

    # Studio item that collides with external pack CMD 5005
    studio_item = ItemDefinition(
        id="void_rapier",
        material="DIAMOND_SWORD",
        display_name="Void Rapier",
        custom_model_data=5005
    )

    report = PreflightValidator.validate([studio_item], sources=[external_source])
    assert report.is_valid is False
    assert len(report.conflicts) == 1
    conflict = report.conflicts[0]
    assert conflict.material == "DIAMOND_SWORD"
    assert conflict.custom_model_data == 5005
    sources_in_conflict = {i.source for i in conflict.items}
    assert "Studio" in sources_in_conflict
    assert "Oraxen Live Pack" in sources_in_conflict


def test_preflight_item_model_collision():
    item1 = ItemDefinition(
        id="ruby_sword",
        material="DIAMOND_SWORD",
        display_name="Ruby Sword",
        custom_model_data=1001,
        item_model="studio:items/ruby_sword"
    )
    item2 = ItemDefinition(
        id="ruby_blade",
        material="NETHERITE_SWORD",  # Different material, but same item_model!
        display_name="Ruby Blade",
        custom_model_data=1002,
        item_model="studio:items/ruby_sword"  # Collision!
    )

    report = PreflightValidator.validate([item1, item2])
    assert report.is_valid is False
    assert any(c.type == "item_model_collision" for c in report.conflicts)
    conflict = [c for c in report.conflicts if c.type == "item_model_collision"][0]
    assert conflict.path == "studio:items/ruby_sword"
    assert len(conflict.items) == 2


def test_preflight_modern_item_definition_collision(tmp_path: Path):
    pack_dir = tmp_path / "modern_pack"
    items_dir = pack_dir / "assets" / "minecraft" / "items"
    items_dir.mkdir(parents=True)

    sword_file = items_dir / "diamond_sword.json"
    sword_file.write_text(json.dumps({
        "model": {
            "type": "minecraft:select",
            "property": "minecraft:custom_model_data",
            "cases": [
                {
                    "when": 7007,
                    "model": {"type": "minecraft:model", "model": "plugin:item/blade"}
                }
            ]
        }
    }), encoding="utf-8")

    external_source = {
        "name": "Modern Pack",
        "storage_path": str(pack_dir)
    }

    studio_item = ItemDefinition(
        id="studio_blade",
        material="DIAMOND_SWORD",
        display_name="Studio Blade",
        custom_model_data=7007
    )

    report = PreflightValidator.validate([studio_item], sources=[external_source])
    assert report.is_valid is False
    assert any(c.custom_model_data == 7007 for c in report.conflicts)

