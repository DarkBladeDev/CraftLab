import json
import pytest
from pathlib import Path
from app.domain.equipment import (
    validate_equipment_model_schema,
    normalize_legacy_equipment_data,
    save_equipment_model,
    list_equipment_models,
    get_equipment_model,
    delete_equipment_model,
    generate_equippable_component,
    get_equipment_model_path,
    get_legacy_equipment_model_path,
)
from app.domain.pack_merger import PackMerger


def test_validate_equipment_model_schema():
    # Valid 1.21.4+ standard model
    valid_data = {
        "layers": {
            "humanoid": [
                {"texture": "craftlab:paladin"},
                {"texture": "craftlab:paladin_overlay", "dyeable": {"color_when_undyed": 10511680}}
            ],
            "humanoid_leggings": [
                {"texture": "craftlab:paladin"}
            ],
            "wings": [
                {"texture": "craftlab:custom_wings", "use_player_texture": True}
            ]
        }
    }
    valid, err = validate_equipment_model_schema(valid_data)
    assert valid is True
    assert err is None

    # Invalid: layers is a list instead of dict
    invalid_list = {
        "layers": [{"texture": "craftlab:paladin", "type": "humanoid"}]
    }
    valid, err = validate_equipment_model_schema(invalid_list)
    assert valid is False
    assert "must define a non-empty 'layers' object" in err

    # Invalid: missing texture
    invalid_no_texture = {
        "layers": {
            "humanoid": [{}]
        }
    }
    valid, err = validate_equipment_model_schema(invalid_no_texture)
    assert valid is False
    assert "missing a valid 'texture'" in err

    # Invalid: unsupported layer type
    invalid_type = {
        "layers": {
            "spaceship": [{"texture": "craftlab:paladin"}]
        }
    }
    valid, err = validate_equipment_model_schema(invalid_type)
    assert valid is False
    assert "Invalid layer type 'spaceship'" in err

    # Invalid: dyeable is not dict
    invalid_dyeable = {
        "layers": {
            "humanoid": [{"texture": "craftlab:paladin", "dyeable": "yes"}]
        }
    }
    valid, err = validate_equipment_model_schema(invalid_dyeable)
    assert valid is False
    assert "'dyeable' must be an object" in err


def test_normalize_legacy_equipment_data():
    legacy_data = {
        "layers": [
            {"texture": "craftlab:armor_base", "type": "humanoid"},
            {"texture": "craftlab:armor_overlay", "type": "humanoid", "dyeable": True},
            {"texture": "craftlab:leggings", "type": "humanoid_leggings"},
            {"texture": "craftlab:wolf_armor", "type": "wolf"}
        ]
    }
    normalized = normalize_legacy_equipment_data(legacy_data)
    layers = normalized["layers"]
    assert isinstance(layers, dict)
    assert "humanoid" in layers
    assert len(layers["humanoid"]) == 2
    assert layers["humanoid"][1]["dyeable"] == {}
    assert "humanoid_leggings" in layers
    assert "wolf_body" in layers  # mapped from 'wolf' to canonical 'wolf_body'

    valid, err = validate_equipment_model_schema(normalized)
    assert valid is True
    assert err is None


def test_save_get_list_delete_equipment_models(tmp_path: Path):
    workspace = tmp_path / "workspace"

    layers = {
        "humanoid": [
            {"texture": "craftlab:paladin"},
            {"texture": "craftlab:paladin_overlay", "dyeable": {"color_when_undyed": 10511680}}
        ],
        "humanoid_leggings": [
            {"texture": "craftlab:paladin"}
        ]
    }

    saved = save_equipment_model(
        workspace_dir=workspace,
        equipment_id="paladin_armor",
        layers=layers,
        namespace="craftlab"
    )
    assert saved["id"] == "paladin_armor"
    assert saved["resource_location"] == "craftlab:paladin_armor"
    assert saved["equippable_component"]["asset_id"] == "craftlab:paladin_armor"
    assert saved["equippable_component"]["slot"] == "chest"

    # Verify canonical file location
    canonical_file = workspace / "assets" / "craftlab" / "equipment" / "paladin_armor.json"
    assert canonical_file.exists()

    # Fetch
    item = get_equipment_model(workspace, "paladin_armor", "craftlab")
    assert item is not None
    assert item["is_valid"] is True
    assert "humanoid" in item["layers"]
    assert "humanoid_leggings" in item["layers"]

    # List
    all_models = list_equipment_models(workspace)
    assert len(all_models) == 1
    assert all_models[0]["id"] == "paladin_armor"
    assert all_models[0]["file_path"] == "assets/craftlab/equipment/paladin_armor.json"

    # Equippable Component generation
    comp = generate_equippable_component("paladin_armor", slot="legs", namespace="craftlab")
    assert comp["minecraft:equippable"]["slot"] == "legs"
    assert comp["minecraft:equippable"]["asset_id"] == "craftlab:paladin_armor"

    # Delete
    del_res = delete_equipment_model(workspace, "paladin_armor", "craftlab")
    assert del_res is True
    assert get_equipment_model(workspace, "paladin_armor", "craftlab") is None
    assert not canonical_file.exists()


