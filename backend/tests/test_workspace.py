import os
import io
import json
import struct
import shutil
import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from main import app
from app.core.database import init_db
from app.domain.workspace import (
    ensure_workspace_initialized,
    validate_minecraft_identifier,
    safe_resolve_workspace_path,
    resolve_resource_location,
    parse_png_dimensions,
    build_workspace_tree,
    get_workspace_metadata,
)


def create_minimal_png(width: int, height: int) -> bytes:
    """Creates a minimal valid PNG header with IHDR chunk."""
    header = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    ihdr_chunk = struct.pack(">I", len(ihdr_data)) + b'IHDR' + ihdr_data + b'\x00\x00\x00\x00'
    return header + ihdr_chunk


def test_validate_minecraft_identifier():
    assert validate_minecraft_identifier("ruby_sword") is True
    assert validate_minecraft_identifier("custom.pack-12") is True
    assert validate_minecraft_identifier("items") is True
    assert validate_minecraft_identifier("Ruby_Sword") is False
    assert validate_minecraft_identifier("ruby sword") is False
    assert validate_minecraft_identifier("ruby/sword") is False
    assert validate_minecraft_identifier("") is False


def test_resolve_resource_location():
    # Texture
    t = resolve_resource_location("assets/craftlab/textures/item/ruby_dagger.png")
    assert t["category"] == "texture"
    assert t["namespace"] == "craftlab"
    assert t["resource_location"] == "craftlab:item/ruby_dagger"
    assert t["item_model_component"] == 'item_model="craftlab:item/ruby_dagger"'
    assert t["json_layer_reference"] == '"layer0": "craftlab:item/ruby_dagger"'

    # Model
    m = resolve_resource_location("assets/craftlab/models/item/ruby_dagger.json")
    assert m["category"] == "model"
    assert m["resource_location"] == "craftlab:item/ruby_dagger"

    # Modern Item Definition 1.21.2+
    i = resolve_resource_location("assets/craftlab/items/ruby_dagger.json")
    assert i["category"] == "item_definition"
    assert i["resource_location"] == "craftlab:ruby_dagger"

    # Sound
    s = resolve_resource_location("assets/craftlab/sounds/weapon/slash.ogg")
    assert s["category"] == "sound"
    assert s["resource_location"] == "craftlab:weapon/slash"

    # Manifest
    mf = resolve_resource_location("pack.mcmeta")
    assert mf["category"] == "manifest"
    assert mf["resource_location"] is None


def test_parse_png_dimensions():
    png_data = create_minimal_png(16, 32)
    dims = parse_png_dimensions(png_data)
    assert dims == (16, 32)

    invalid_data = b"not a png at all"
    assert parse_png_dimensions(invalid_data) is None


def test_safe_resolve_and_traversal(tmp_path):
    ws = tmp_path / "workspace"
    ws.mkdir()

    resolved = safe_resolve_workspace_path(ws, "assets/minecraft/textures")
    assert resolved == ws / "assets" / "minecraft" / "textures"

    with pytest.raises(ValueError):
        safe_resolve_workspace_path(ws, "../outside.txt")

    with pytest.raises(ValueError):
        safe_resolve_workspace_path(ws, "assets/../../secret")


def test_workspace_auto_initialization(tmp_path):
    ws = tmp_path / "workspace_test"
    assert not ws.exists()

    init_path = ensure_workspace_initialized(ws)
    assert init_path == ws
    assert (ws / "pack.mcmeta").exists()
    assert (ws / "assets" / "minecraft" / "textures" / "item").exists()
    assert (ws / "assets" / "minecraft" / "models" / "item").exists()
    assert (ws / "assets" / "minecraft" / "items").exists()

    data = json.loads((ws / "pack.mcmeta").read_text(encoding="utf-8"))
    assert data["pack"]["pack_format"] == 34
    assert data["pack"]["supported_formats"]["max_inclusive"] == 65


