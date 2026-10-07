import io
import json
import zipfile
import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from app.core.database import init_db, AsyncSessionLocal
from sqlalchemy import delete
from app.models.entities import ItemModel, TargetModel


@pytest.mark.asyncio
async def test_packs_api_full_workflow():
    await init_db()

    # Clean up test records
    async with AsyncSessionLocal() as session:
        await session.execute(delete(ItemModel).where(ItemModel.id.in_(["emerald_rapier", "colliding_blade"])))
        await session.execute(delete(TargetModel).where(TargetModel.id == "target-pack-test"))
        await session.commit()

        target = TargetModel(
            id="target-pack-test",
            name="Test Paper Server",
            secret="test-secret"
        )
        session.add(target)

        item = ItemModel(
            id="emerald_rapier",
            material="DIAMOND_SWORD",
            display_name="Emerald Rapier",
            custom_model_data=8801
        )
        session.add(item)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Preflight check
        resp_pre = await client.post("/api/v1/packs/preflight?target_id=target-pack-test")
        assert resp_pre.status_code == 200
        pre_data = resp_pre.json()
        assert pre_data["is_valid"] is True
        assert len(pre_data["conflicts"]) == 0

        # 2. Upload third-party source zip
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("pack.mcmeta", json.dumps({"pack": {"pack_format": 34, "description": "Base Pack"}}))
            zf.writestr("assets/minecraft/textures/item/base_dagger.png", b"BASE_PNG")
        zip_bytes = zip_buf.getvalue()

        files = {"file": ("base_pack.zip", zip_bytes, "application/zip")}
        data = {
            "name": "Base Server Pack",
            "layer_priority": "10",
            "target_id": "target-pack-test"
        }
        resp_upload = await client.post("/api/v1/packs/sources/upload", files=files, data=data)
        assert resp_upload.status_code == 200
        upload_data = resp_upload.json()
        assert "id" in upload_data
        assert upload_data["name"] == "Base Server Pack"
        source_id = upload_data["id"]

        # 3. List sources
        resp_list = await client.get("/api/v1/packs/sources?target_id=target-pack-test")
        assert resp_list.status_code == 200
        sources_list = resp_list.json()
        assert any(s["id"] == source_id for s in sources_list)

        # 4. Build pack
        build_payload = {
            "target_id": "target-pack-test",
            "pack_format": 34,
            "description": "Test Compiled Pack"
        }
        resp_build = await client.post("/api/v1/packs/build", json=build_payload)
        assert resp_build.status_code == 200
        build_data = resp_build.json()
        assert "sha1_hash" in build_data
        assert len(build_data["sha1_hash"]) == 40
        assert build_data["file_size"] > 0
        sha1_hash = build_data["sha1_hash"]

        # 5. Download pack
        resp_dl = await client.get("/api/v1/packs/target-pack-test/download")
        assert resp_dl.status_code == 200
        assert resp_dl.headers.get("etag") == f'"{sha1_hash}"'
        assert "application/zip" in resp_dl.headers.get("content-type")
        assert len(resp_dl.content) == build_data["file_size"]

        # 6. Conditional GET with matching ETag (304 Not Modified)
        resp_304 = await client.get(
            "/api/v1/packs/target-pack-test/download",
            headers={"if-none-match": sha1_hash}
        )
        assert resp_304.status_code == 304

        # 7. Preflight collision blocks build
        async with AsyncSessionLocal() as session:
            colliding_item = ItemModel(
                id="colliding_blade",
                material="DIAMOND_SWORD",
                display_name="Colliding Blade",
                custom_model_data=8801  # Same CMD 8801!
            )
            session.add(colliding_item)
            await session.commit()

        # Build attempt without force should return 409
        resp_build_conflict = await client.post("/api/v1/packs/build", json=build_payload)
        assert resp_build_conflict.status_code == 409
        conflict_data = resp_build_conflict.json()
        assert conflict_data["is_valid"] is False
        assert len(conflict_data["conflicts"]) == 1

        # Delete source cleanup
        resp_del = await client.delete(f"/api/v1/packs/sources/{source_id}")
        assert resp_del.status_code == 200


@pytest.mark.asyncio
async def test_packs_api_custom_item_model_and_blocks_build():
    await init_db()

    async with AsyncSessionLocal() as session:
        from app.models.entities import BlockModel, ItemModel, TargetModel
        # Clean up existing test items if any
        await session.execute(delete(BlockModel).where(BlockModel.id == "custom_chair_block"))
        await session.execute(delete(ItemModel).where(ItemModel.id == "custom_chair_item"))
        await session.execute(delete(TargetModel).where(TargetModel.id == "target-model-test"))
        await session.commit()

        target = TargetModel(
            id="target-model-test",
            name="Model Test Server",
            secret="model-secret"
        )
        session.add(target)

        item = ItemModel(
            id="custom_chair_item",
            material="WHITE_WOOL",
            display_name="Custom Chair",
            custom_model_data=20001,
            item_model="minecraft:item/test_chair"
        )
        session.add(item)

        block = BlockModel(
            id="custom_chair_block",
            display_name="Custom Chair Prop",
            mode="display_prop",
            item_model="minecraft:item/test_chair",
            drop_item_id="custom_chair_item"
        )
        session.add(block)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        build_payload = {
            "target_id": "target-model-test",
            "pack_format": 34,
            "description": "Custom Model Pack",
            "force": True
        }
        resp_build = await client.post("/api/v1/packs/build", json=build_payload)
        assert resp_build.status_code == 200

        resp_dl = await client.get("/api/v1/packs/target-model-test/download")
        assert resp_dl.status_code == 200

        with zipfile.ZipFile(io.BytesIO(resp_dl.content), "r") as zf:
            namelist = zf.namelist()
            # 1. pack.mcmeta format compliance (> 64 requires min_format and max_format)
            mcmeta = json.loads(zf.read("pack.mcmeta").decode("utf-8"))
            assert mcmeta["pack"]["min_format"] == 34
            assert mcmeta["pack"]["max_format"] == 65
            assert mcmeta["overlays"]["entries"][0]["min_format"] == 42
            assert mcmeta["overlays"]["entries"][0]["max_format"] == 65

            # 2. Modern Item Definitions in overlay and base
            assert "overlay_v1_21_2/assets/minecraft/items/item/test_chair.json" in namelist
            assert "overlay_v1_21_2/assets/minecraft/items/test_chair.json" in namelist
            assert "assets/minecraft/items/item/test_chair.json" in namelist
            assert "assets/minecraft/items/test_chair.json" in namelist

            item_def = json.loads(zf.read("overlay_v1_21_2/assets/minecraft/items/item/test_chair.json").decode("utf-8"))
            assert item_def["model"]["type"] == "minecraft:model"
            assert item_def["model"]["model"] == "minecraft:item/test_chair"

            # 3. Legacy base override points to custom model, NOT dummy studio model
            white_wool = json.loads(zf.read("assets/minecraft/models/item/white_wool.json").decode("utf-8"))
            assert any(
                ov.get("predicate", {}).get("custom_model_data") == 20001 and
                ov.get("model") == "minecraft:item/test_chair"
                for ov in white_wool["overrides"]
            )

