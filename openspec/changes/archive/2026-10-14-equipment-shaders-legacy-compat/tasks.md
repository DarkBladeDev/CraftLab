# Tasks: Equipment Shaders Legacy Compatibility (< 1.21.2)

## 1. Core Shader Assets & Atlas Stitcher

- [x] 1.1 Embed adapted LessFancyPants GLSL shader templates (`rendertype_armor_cutout_no_cull.json`, `.vsh`, `.fsh`) in `CraftLab-backend/app/domain/shaders/` and verify templates compile cleanly.
- [x] 1.2 Implement `ArmorAtlasStitcher` in `CraftLab-backend/app/domain/pack_merger.py` to scan equipment models, stitch `leather_layer_1.png` and `leather_layer_2.png` vertically using Pillow, and verify synthesized image dimensions match `64 x (32 * total_layers)`.
- [x] 1.3 Update `pack_merger.py` to inject the LessFancyPants core shader into root assets with dynamically calculated `#define TOTAL_LAYERS`, ensuring `ShaderRouter` excludes legacy shaders from `overlay_v1_21_4`.
- [x] 1.4 Add `compatibility_profile` (`modern_native`, `hybrid_shaders`, `hybrid_trims`) to workspace manifest parsing and pack build options in `CraftLab-backend/app/domain/pack_compiler.py`.

## 2. Equipment Model Indexing & Item Studio Projection

- [x] 2.1 Implement deterministic 1-based layer indexing and 24-bit RGB color allocation (`id -> hex/rgb`) in `CraftLab-backend/app/domain/equipment.py`.
- [x] 2.2 Expose legacy shader metadata (assigned ID, RGB hex code, and atlas position) on the creative equipment REST endpoints in `CraftLab-backend/app/api/creative.py`.
- [x] 2.3 Implement hybrid equipment projection in `CraftLab-backend/app/domain/items.py` that auto-derives `custom_model_data`, 24-bit RGB `dyed_color`, `LEATHER_*` base material fallback, and compensating armor defense attributes for equippable items in `hybrid_shaders` mode.

## 3. Frontend UI & Diagnostics

- [x] 3.1 Add a compatibility profile selector (`Modern Native`, `Hybrid Shaders`, `Hybrid Trims`) in Workspace / Resource Pack configuration modals in `CraftLab-frontend`.
- [x] 3.2 Add a Multi-Version Diagnostics badge in Creative Assets Lab (`CreativeView.tsx` / Equipment editor) showing assigned shader ID, RGB hex tint, and atlas status alongside canonical `asset_id`.
- [x] 3.3 Enhance Item Studio (`ItemStudioView.tsx`) to show dual-compatibility badges ("1.21.2+ Native" / "< 1.21.2 Shader Fallback") and a 1-click action to populate legacy leather fallback attributes.

## 4. Paper Plugin Adapter Fallback

- [x] 4.1 Update `EquippableComponentApplier.java` in `CraftLab-plugin` to detect when `getEquippable()` is unsupported and apply leather `dyed_color` (`setColor`), `CustomModelData`, and compensating armor attribute modifiers.
- [x] 4.2 Verify in `Paper121ItemAdapter.java` that hybrid leather items correctly append `ItemFlag.HIDE_DYE` to prevent raw dye metadata from rendering in item tooltips.

## 5. End-to-End Verification & Automated Testing

- [x] 5.1 Write pytest test suite `tests/test_armor_atlas_stitcher.py` covering vertical atlas assembly, layer indexing, and shader injection across modern vs hybrid profiles.
- [x] 5.2 Write pytest test suite `tests/test_hybrid_equipment_items.py` verifying item model dual-projection, attribute compensation, and `pack_merger.py` compilation integrity.
- [x] 5.3 Execute full test suite `pytest` across backend and `npm run test` / `npm run build` in frontend to guarantee zero regression.
