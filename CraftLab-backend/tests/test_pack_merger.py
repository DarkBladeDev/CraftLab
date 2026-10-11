import json
from pathlib import Path
from app.domain.pack_merger import (
    SemanticMerger,
    PackManifestInspector,
    AtlasSynthesizer,
    ShaderRouter
)


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
    assert len(mcmeta["overlays"]["entries"]) == 2
    overlay_dirs = [e["directory"] for e in mcmeta["overlays"]["entries"]]
    assert "overlay_v1_21_2" in overlay_dirs
    assert "overlay_v1_21_4" in overlay_dirs


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


def test_pack_manifest_inspector_format_ranges():
    # Int format
    assert PackManifestInspector.resolve_format_range(34) == (34, 34)
    assert PackManifestInspector.map_range_to_canonical_target(34, 34) == "root"

    # Dict format (1.21.2)
    assert PackManifestInspector.resolve_format_range({"min_inclusive": 42, "max_inclusive": 45}) == (42, 45)
    assert PackManifestInspector.map_range_to_canonical_target(42, 45) == "overlay_v1_21_2"

    # Dict format (1.21.4)
    assert PackManifestInspector.resolve_format_range({"min_inclusive": 46, "max_inclusive": 65}) == (46, 65)
    assert PackManifestInspector.map_range_to_canonical_target(46, 65) == "overlay_v1_21_4"

    # List format
    assert PackManifestInspector.resolve_format_range([42, 43, 44]) == (42, 44)


def test_pack_manifest_inspector_normalize_extracted_pack(tmp_path: Path):
    pack_dir = tmp_path / "external_pack"
    pack_dir.mkdir(parents=True)

    # Write pack.mcmeta with non-standard overlay folders
    mcmeta = {
        "pack": {"pack_format": 34, "description": "Foreign Pack"},
        "overlays": {
            "entries": [
                {
                    "formats": {"min_inclusive": 42, "max_inclusive": 45},
                    "directory": "items_42_dir"
                },
                {
                    "formats": {"min_inclusive": 46, "max_inclusive": 65},
                    "directory": "modern_46_dir"
                }
            ]
        }
    }
    (pack_dir / "pack.mcmeta").write_text(json.dumps(mcmeta), encoding="utf-8")

    # Put a sample file in items_42_dir
    f1 = pack_dir / "items_42_dir" / "assets" / "minecraft" / "items" / "ruby.json"
    f1.parent.mkdir(parents=True)
    f1.write_text('{"test": "42"}', encoding="utf-8")

    # Put a sample file in modern_46_dir
    f2 = pack_dir / "modern_46_dir" / "assets" / "minecraft" / "shaders" / "core" / "sample.vsh"
    f2.parent.mkdir(parents=True)
    f2.write_text('// shader 46', encoding="utf-8")

    # Run normalizer
    actions = PackManifestInspector.normalize_extracted_pack(pack_dir)
    assert len(actions) == 2

    # Verify files were moved to canonical targets
    canonical_42 = pack_dir / "overlay_v1_21_2" / "assets" / "minecraft" / "items" / "ruby.json"
    canonical_46 = pack_dir / "overlay_v1_21_4" / "assets" / "minecraft" / "shaders" / "core" / "sample.vsh"
    assert canonical_42.exists()
    assert canonical_46.exists()

    # Verify foreign folders were removed
    assert not (pack_dir / "items_42_dir").exists()
    assert not (pack_dir / "modern_46_dir").exists()


def test_atlas_synthesizer_blocks_and_gui_sources():
    # 1. Blocks sources induction
    tex_refs = {
        "studio:item/ruby_dagger",
        "studio:props/chair",
        "minecraft:item/iron_sword",  # Vanilla should be skipped
        "oraxen:custom_item"
    }
    block_sources = AtlasSynthesizer.synthesize_blocks_atlas_sources(tex_refs)
    sources_repr = [(s["type"], s.get("source"), s.get("prefix")) for s in block_sources]
    assert ("directory", "studio:item", "item/") in sources_repr
    assert ("directory", "studio:props", "props/") in sources_repr
    assert ("single", None, None) in [(s["type"], None, None) for s in block_sources if s.get("resource") == "oraxen:custom_item"]

    # 2. GUI sources induction
    gui_ns = {"studio", "minecraft", "custom"}
    gui_sources = AtlasSynthesizer.synthesize_gui_atlas_sources(gui_ns)
    gui_repr = [(s["type"], s.get("source"), s.get("prefix")) for s in gui_sources]
    assert ("directory", "gui/sprites", "") in gui_repr
    assert ("directory", "studio:gui/sprites", "") in gui_repr
    assert ("directory", "custom:gui/sprites", "") in gui_repr


