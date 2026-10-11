import pytest
from pathlib import Path
from app.domain.equipment import (
    validate_equipment_model_schema,
    save_equipment_model,
    list_equipment_models,
    get_equipment_model,
    delete_equipment_model,
    generate_equippable_component,
)


def test_validate_equipment_model_schema():
    # Valid model
    valid_data = {
        "layers": [
            {"texture": "craftlab:paladin", "type": "humanoid"},
            {"texture": "craftlab:paladin_overlay", "dyeable": True}
        ]
    }
    valid, err = validate_equipment_model_schema(valid_data)
    assert valid is True
    assert err is None

    # Invalid: missing texture
    invalid_no_texture = {
        "layers": [{"type": "humanoid"}]
    }
    valid, err = validate_equipment_model_schema(invalid_no_texture)
    assert valid is False
    assert "missing a valid 'texture'" in err

    # Invalid: unsupported layer type
    invalid_type = {
        "layers": [{"texture": "craftlab:paladin", "type": "spaceship"}]
    }
    valid, err = validate_equipment_model_schema(invalid_type)
    assert valid is False
    assert "invalid type" in err


def test_save_get_list_delete_equipment_models(tmp_path: Path):
    workspace = tmp_path / "workspace"

    layers = [
        {"texture": "craftlab:paladin", "type": "humanoid"},
        {"texture": "craftlab:paladin_overlay", "dyeable": True}
    ]

    saved = save_equipment_model(
        workspace_dir=workspace,
        equipment_id="paladin_armor",
        layers=layers,
        namespace="craftlab"
    )
    assert saved["id"] == "paladin_armor"
    assert saved["resource_location"] == "craftlab:paladin_armor"

    # Fetch
    item = get_equipment_model(workspace, "paladin_armor", "craftlab")
    assert item is not None
    assert item["is_valid"] is True
    assert len(item["layers"]) == 2

    # List
    all_models = list_equipment_models(workspace)
    assert len(all_models) == 1
    assert all_models[0]["id"] == "paladin_armor"

    # Equippable Component
    comp = generate_equippable_component("paladin_armor", slot="chest", namespace="craftlab")
    assert comp["minecraft:equippable"]["slot"] == "chest"
    assert comp["minecraft:equippable"]["model"] == "craftlab:paladin_armor"

    # Delete
    del_res = delete_equipment_model(workspace, "paladin_armor", "craftlab")
    assert del_res is True
    assert get_equipment_model(workspace, "paladin_armor", "craftlab") is None


def test_save_equipment_model_custom_namespace_and_colon(tmp_path: Path):
    workspace = tmp_path / "workspace"
    layers = [{"texture": "dev_studio:test_tex", "type": "humanoid"}]

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

    expected_file = workspace / "assets" / "dev_studio" / "models" / "equipment" / "shadow_plate.json"
    assert expected_file.exists()

    # Query with colon in ID
    item = get_equipment_model(workspace, "dev_studio:shadow_plate")
    assert item is not None
    assert item["id"] == "shadow_plate"
    assert item["namespace"] == "dev_studio"

    # Equippable generation with colon
    comp = generate_equippable_component("dev_studio:shadow_plate", slot="chest")
    assert comp["minecraft:equippable"]["model"] == "dev_studio:shadow_plate"

    # Delete with colon
    deleted = delete_equipment_model(workspace, "dev_studio:shadow_plate")
    assert deleted is True
    assert not expected_file.exists()
