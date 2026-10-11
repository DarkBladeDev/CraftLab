import json
import zipfile
from pathlib import Path
from app.domain.pack_compiler import DeterministicPackCompiler
from app.domain.pack_merger import SemanticMerger


def test_deterministic_zip_reproducibility(tmp_path: Path):
    source_dir = tmp_path / "pack_src"
    source_dir.mkdir()

    # Add several files in subdirectories
    (source_dir / "pack.mcmeta").write_text(json.dumps({"pack": {"pack_format": 34}}), encoding="utf-8")
    textures_dir = source_dir / "assets" / "minecraft" / "textures" / "item"
    textures_dir.mkdir(parents=True)
    (textures_dir / "b_texture.png").write_bytes(b"TEXTURE_B")
    (textures_dir / "a_texture.png").write_bytes(b"TEXTURE_A")

    zip1_path = tmp_path / "build1.zip"
    zip2_path = tmp_path / "build2.zip"

    sha1_1, size1 = DeterministicPackCompiler.compile_directory_to_zip(source_dir, zip1_path)
    sha1_2, size2 = DeterministicPackCompiler.compile_directory_to_zip(source_dir, zip2_path)

    assert len(sha1_1) == 40
    assert sha1_1 == sha1_2
    assert size1 == size2
    # Verify bit-for-bit exact binary equality
    assert zip1_path.read_bytes() == zip2_path.read_bytes()

    # Verify that changing content alters the SHA-1
    (textures_dir / "b_texture.png").write_bytes(b"TEXTURE_B_MODIFIED")
    zip3_path = tmp_path / "build3.zip"
    sha1_3, size3 = DeterministicPackCompiler.compile_directory_to_zip(source_dir, zip3_path)
    assert sha1_3 != sha1_1


def test_zip_contents_and_normalized_timestamp(tmp_path: Path):
    source_dir = tmp_path / "pack_src"
    source_dir.mkdir()
    (source_dir / "pack.mcmeta").write_text("{}", encoding="utf-8")

    out_zip = tmp_path / "out.zip"
    sha1, size = DeterministicPackCompiler.compile_directory_to_zip(source_dir, out_zip)

    with zipfile.ZipFile(out_zip, "r") as zf:
        infolist = zf.infolist()
        assert len(infolist) == 1
        assert infolist[0].filename == "pack.mcmeta"
        assert infolist[0].date_time == DeterministicPackCompiler.FIXED_DATE_TIME


def test_write_multiversion_mcmeta_and_compile_with_overlays(tmp_path: Path):
    source_dir = tmp_path / "multi_pack_src"
    source_dir.mkdir()

    mcmeta_file = DeterministicPackCompiler.write_multiversion_mcmeta(source_dir)
    assert mcmeta_file.exists()
    data = json.loads(mcmeta_file.read_text(encoding="utf-8"))
    assert data["pack"]["pack_format"] == 34
    assert data["pack"]["supported_formats"]["min_inclusive"] == 34
    assert data["pack"]["supported_formats"]["max_inclusive"] == 65
    assert data["overlays"]["entries"][0]["directory"] == "overlay_v1_21_2"
    assert data["overlays"]["entries"][1]["directory"] == "overlay_v1_21_4"

    # Test custom max_inclusive
    custom_mcmeta = DeterministicPackCompiler.generate_multiversion_mcmeta(pack_format=34, max_inclusive=72)
    assert custom_mcmeta["pack"]["supported_formats"]["max_inclusive"] == 72
    assert custom_mcmeta["overlays"]["entries"][0]["formats"]["max_inclusive"] == 72
    assert custom_mcmeta["overlays"]["entries"][1]["formats"]["max_inclusive"] == 72

    # Add overlay item
    overlay_item_dir = source_dir / "overlays" / "overlay_v1_21_2" / "assets" / "minecraft" / "items"
    overlay_item_dir.mkdir(parents=True)
    (overlay_item_dir / "diamond_sword.json").write_text("{}", encoding="utf-8")

    out_zip = tmp_path / "multi_out.zip"
    sha1, size = DeterministicPackCompiler.compile_directory_to_zip(source_dir, out_zip)
    assert len(sha1) == 40
    assert size > 0

    with zipfile.ZipFile(out_zip, "r") as zf:
        namelist = zf.namelist()
        assert "pack.mcmeta" in namelist
        assert "overlays/overlay_v1_21_2/assets/minecraft/items/diamond_sword.json" in namelist


