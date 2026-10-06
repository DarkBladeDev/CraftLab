import json
from pathlib import Path
from app.domain.pack_merger import SemanticMerger


def test_merge_sounds_json():
    base = {
        "item.sword.hit": {"sounds": ["minecraft:item/hit1", "minecraft:item/hit2"]}
    }
    overlay = {
        "item.ruby_dagger.slash": {"sounds": ["studio:dagger/slash"]},
        "item.sword.hit": {"category": "player"}
    }
    merged = SemanticMerger.merge_sounds_json(base, overlay)
    assert "item.ruby_dagger.slash" in merged
    assert "item.sword.hit" in merged
    assert merged["item.sword.hit"]["sounds"] == ["minecraft:item/hit1", "minecraft:item/hit2"]
    assert merged["item.sword.hit"]["category"] == "player"


def test_merge_font_json():
    base = {
        "providers": [
            {"type": "bitmap", "file": "minecraft:font/ascii.png", "chars": ["!"]}
        ]
    }
    overlay = {
        "providers": [
            {"type": "bitmap", "file": "minecraft:font/ascii.png", "chars": ["!"]},  # duplicate
            {"type": "bitmap", "file": "studio:font/custom_icons.png", "chars": ["\uE001"]}
        ]
    }
    merged = SemanticMerger.merge_font_json(base, overlay)
    assert len(merged["providers"]) == 2
    files = [p["file"] for p in merged["providers"]]
    assert "minecraft:font/ascii.png" in files
    assert "studio:font/custom_icons.png" in files


def test_merge_atlas_json():
    base = {
        "sources": [{"type": "directory", "source": "item", "prefix": "item/"}]
    }
    overlay = {
        "sources": [
            {"type": "directory", "source": "item", "prefix": "item/"},
            {"type": "directory", "source": "studio_items", "prefix": "studio_items/"}
        ]
    }
    merged = SemanticMerger.merge_atlas_json(base, overlay)
    assert len(merged["sources"]) == 2


def test_merge_item_model_json_sorted_cmd():
    base = {
        "parent": "item/handheld",
        "overrides": [
            {"predicate": {"custom_model_data": 500}, "model": "base:item/sword_500"},
            {"predicate": {"custom_model_data": 100}, "model": "base:item/sword_100"}
        ]
    }
    overlay = {
        "overrides": [
            {"predicate": {"custom_model_data": 250}, "model": "overlay:item/sword_250"},
            {"predicate": {"custom_model_data": 100}, "model": "overlay:item/sword_100_updated"}
        ]
    }
    merged = SemanticMerger.merge_item_model_json(base, overlay)
    # Check overrides are sorted: 100, 250, 500
    cmds = [ov["predicate"]["custom_model_data"] for ov in merged["overrides"]]
    assert cmds == [100, 250, 500]
    # Check CMD 100 was overridden by overlay
    assert merged["overrides"][0]["model"] == "overlay:item/sword_100_updated"


def test_merge_layers_to_directory(tmp_path: Path):
    layer1 = tmp_path / "layer1"
    layer2 = tmp_path / "layer2"
    output_dir = tmp_path / "out_pack"

    # Layer 1 (base): texture and sound
    (layer1 / "assets" / "minecraft" / "textures" / "item").mkdir(parents=True)
    (layer1 / "assets" / "minecraft" / "textures" / "item" / "base.png").write_bytes(b"PNG_DATA_1")
    (layer1 / "assets" / "minecraft").mkdir(parents=True, exist_ok=True)
    (layer1 / "assets" / "minecraft" / "sounds.json").write_text(
        json.dumps({"sound1": {"sounds": ["s1"]}}), encoding="utf-8"
    )

    # Layer 2 (overlay): additional texture and sound
    (layer2 / "assets" / "minecraft" / "textures" / "item").mkdir(parents=True)
    (layer2 / "assets" / "minecraft" / "textures" / "item" / "custom.png").write_bytes(b"PNG_DATA_2")
    (layer2 / "assets" / "minecraft").mkdir(parents=True, exist_ok=True)
    (layer2 / "assets" / "minecraft" / "sounds.json").write_text(
        json.dumps({"sound2": {"sounds": ["s2"]}}), encoding="utf-8"
    )

    summary = SemanticMerger.merge_layers_to_directory(
        ordered_source_dirs=[layer1, layer2],
        output_dir=output_dir,
        pack_format=34
    )

    assert (output_dir / "pack.mcmeta").exists()
    assert (output_dir / "assets" / "minecraft" / "textures" / "item" / "base.png").exists()
    assert (output_dir / "assets" / "minecraft" / "textures" / "item" / "custom.png").exists()

    merged_sounds = json.loads((output_dir / "assets" / "minecraft" / "sounds.json").read_text(encoding="utf-8"))
    assert "sound1" in merged_sounds
    assert "sound2" in merged_sounds
    assert summary["total_textures"] == 2
    assert summary["is_hybrid_multiversion"] is True

    # Verify multi-version pack.mcmeta
    mcmeta = json.loads((output_dir / "pack.mcmeta").read_text(encoding="utf-8"))
    assert mcmeta["pack"]["pack_format"] == 34
    assert mcmeta["pack"]["supported_formats"]["min_inclusive"] == 34
    assert mcmeta["pack"]["supported_formats"]["max_inclusive"] == 65
    assert len(mcmeta["overlays"]["entries"]) == 1
    assert mcmeta["overlays"]["entries"][0]["directory"] == "overlay_v1_21_2"


def test_merge_item_definition_json():
    base = {
        "model": {
            "type": "minecraft:select",
            "property": "minecraft:custom_model_data",
            "cases": [
                {"when": "1001", "model": {"type": "minecraft:model", "model": "base:item/one"}},
                {"when": "1003", "model": {"type": "minecraft:model", "model": "base:item/three"}}
            ]
        }
    }
    overlay = {
        "model": {
            "type": "minecraft:select",
            "property": "minecraft:custom_model_data",
            "cases": [
                {"when": "1002", "model": {"type": "minecraft:model", "model": "overlay:item/two"}},
                {"when": "1001", "model": {"type": "minecraft:model", "model": "overlay:item/one_updated"}}
            ]
        }
    }
    merged = SemanticMerger.merge_item_definition_json(base, overlay)
    cases = merged["model"]["cases"]
    assert len(cases) == 3
    when_vals = [c["when"] for c in cases]
    assert when_vals == ["1001", "1002", "1003"]
    assert cases[0]["model"]["model"] == "overlay:item/one_updated"


def test_dual_projection_cross_generation(tmp_path: Path):
    pack_dir = tmp_path / "test_dual_pack"

    # Only provide legacy models/item/diamond_sword.json
    legacy_file = pack_dir / "assets" / "minecraft" / "models" / "item" / "diamond_sword.json"
    legacy_file.parent.mkdir(parents=True)
    legacy_file.write_text(json.dumps({
        "parent": "item/handheld",
        "overrides": [
            {"predicate": {"custom_model_data": 9001}, "model": "custom:item/excalibur"}
        ]
    }), encoding="utf-8")

    # Run dual projection
    SemanticMerger.apply_dual_projection(pack_dir)

    # Modern overlay definition must have been created!
    modern_file = pack_dir / "overlay_v1_21_2" / "assets" / "minecraft" / "items" / "diamond_sword.json"
    assert modern_file.exists()
    modern_data = json.loads(modern_file.read_text(encoding="utf-8"))
    assert modern_data["model"]["type"] == "minecraft:select"
    assert modern_data["model"]["cases"][0]["when"] == "9001"
    assert modern_data["model"]["cases"][0]["model"]["model"] == "custom:item/excalibur"

