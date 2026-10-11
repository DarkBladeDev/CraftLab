import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from main import app
from app.core.database import init_db
from tests.test_sound_events import create_mock_vorbis_ogg
from app.domain.glyphs import delete_glyph
from app.domain.workspace import ensure_workspace_initialized, get_default_workspace_dir


@pytest.mark.asyncio
async def test_creative_api_endpoints():
    await init_db()
    workspace = ensure_workspace_initialized()
    # Clean up test glyph if left from previous runs
    delete_glyph(workspace, "E001", namespace="craftlab")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # --- 1. Glyphs ---
        # Register glyph
        glyph_req = {
            "id": "badge_vip",
            "file": "craftlab:font/badge_vip.png",
            "hex": "E001",
            "height": 8,
            "ascent": 7,
            "namespace": "craftlab"
        }
        res = await client.post("/api/v1/assets/creative/glyphs", json=glyph_req)
        assert res.status_code == 200
        data = res.json()
        assert data["hex"] == "E001"
        assert data["character"] == "\uE001"

        # Validate hex endpoint
        val_res = await client.get("/api/v1/assets/creative/glyphs/validate-hex?hex=E001")
        assert val_res.status_code == 200
        assert val_res.json()["valid"] is False  # Collision!

        val_res_free = await client.get("/api/v1/assets/creative/glyphs/validate-hex?hex=E002")
        assert val_res_free.status_code == 200
        assert val_res_free.json()["valid"] is True

        # List glyphs
        list_g = await client.get("/api/v1/assets/creative/glyphs")
        assert list_g.status_code == 200
        assert list_g.json()["count"] >= 1

        # Delete glyph
        del_g = await client.delete("/api/v1/assets/creative/glyphs/E001")
        assert del_g.status_code == 200

        # --- 2. Equipment Models ---
        eq_req = {
            "id": "paladin_chest",
            "layers": [
                {"texture": "craftlab:paladin", "type": "humanoid"},
                {"texture": "craftlab:paladin_overlay", "dyeable": True}
            ],
            "namespace": "craftlab"
        }
        res_eq = await client.post("/api/v1/assets/creative/equipment", json=eq_req)
        assert res_eq.status_code == 200
        assert res_eq.json()["id"] == "paladin_chest"

        get_eq = await client.get("/api/v1/assets/creative/equipment/paladin_chest")
        assert get_eq.status_code == 200
        assert len(get_eq.json()["layers"]) == 2

        list_eq = await client.get("/api/v1/assets/creative/equipment")
        assert list_eq.status_code == 200
        assert len(list_eq.json()) >= 1

        del_eq = await client.delete("/api/v1/assets/creative/equipment/paladin_chest")
        assert del_eq.status_code == 200

        # --- 3. Sound Events & Probe ---
        sound_req = {
            "id": "prop.door.creak",
            "category": "blocks",
            "subtitle": "subtitles.craftlab.door_creak",
            "sounds": [
                {"name": "craftlab:door_1", "volume": 1.0, "pitch": 1.0}
            ],
            "namespace": "craftlab"
        }
        res_snd = await client.post("/api/v1/assets/creative/sounds", json=sound_req)
        assert res_snd.status_code == 200

        list_snd = await client.get("/api/v1/assets/creative/sounds")
        assert list_snd.status_code == 200
        assert any(s["id"] == "prop.door.creak" for s in list_snd.json())

        # Test audio probe
        sounds_dir = workspace / "assets" / "craftlab" / "sounds"
        sounds_dir.mkdir(parents=True, exist_ok=True)
        test_audio = sounds_dir / "stereo_test.ogg"
        test_audio.write_bytes(create_mock_vorbis_ogg(channels=2, sample_rate=44100))

        probe_res = await client.post("/api/v1/assets/creative/sounds/probe", json={"relative_path": "assets/craftlab/sounds/stereo_test.ogg"})
        assert probe_res.status_code == 200
        assert probe_res.json()["channels"] == 2
        assert probe_res.json()["is_mono"] is False

        del_snd = await client.delete("/api/v1/assets/creative/sounds/prop.door.creak")
        assert del_snd.status_code == 200

        # --- 4. Particles ---
        part_req = {
            "id": "magic_spark",
            "textures": ["craftlab:particle/spark"],
            "emitter": {"speed": 4, "spread": 5},
            "namespace": "craftlab"
        }
        res_part = await client.post("/api/v1/assets/creative/particles", json=part_req)
        assert res_part.status_code == 200

        get_part = await client.get("/api/v1/assets/creative/particles/magic_spark")
        assert get_part.status_code == 200
        assert get_part.json()["id"] == "magic_spark"

        list_part = await client.get("/api/v1/assets/creative/particles")
        assert list_part.status_code == 200
        assert any(p["id"] == "magic_spark" for p in list_part.json())

        del_part = await client.delete("/api/v1/assets/creative/particles/magic_spark")
        assert del_part.status_code == 200

        if test_audio.exists():
            test_audio.unlink()