def test_end_to_end_pack_compilation_with_models_shaders_and_atlases(tmp_path: Path):
    layer1 = tmp_path / "layer1"
    layer2 = tmp_path / "layer2"
    merged_dir = tmp_path / "merged_out"

    # Layer 1: legacy model referencing studio:item/flame_sword, custom model, legacy core shader, texture
    m1_dir = layer1 / "assets" / "minecraft" / "models" / "item"
    m1_dir.mkdir(parents=True)
    (m1_dir / "diamond_sword.json").write_text(json.dumps({
        "parent": "item/handheld",
        "overrides": [{"predicate": {"custom_model_data": 7001}, "model": "studio:item/flame_sword"}]
    }), encoding="utf-8")

    m2_dir = layer1 / "assets" / "studio" / "models" / "item"
    m2_dir.mkdir(parents=True)
    (m2_dir / "flame_sword.json").write_text(json.dumps({
        "parent": "item/handheld",
        "textures": {"layer0": "studio:item/flame_sword"}
    }), encoding="utf-8")

    tex_dir = layer1 / "assets" / "studio" / "textures" / "item"
    tex_dir.mkdir(parents=True)
    (tex_dir / "flame_sword.png").write_bytes(b"PNG_FLAME")

    sh_dir1 = layer1 / "assets" / "minecraft" / "shaders" / "core"
    sh_dir1.mkdir(parents=True)
    (sh_dir1 / "rendertype_text.vsh").write_text("#version 150\nvoid main() {}", encoding="utf-8")

    # Layer 2: modern 1.21.4 core shader, GUI sprite
    sh_dir2 = layer2 / "assets" / "minecraft" / "shaders" / "core"
    sh_dir2.mkdir(parents=True)
    (sh_dir2 / "rendertype_text.vsh").write_text("// 1.21.4 modern shader\nvoid main() {}", encoding="utf-8")

    gui_dir = layer2 / "assets" / "studio" / "textures" / "gui" / "sprites"
    gui_dir.mkdir(parents=True)
    (gui_dir / "mana_bar.png").write_bytes(b"PNG_MANA")

    # Merge layers to directory with custom operator max_inclusive=75
    summary = SemanticMerger.merge_layers_to_directory(
        ordered_source_dirs=[layer1, layer2],
        output_dir=merged_dir,
        pack_format=34,
        max_inclusive=75,
        description="CraftLab Unified Monorepo Pack"
    )

    assert summary["pack_format"] == 34
    assert summary["is_hybrid_multiversion"] is True

    # Compile deterministically twice to verify SHA-1 byte-for-byte reproducibility
    zip1_path = tmp_path / "release_build1.zip"
    zip2_path = tmp_path / "release_build2.zip"

    sha1_1, size1 = DeterministicPackCompiler.compile_directory_to_zip(merged_dir, zip1_path)
    sha1_2, size2 = DeterministicPackCompiler.compile_directory_to_zip(merged_dir, zip2_path)

    assert sha1_1 == sha1_2
    assert size1 == size2
    assert zip1_path.read_bytes() == zip2_path.read_bytes()

    # Inspect zip contents
    with zipfile.ZipFile(zip1_path, "r") as zf:
        names = zf.namelist()
        assert "pack.mcmeta" in names
        assert "assets/minecraft/atlases/blocks.json" in names
        assert "assets/minecraft/atlases/gui.json" in names
        assert "assets/minecraft/shaders/core/rendertype_text.vsh" in names
        assert "overlay_v1_21_4/assets/minecraft/shaders/core/rendertype_text.vsh" in names
        assert "overlay_v1_21_2/assets/minecraft/items/diamond_sword.json" in names
        assert "assets/minecraft/models/item/diamond_sword.json" in names

        # Inspect pack.mcmeta
        mcmeta_data = json.loads(zf.read("pack.mcmeta").decode("utf-8"))
        assert mcmeta_data["pack"]["supported_formats"]["max_inclusive"] == 75
        entries = mcmeta_data["overlays"]["entries"]
        assert len(entries) == 2
        assert entries[0]["directory"] == "overlay_v1_21_2"
        assert entries[0]["formats"]["max_inclusive"] == 75
        assert entries[1]["directory"] == "overlay_v1_21_4"
        assert entries[1]["formats"]["max_inclusive"] == 75

        # Inspect atlases
        blocks_atlas = json.loads(zf.read("assets/minecraft/atlases/blocks.json").decode("utf-8"))
        b_sources = [s["source"] for s in blocks_atlas["sources"] if s.get("type") == "directory"]
        assert "studio:item" in b_sources

        gui_atlas = json.loads(zf.read("assets/minecraft/atlases/gui.json").decode("utf-8"))
        g_sources = [s["source"] for s in gui_atlas["sources"] if s.get("type") == "directory"]
        assert "studio:gui/sprites" in g_sources

        # Inspect shaders
        legacy_sh = zf.read("assets/minecraft/shaders/core/rendertype_text.vsh").decode("utf-8")
        modern_sh = zf.read("overlay_v1_21_4/assets/minecraft/shaders/core/rendertype_text.vsh").decode("utf-8")
        assert "#version 150" in legacy_sh
        assert "1.21.4 modern" in modern_sh



