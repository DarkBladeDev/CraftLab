import json
import pytest
from pathlib import Path
from PIL import Image
from app.domain.pack_merger import ArmorAtlasStitcher, PackMerger


def create_dummy_texture(path: Path, width=64, height=32, color=(255, 0, 0, 255)):
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (width, height), color)
    img.save(path)


def test_armor_atlas_stitcher_empty_directory(tmp_path):
    root_dir = tmp_path / "pack"
    root_dir.mkdir()
    meta = ArmorAtlasStitcher.synthesize_legacy_armor_assets(root_dir, compatibility_profile="hybrid_shaders")
    assert meta["total_layers"] == 0
    assert len(meta["mappings"]) == 0


def test_armor_atlas_stitcher_multi_model(tmp_path):
    root_dir = tmp_path / "pack"
    root_dir.mkdir()

    # Model 1: Paladin
    paladin_eq = {
        "layers": {
            "humanoid": [{"texture": "craftlab:paladin"}],
            "humanoid_leggings": [{"texture": "craftlab:paladin"}]
        }
    }
    eq_path = root_dir / "assets" / "craftlab" / "equipment"
    eq_path.mkdir(parents=True, exist_ok=True)
    (eq_path / "paladin.json").write_text(json.dumps(paladin_eq), encoding="utf-8")

    tex_armor_dir = root_dir / "assets" / "craftlab" / "textures" / "entity" / "equipment" / "humanoid"
    tex_leggings_dir = root_dir / "assets" / "craftlab" / "textures" / "entity" / "equipment" / "humanoid_leggings"
    create_dummy_texture(tex_armor_dir / "paladin.png", 64, 32, (200, 10, 10, 255))
    create_dummy_texture(tex_leggings_dir / "paladin.png", 64, 32, (10, 200, 10, 255))

    # Model 2: Ruby
    ruby_eq = {
        "layers": {
            "humanoid": [{"texture": "craftlab:ruby"}],
            "humanoid_leggings": [{"texture": "craftlab:ruby"}]
        }
    }
    (eq_path / "ruby.json").write_text(json.dumps(ruby_eq), encoding="utf-8")
    create_dummy_texture(tex_armor_dir / "ruby.png", 64, 32, (10, 10, 200, 255))
    create_dummy_texture(tex_leggings_dir / "ruby.png", 64, 32, (200, 200, 10, 255))

    summary = ArmorAtlasStitcher.synthesize_legacy_armor_assets(root_dir, compatibility_profile="hybrid_shaders")

    assert summary["total_layers"] == 3  # 1 base + 2 custom
    assert len(summary["mappings"]) == 2
    assert "craftlab:paladin" in summary["mappings"]
    assert "craftlab:ruby" in summary["mappings"]

    # Verify atlas textures exist and have expected dimensions: 64 x (32 * 3) = 64 x 96
    layer1_path = root_dir / "assets" / "minecraft" / "textures" / "models" / "armor" / "leather_layer_1.png"
    layer2_path = root_dir / "assets" / "minecraft" / "textures" / "models" / "armor" / "leather_layer_2.png"
    assert layer1_path.exists()
    assert layer2_path.exists()

    with Image.open(layer1_path) as img1:
        assert img1.size == (64, 96)
    with Image.open(layer2_path) as img2:
        assert img2.size == (64, 96)

    # Verify overlays are 64x32 blank
    overlay1_path = root_dir / "assets" / "minecraft" / "textures" / "models" / "armor" / "leather_layer_1_overlay.png"
    assert overlay1_path.exists()
    with Image.open(overlay1_path) as o1:
        assert o1.size == (64, 32)

    # Verify shaders injected
    shader_vsh = root_dir / "assets" / "minecraft" / "shaders" / "core" / "rendertype_armor_cutout_no_cull.vsh"
    shader_fsh = root_dir / "assets" / "minecraft" / "shaders" / "core" / "rendertype_armor_cutout_no_cull.fsh"
    shader_json = root_dir / "assets" / "minecraft" / "shaders" / "core" / "rendertype_armor_cutout_no_cull.json"

    assert shader_vsh.exists()
    assert shader_fsh.exists()
    assert shader_json.exists()

    vsh_content = shader_vsh.read_text(encoding="utf-8")
    assert "#define TOTAL_LAYERS 3" in vsh_content


def test_deterministic_pack_merger_hybrid_vs_modern_profile(tmp_path):
    # Setup source pack layer
    layer_dir = tmp_path / "source_pack"
    eq_path = layer_dir / "assets" / "craftlab" / "equipment"
    eq_path.mkdir(parents=True, exist_ok=True)
    paladin_eq = {
        "layers": {
            "humanoid": [{"texture": "craftlab:paladin"}],
            "humanoid_leggings": [{"texture": "craftlab:paladin"}]
        }
    }
    (eq_path / "paladin.json").write_text(json.dumps(paladin_eq), encoding="utf-8")
    tex_dir = layer_dir / "assets" / "craftlab" / "textures" / "entity" / "equipment" / "humanoid"
    tex_dir.mkdir(parents=True, exist_ok=True)
    create_dummy_texture(tex_dir / "paladin.png", 64, 32)

    # 1. Hybrid Shaders Profile
    out_hybrid = tmp_path / "out_hybrid"
    PackMerger.merge_layers_to_directory([layer_dir], out_hybrid, compatibility_profile="hybrid_shaders")

    hybrid_vsh = out_hybrid / "assets" / "minecraft" / "shaders" / "core" / "rendertype_armor_cutout_no_cull.vsh"
    assert hybrid_vsh.exists()
    # Ensure overlay_v1_21_4 is clean of legacy shader
    modern_overlay_shader = out_hybrid / "overlay_v1_21_4" / "assets" / "minecraft" / "shaders" / "core" / "rendertype_armor_cutout_no_cull.vsh"
    assert not modern_overlay_shader.exists()

    # 2. Modern Native Profile
    out_modern = tmp_path / "out_modern"
    PackMerger.merge_layers_to_directory([layer_dir], out_modern, compatibility_profile="modern_native")

    modern_root_vsh = out_modern / "assets" / "minecraft" / "shaders" / "core" / "rendertype_armor_cutout_no_cull.vsh"
    assert not modern_root_vsh.exists()
