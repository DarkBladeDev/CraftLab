import pytest
from pathlib import Path
from app.domain.particles import (
    validate_particle_definition,
    save_particle,
    get_particle,
    list_particles,
    delete_particle,
    generate_particle_command,
)


def test_validate_particle_definition():
    valid_data = {
        "textures": ["craftlab:particle/spark_0", "craftlab:particle/spark_1"]
    }
    valid, err = validate_particle_definition(valid_data)
    assert valid is True
    assert err is None

    # Empty textures array
    invalid_empty = {"textures": []}
    valid, err = validate_particle_definition(invalid_empty)
    assert valid is False
    assert "non-empty 'textures'" in err


def test_particles_crud(tmp_path: Path):
    workspace = tmp_path / "workspace"

    saved = save_particle(
        workspace_dir=workspace,
        particle_id="mystic_spark",
        textures=["craftlab:particle/spark"],
        emitter_params={"speed": 4, "spread": 5, "rate": 8},
        namespace="craftlab"
    )
    assert saved["id"] == "mystic_spark"
    assert saved["resource_location"] == "craftlab:mystic_spark"
    assert "craftlab:mystic_spark" in saved["command"]

    # Get
    item = get_particle(workspace, "mystic_spark", "craftlab")
    assert item is not None
    assert item["is_valid"] is True
    assert len(item["textures"]) == 1

    # List
    all_parts = list_particles(workspace)
    assert len(all_parts) == 1
    assert all_parts[0]["id"] == "mystic_spark"

    # Command
    cmd = generate_particle_command("mystic_spark", count=20, speed=0.1, namespace="craftlab")
    assert cmd == "/particle craftlab:mystic_spark ~ ~1 ~ 0.3 0.5 0.3 0.1 20"

    # Delete
    del_ok = delete_particle(workspace, "mystic_spark", "craftlab")
    assert del_ok is True
    assert get_particle(workspace, "mystic_spark", "craftlab") is None