def test_atlas_synthesizer_pruning_redundant_singles():
    base = {
        "sources": [
            {"type": "directory", "source": "studio:item", "prefix": "item/"}
        ]
    }
    overlay = {
        "sources": [
            {"type": "single", "resource": "studio:item/ruby_sword"},  # Redundant, covered by directory studio:item!
            {"type": "single", "resource": "studio:other/ruby_gem"}   # Not covered, keep
        ]
    }
    merged = SemanticMerger.merge_atlas_json(base, overlay)
    assert len(merged["sources"]) == 2
    types = [s["type"] for s in merged["sources"]]
    assert types == ["directory", "single"]
    assert merged["sources"][1]["resource"] == "studio:other/ruby_gem"


def test_auto_synthesize_atlases_end_to_end(tmp_path: Path):
    pack_dir = tmp_path / "auto_atlas_pack"
    models_dir = pack_dir / "assets" / "studio" / "models" / "item"
    models_dir.mkdir(parents=True)
    (models_dir / "ruby.json").write_text(json.dumps({
        "textures": {"0": "studio:item/ruby", "1": "studio:props/table"}
    }), encoding="utf-8")

    sprites_dir = pack_dir / "assets" / "studio" / "textures" / "gui" / "sprites"
    sprites_dir.mkdir(parents=True)
    (sprites_dir / "mana_bar.png").write_bytes(b"PNG")

    SemanticMerger.auto_synthesize_atlases(pack_dir)

    blocks_atlas = pack_dir / "assets" / "minecraft" / "atlases" / "blocks.json"
    gui_atlas = pack_dir / "assets" / "minecraft" / "atlases" / "gui.json"

    assert blocks_atlas.exists()
    assert gui_atlas.exists()

    b_data = json.loads(blocks_atlas.read_text(encoding="utf-8"))
    b_dirs = [s["source"] for s in b_data["sources"] if s.get("type") == "directory"]
    assert "studio:item" in b_dirs
    assert "studio:props" in b_dirs

    g_data = json.loads(gui_atlas.read_text(encoding="utf-8"))
    g_dirs = [s["source"] for s in g_data["sources"] if s.get("type") == "directory"]
    assert "studio:gui/sprites" in g_dirs


def test_shader_router_classification(tmp_path: Path):
    # 1. Modern by JSON format field
    j1 = tmp_path / "modern_format.json"
    j1.write_text(json.dumps({"format": 46, "vertex": "rendertype_solid"}), encoding="utf-8")
    assert ShaderRouter.is_modern_shader(j1) is True

    # 2. Legacy JSON
    j2 = tmp_path / "legacy_format.json"
    j2.write_text(json.dumps({"attributes": ["Position", "Color"]}), encoding="utf-8")
    assert ShaderRouter.is_modern_shader(j2) is False

    # 3. Modern by GLSL comment or tag
    v1 = tmp_path / "rendertype_text.vsh"
    v1.write_text("// Minecraft 1.21.4 modern shader\nvoid main() {}", encoding="utf-8")
    assert ShaderRouter.is_modern_shader(v1) is True

    # 4. Legacy GLSL
    v2 = tmp_path / "rendertype_lines.vsh"
    v2.write_text("#version 150\nvoid main() {}", encoding="utf-8")
    assert ShaderRouter.is_modern_shader(v2) is False

    # 5. Companion file induction
    prog_dir = tmp_path / "prog"
    prog_dir.mkdir()
    prog_vsh = prog_dir / "custom.vsh"
    prog_json = prog_dir / "custom.json"
    prog_vsh.write_text("#version 150\nvoid main() {}", encoding="utf-8")
    prog_json.write_text(json.dumps({"version": "1.21.4"}), encoding="utf-8")
    # prog_vsh has legacy glsl header, but companion prog_json declares 1.21.4
    assert ShaderRouter.is_modern_shader(prog_vsh) is True


