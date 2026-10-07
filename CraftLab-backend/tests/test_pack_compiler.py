import json
import zipfile
from pathlib import Path
from app.domain.pack_compiler import DeterministicPackCompiler


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

