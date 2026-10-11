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


def test_preflight_shader_collision(tmp_path: Path):
    src1 = tmp_path / "src1"
    src2 = tmp_path / "src2"

    sh1 = src1 / "assets" / "minecraft" / "shaders" / "core" / "rendertype_text.vsh"
    sh1.parent.mkdir(parents=True)
    sh1.write_text("// shader 1", encoding="utf-8")

    sh2 = src2 / "assets" / "minecraft" / "shaders" / "core" / "rendertype_text.vsh"
    sh2.parent.mkdir(parents=True)
    sh2.write_text("// shader 2", encoding="utf-8")

    sources = [
        {"name": "ShaderPackA", "storage_path": str(src1), "layer_priority": 10},
        {"name": "ShaderPackB", "storage_path": str(src2), "layer_priority": 20}
    ]

    report = PreflightValidator.validate([], sources=sources)
    assert report.has_warnings is True
    shader_warns = [w for w in report.warnings if w.type == "shader_collision"]
    assert len(shader_warns) == 1
    assert "ShaderPackB" in shader_warns[0].message


def test_preflight_missing_texture_reference(tmp_path: Path):
    src = tmp_path / "src"
    model_file = src / "assets" / "studio" / "models" / "item" / "ruby_dagger.json"
    model_file.parent.mkdir(parents=True)
    model_file.write_text(json.dumps({
        "parent": "item/handheld",
        "textures": {
            "layer0": "studio:item/non_existent_ruby"
        }
    }), encoding="utf-8")

    sources = [{"name": "StudioSource", "storage_path": str(src), "layer_priority": 10}]
    report = PreflightValidator.validate([], sources=sources)
    assert report.is_valid is False
    tex_conflicts = [c for c in report.conflicts if c.type == "missing_texture_reference"]
    assert len(tex_conflicts) == 1
    assert "studio:item/non_existent_ruby" in tex_conflicts[0].path


def test_preflight_texture_dimension_and_animation_warnings(tmp_path: Path):
    import struct, zlib

    def make_dummy_png(w: int, h: int) -> bytes:
        header = b"\x89PNG\r\n\x1a\n"
        ihdr_data = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
        ihdr_crc = struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_data))
        return header + struct.pack(">I", 13) + b"IHDR" + ihdr_data + ihdr_crc

    src = tmp_path / "src"
    tex_dir = src / "assets" / "studio" / "textures" / "item"
    tex_dir.mkdir(parents=True)

    # 1. Non-power-of-two (15x15)
    (tex_dir / "odd.png").write_bytes(make_dummy_png(15, 15))

    # 2. Animated strip (16x32) without .png.mcmeta
    (tex_dir / "animated.png").write_bytes(make_dummy_png(16, 32))

    # 3. Animated strip (16x48) WITH .png.mcmeta (should not warn)
    (tex_dir / "valid_anim.png").write_bytes(make_dummy_png(16, 48))
    (tex_dir / "valid_anim.png.mcmeta").write_text('{"animation": {}}', encoding="utf-8")

    sources = [{"name": "TextureSource", "storage_path": str(src), "layer_priority": 10}]
    report = PreflightValidator.validate([], sources=sources)

    warn_types = [w.type for w in report.warnings]
    assert "texture_dimension_warning" in warn_types
    assert "texture_animation_warning" in warn_types