def test_shader_router_resolve_destination(tmp_path: Path):
    out_dir = tmp_path / "out"
    legacy_file = tmp_path / "rendertype_legacy.vsh"
    legacy_file.write_text("#version 150", encoding="utf-8")

    modern_file = tmp_path / "rendertype_modern.json"
    modern_file.write_text(json.dumps({"min_format": 46}), encoding="utf-8")

    rel_root = Path("assets/minecraft/shaders/core")
    dest_legacy = ShaderRouter.resolve_destination(legacy_file, rel_root, out_dir)
    dest_modern = ShaderRouter.resolve_destination(modern_file, rel_root, out_dir)

    assert dest_legacy == out_dir / "assets" / "minecraft" / "shaders" / "core" / "rendertype_legacy.vsh"
    assert dest_modern == out_dir / "overlay_v1_21_4" / "assets" / "minecraft" / "shaders" / "core" / "rendertype_modern.json"


def test_shader_router_route_shaders_in_directory(tmp_path: Path):
    pack_dir = tmp_path / "pack"
    s_dir = pack_dir / "assets" / "minecraft" / "shaders" / "core"
    s_dir.mkdir(parents=True)

    # Legacy program
    (s_dir / "legacy_prog.vsh").write_text("#version 150", encoding="utf-8")
    (s_dir / "legacy_prog.json").write_text("{}", encoding="utf-8")

    # Modern program
    (s_dir / "modern_prog.vsh").write_text("#version 330\n// modern", encoding="utf-8")
    (s_dir / "modern_prog.json").write_text("{}", encoding="utf-8")

    routed = ShaderRouter.route_shaders_in_directory(pack_dir)
    assert len(routed) == 2  # modern_prog.vsh and modern_prog.json

    # Legacy files remain in root
    assert (s_dir / "legacy_prog.vsh").exists()
    assert (s_dir / "legacy_prog.json").exists()

    # Modern files moved to overlay_v1_21_4
    assert not (s_dir / "modern_prog.vsh").exists()
    assert not (s_dir / "modern_prog.json").exists()
    assert (pack_dir / "overlay_v1_21_4" / "assets" / "minecraft" / "shaders" / "core" / "modern_prog.vsh").exists()
    assert (pack_dir / "overlay_v1_21_4" / "assets" / "minecraft" / "shaders" / "core" / "modern_prog.json").exists()


def test_merge_layers_with_multi_overlay_and_shader_routing(tmp_path: Path):
    layer1 = tmp_path / "layer_legacy"
    layer2 = tmp_path / "layer_modern"
    out_dir = tmp_path / "out_pack"

    # Layer 1 has legacy shader and legacy item model
    (layer1 / "assets" / "minecraft" / "shaders" / "core").mkdir(parents=True)
    (layer1 / "assets" / "minecraft" / "shaders" / "core" / "rendertype_text.vsh").write_text(
        "#version 150 // legacy core shader", encoding="utf-8"
    )
    (layer1 / "assets" / "minecraft" / "models" / "item").mkdir(parents=True)
    (layer1 / "assets" / "minecraft" / "models" / "item" / "diamond_sword.json").write_text(
        json.dumps({
            "parent": "item/handheld",
            "overrides": [{"predicate": {"custom_model_data": 5001}, "model": "studio:item/flame_sword"}]
        }),
        encoding="utf-8"
    )

    # Layer 2 has 1.21.4 modern shader and modern item definition in overlay_v1_21_4
    (layer2 / "assets" / "minecraft" / "shaders" / "core").mkdir(parents=True)
    (layer2 / "assets" / "minecraft" / "shaders" / "core" / "rendertype_text.vsh").write_text(
        "#version 330 // 1.21.4 modern core shader", encoding="utf-8"
    )
    (layer2 / "overlay_v1_21_4" / "assets" / "minecraft" / "items").mkdir(parents=True)
    (layer2 / "overlay_v1_21_4" / "assets" / "minecraft" / "items" / "diamond_sword.json").write_text(
        json.dumps({
            "model": {
                "type": "minecraft:select",
                "property": "minecraft:custom_model_data",
                "cases": [{"when": "5002", "model": {"type": "minecraft:model", "model": "studio:item/frost_sword"}}]
            }
        }),
        encoding="utf-8"
    )

    summary = SemanticMerger.merge_layers_to_directory(
        ordered_source_dirs=[layer1, layer2],
        output_dir=out_dir,
        pack_format=34,
        max_inclusive=65
    )

    # 1. Shaders: Legacy remains in root assets, Modern is routed to overlay_v1_21_4
    root_shader = (out_dir / "assets" / "minecraft" / "shaders" / "core" / "rendertype_text.vsh").read_text(encoding="utf-8")
    overlay_shader = (out_dir / "overlay_v1_21_4" / "assets" / "minecraft" / "shaders" / "core" / "rendertype_text.vsh").read_text(encoding="utf-8")
    assert "#version 150" in root_shader
    assert "1.21.4 modern" in overlay_shader

    # 2. Dual Projection: overlay_v1_21_2 has both CMD 5001 and 5002
    v1_21_2_item = out_dir / "overlay_v1_21_2" / "assets" / "minecraft" / "items" / "diamond_sword.json"
    assert v1_21_2_item.exists()
    item_data = json.loads(v1_21_2_item.read_text(encoding="utf-8"))
    whens = [c["when"] for c in item_data["model"]["cases"]]
    assert "5001" in whens
    assert "5002" in whens

    # 3. Base models/item has both overrides
    root_model = json.loads((out_dir / "assets" / "minecraft" / "models" / "item" / "diamond_sword.json").read_text(encoding="utf-8"))
    cmds = [o["predicate"]["custom_model_data"] for o in root_model["overrides"]]
    assert 5001 in cmds
    assert 5002 in cmds