def test_legacy_disk_ingestion_and_migration(tmp_path: Path):
    workspace = tmp_path / "workspace"
    legacy_dir = workspace / "assets" / "craftlab" / "models" / "equipment"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    legacy_file = legacy_dir / "old_relic.json"

    legacy_payload = {
        "layers": [
            {"texture": "craftlab:relic_base", "type": "humanoid"},
            {"texture": "craftlab:relic_pants", "type": "humanoid_leggings"}
        ]
    }
    legacy_file.write_text(json.dumps(legacy_payload), encoding="utf-8")

    # Verify discovery
    models = list_equipment_models(workspace)
    assert len(models) == 1
    assert models[0]["id"] == "old_relic"
    assert "humanoid" in models[0]["layers"]

    # Verify fetch
    item = get_equipment_model(workspace, "old_relic")
    assert item is not None
    assert item["is_valid"] is True
    assert item["is_legacy_path"] is True

    # Saving normalizes and migrates to canonical path
    saved = save_equipment_model(workspace, "old_relic", item["layers"], "craftlab")
    canonical_file = workspace / "assets" / "craftlab" / "equipment" / "old_relic.json"
    assert canonical_file.exists()
    assert not legacy_file.exists()  # Old path unlinked


def test_save_equipment_model_custom_namespace_and_colon(tmp_path: Path):
    workspace = tmp_path / "workspace"
    layers = {
        "humanoid": [{"texture": "dev_studio:test_tex"}]
    }

    # Save using colon in ID
    saved = save_equipment_model(
        workspace_dir=workspace,
        equipment_id="dev_studio:shadow_plate",
        layers=layers,
        namespace="craftlab"
    )
    assert saved["id"] == "shadow_plate"
    assert saved["namespace"] == "dev_studio"
    assert saved["resource_location"] == "dev_studio:shadow_plate"

    expected_file = workspace / "assets" / "dev_studio" / "equipment" / "shadow_plate.json"
    assert expected_file.exists()

    # Query with colon in ID
    item = get_equipment_model(workspace, "dev_studio:shadow_plate")
    assert item is not None
    assert item["id"] == "shadow_plate"
    assert item["namespace"] == "dev_studio"

    # Equippable generation with colon
    comp = generate_equippable_component("dev_studio:shadow_plate", slot="chest")
    assert comp["minecraft:equippable"]["asset_id"] == "dev_studio:shadow_plate"

    # Delete with colon
    deleted = delete_equipment_model(workspace, "dev_studio:shadow_plate")
    assert deleted is True
    assert not expected_file.exists()


def test_pack_merger_hybrid_equipment_staging(tmp_path: Path):
    source_layer = tmp_path / "layer1"
    eq_dir = source_layer / "assets" / "craftlab" / "equipment"
    eq_dir.mkdir(parents=True, exist_ok=True)
    eq_file = eq_dir / "knight_armor.json"
    eq_file.write_text(json.dumps({
        "layers": {
            "humanoid": [{"texture": "craftlab:knight"}]
        }
    }), encoding="utf-8")

    output_dir = tmp_path / "dist_pack"
    summary = PackMerger.merge_layers_to_directory(
        ordered_source_dirs=[source_layer],
        output_dir=output_dir,
        pack_format=34,
        max_inclusive=65
    )

    # Canonical root file
    assert (output_dir / "assets" / "craftlab" / "equipment" / "knight_armor.json").exists()
    # Backward-compatible 1.21.2 overlay file
    assert (output_dir / "overlay_v1_21_2" / "assets" / "craftlab" / "models" / "equipment" / "knight_armor.json").exists()
    assert summary["total_equipment"] >= 1
