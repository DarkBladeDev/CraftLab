import json
import pytest
from pathlib import Path
from app.domain.glyphs import (
    PUA_MIN,
    PUA_MAX,
    normalize_hex,
    is_valid_pua_code,
    allocate_next_pua,
    validate_pua_hex,
    register_glyph,
    scan_registered_glyphs,
    delete_glyph,
)


def test_pua_hex_normalization_and_validation():
    assert normalize_hex("e001") == "E001"
    assert normalize_hex("\\uE005") == "E005"
    assert normalize_hex("U+e12a") == "E12A"

    assert is_valid_pua_code(0xE000) is True
    assert is_valid_pua_code(0xF8FF) is True
    assert is_valid_pua_code(0xDFFF) is False
    assert is_valid_pua_code(0xF900) is False

    used = {"E001", "E002"}
    valid, res = validate_pua_hex("E003", used)
    assert valid is True
    assert res == "E003"

    valid_collision, err = validate_pua_hex("E001", used)
    assert valid_collision is False
    assert "Collision detected" in err

    valid_range, err = validate_pua_hex("0041", used)  # ASCII 'A'
    assert valid_range is False
    assert "outside Minecraft PUA range" in err


def test_allocate_next_pua():
    used = {"E001", "E002", "E003"}
    allocated = allocate_next_pua(used, start_hex="E001")
    assert allocated == "E004"


def test_register_scan_and_delete_glyphs(tmp_path: Path):
    workspace_dir = tmp_path / "workspace"

    # Register glyph 1 (auto-allocated)
    g1 = register_glyph(
        workspace_dir=workspace_dir,
        glyph_id="badge_vip",
        file_ref="craftlab:font/badge_vip.png",
        height=8,
        ascent=7,
        namespace="craftlab"
    )
    assert g1["hex"] == "E001"
    assert g1["character"] == "\uE001"
    assert g1["placeholder"] == "%craftlab_glyph_badge_vip%"

    # Register glyph 2 (custom hex override in custom namespace)
    g2 = register_glyph(
        workspace_dir=workspace_dir,
        glyph_id="badge_mvp",
        file_ref="ranks:font/badge_mvp.png",
        hex_code="E005",
        height=9,
        ascent=8,
        namespace="ranks"
    )
    assert g2["hex"] == "E005"
    assert g2["placeholder"] == "%craftlab_glyph_ranks:badge_mvp%"

    # Scan
    glyphs = scan_registered_glyphs(workspace_dir)
    assert len(glyphs) == 2
    hexes = {g["hex"] for g in glyphs}
    assert hexes == {"E001", "E005"}
    by_hex = {g["hex"]: g for g in glyphs}
    assert by_hex["E001"]["placeholder"] == "%craftlab_glyph_badge_vip%"
    assert by_hex["E005"]["placeholder"] == "%craftlab_glyph_ranks:badge_mvp%"

    # Attempt duplicate hex registration should fail
    with pytest.raises(ValueError, match="Collision detected"):
        register_glyph(
            workspace_dir=workspace_dir,
            glyph_id="badge_staff",
            file_ref="craftlab:font/badge_staff.png",
            hex_code="E001",
            namespace="craftlab"
        )

    # Delete glyph 1
    deleted = delete_glyph(workspace_dir, "E001")
    assert deleted is True

    # Scan again
    glyphs_after = scan_registered_glyphs(workspace_dir)
    assert len(glyphs_after) == 1
    assert glyphs_after[0]["hex"] == "E005"