def test_semantic_merger_creative_assets():
    # 1. sounds.json merging
    base_sounds = {
        "prop.door": {
            "category": "blocks",
            "sounds": [{"name": "craftlab:door_1", "volume": 1.0}]
        }
    }
    overlay_sounds = {
        "prop.door": {
            "subtitle": "subtitles.door",
            "sounds": [{"name": "craftlab:door_2", "volume": 0.9}]
        },
        "prop.bell": {
            "category": "blocks",
            "sounds": ["craftlab:bell"]
        }
    }
    merged_sounds = SemanticMerger.merge_sounds_json(base_sounds, overlay_sounds)
    assert "prop.bell" in merged_sounds
    assert len(merged_sounds["prop.door"]["sounds"]) == 2
    assert merged_sounds["prop.door"]["subtitle"] == "subtitles.door"

    # 2. font/*.json merging
    base_font = {
        "providers": [
            {"type": "bitmap", "file": "craftlab:font/badge_vip.png", "chars": ["\uE001"]}
        ]
    }
    overlay_font = {
        "providers": [
            {"type": "bitmap", "file": "craftlab:font/badge_vip_new.png", "chars": ["\uE001"]},
            {"type": "bitmap", "file": "craftlab:font/badge_mvp.png", "chars": ["\uE002"]}
        ]
    }
    merged_font = SemanticMerger.merge_font_json(base_font, overlay_font)
    assert len(merged_font["providers"]) == 2
    # Overlay overrides matching \uE001
    assert merged_font["providers"][0]["file"] == "craftlab:font/badge_vip_new.png"

    # 3. particles/*.json merging
    base_part = {"textures": ["craftlab:particle/spark_0"]}
    overlay_part = {"textures": ["craftlab:particle/spark_1"]}
    merged_part = SemanticMerger.merge_particles_json(base_part, overlay_part)
    assert merged_part["textures"] == ["craftlab:particle/spark_0", "craftlab:particle/spark_1"]

    # 4. equipment/*.json merging
    base_eq = {"layers": [{"texture": "craftlab:armor_base", "type": "humanoid"}]}
    overlay_eq = {"layers": [{"texture": "craftlab:armor_upgraded", "type": "humanoid"}]}
    merged_eq = SemanticMerger.merge_equipment_json(base_eq, overlay_eq)
    assert merged_eq["layers"][0]["texture"] == "craftlab:armor_upgraded"


def test_equipment_models_staged_to_overlay(tmp_path: Path):
    layer1 = tmp_path / "layer1"
    layer1.mkdir()
    eq_file = layer1 / "assets" / "craftlab" / "models" / "equipment" / "paladin.json"
    eq_file.parent.mkdir(parents=True)
    eq_file.write_text('{"layers": [{"texture": "craftlab:paladin", "type": "humanoid"}]}', encoding="utf-8")

    out_dir = tmp_path / "out"
    summary = SemanticMerger.merge_layers_to_directory(
        ordered_source_dirs=[layer1],
        output_dir=out_dir,
        pack_format=34,
        max_inclusive=65
    )

    assert (out_dir / "assets" / "craftlab" / "models" / "equipment" / "paladin.json").exists()
    assert (out_dir / "overlay_v1_21_2" / "assets" / "craftlab" / "models" / "equipment" / "paladin.json").exists()
    assert summary["total_equipment"] == 1