@pytest.mark.asyncio
async def test_workspace_api_full_crud_and_metadata(tmp_path, monkeypatch):
    test_ws = tmp_path / "data_packs" / "workspace"
    monkeypatch.setenv("MCP_DATA_DIR", str(tmp_path / "data_packs"))

    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Tree auto-initialization
        r_tree = await client.get("/api/v1/packs/workspace/tree")
        assert r_tree.status_code == 200
        tree = r_tree.json()
        assert tree["type"] == "directory"
        assert any(c["name"] == "pack.mcmeta" for c in tree["children"])

        # 2. Create directory with valid and invalid names
        r_dir_invalid = await client.post(
            "/api/v1/packs/workspace/directory",
            json={"path": "assets/CraftLab/Textures"}
        )
        assert r_dir_invalid.status_code == 400

        r_dir_valid = await client.post(
            "/api/v1/packs/workspace/directory",
            json={"path": "assets/craftlab/textures/item"}
        )
        assert r_dir_valid.status_code == 200
        assert r_dir_valid.json()["success"] is True

        # 3. Upload a texture PNG
        png_bytes = create_minimal_png(16, 16)
        r_up = await client.post(
            "/api/v1/packs/workspace/upload",
            data={"directory": "assets/craftlab/textures/item"},
            files={"file": ("ruby_sword.png", png_bytes, "image/png")}
        )
        assert r_up.status_code == 200
        assert r_up.json()["filename"] == "ruby_sword.png"

        # 4. Write a JSON model referencing the texture
        model_content = json.dumps({
            "parent": "minecraft:item/handheld",
            "textures": {
                "layer0": "craftlab:item/ruby_sword"
            }
        }, indent=2)

        r_write = await client.put(
            "/api/v1/packs/workspace/file",
            json={
                "path": "assets/craftlab/models/item/ruby_sword.json",
                "content": model_content
            }
        )
        assert r_write.status_code == 200
        assert r_write.json()["success"] is True

        # 5. Invalid JSON writing rejected
        r_bad_json = await client.put(
            "/api/v1/packs/workspace/file",
            json={
                "path": "assets/craftlab/models/item/bad.json",
                "content": '{"broken": missing_quote}'
            }
        )
        assert r_bad_json.status_code == 400

        # 6. Metadata inspection on the texture
        r_meta_tex = await client.get(
            "/api/v1/packs/workspace/metadata?path=assets/craftlab/textures/item/ruby_sword.png"
        )
        assert r_meta_tex.status_code == 200
        meta_tex = r_meta_tex.json()
        assert meta_tex["resource_location"] == "craftlab:item/ruby_sword"
        assert meta_tex["diagnostics"]["dimensions"] == {"width": 16, "height": 16}
        assert meta_tex["diagnostics"]["is_square"] is True
        assert "assets/craftlab/models/item/ruby_sword.json" in meta_tex["diagnostics"]["referenced_by_models"]

        # 7. Metadata inspection on the model
        r_meta_model = await client.get(
            "/api/v1/packs/workspace/metadata?path=assets/craftlab/models/item/ruby_sword.json"
        )
        assert r_meta_model.status_code == 200
        meta_model = r_meta_model.json()
        assert meta_model["resource_location"] == "craftlab:item/ruby_sword"
        assert len(meta_model["diagnostics"]["missing_textures"]) == 0

        # 8. Test compile pack merges workspace files
        r_build = await client.post(
            "/api/v1/packs/build",
            json={"target_id": "test-ws-build", "pack_format": 34, "force": True}
        )
        assert r_build.status_code == 200
        build_data = r_build.json()
        assert "pack_id" in build_data

        # 9. Delete file
        r_del = await client.delete(
            "/api/v1/packs/workspace/file?path=assets/craftlab/textures/item/ruby_sword.png"
        )
        assert r_del.status_code == 200
        assert r_del.json()["success"] is True
