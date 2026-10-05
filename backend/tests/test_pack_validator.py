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
