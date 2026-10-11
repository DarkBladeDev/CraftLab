# Tasks

## 1. Pack Manifest Inspector & Ingestion Normalizer

- [x] 1.1 Implement `PackManifestInspector` in `CraftLab-backend/app/domain/pack_merger.py` to parse `pack.mcmeta`, extract format ranges from `overlays.entries`, and map external overlay directory paths into canonical targets (`root`, `overlay_v1_21_2`, `overlay_v1_21_4`). Verify with unit test parsing external manifest structures.
- [x] 1.2 Integrate `PackManifestInspector` into external zip archive ingestion in `CraftLab-backend/app/domain/pack_sources.py` and `CraftLab-backend/app/api/packs.py` to normalize extracted overlay structures during layer staging. Verify with test ingesting a pack with non-standard overlay folders.

## 2. Multi-Version Cumulative Overlay Matrix & Compiler

- [x] 2.1 Update `DeterministicPackCompiler.generate_multiversion_mcmeta` and `write_multiversion_mcmeta` in `CraftLab-backend/app/domain/pack_compiler.py` to support dynamic `max_inclusive` and generate cumulative overlay entries (`overlay_v1_21_2` for formats 42..max and `overlay_v1_21_4` for formats 46..max). Verify with unit tests in `CraftLab-backend/tests/test_pack_compiler.py`.
- [x] 2.2 Update `BuildPackRequest` schema and `build_resource_pack` endpoint in `CraftLab-backend/app/api/packs.py` to accept configurable `max_format` / `max_inclusive` (defaulting to 65). Verify with API endpoint tests in `CraftLab-backend/tests/test_packs_api.py`.

## 3. Pre-Flight Audit Expansion (Shaders & Texture References)

- [x] 3.1 Implement core shader collision detection in `PreflightValidator.validate` in `CraftLab-backend/app/domain/pack_validator.py` to detect overlapping `.vsh`, `.fsh`, and shader JSON files across active layers and report collision warnings with layer precedence. Verify with unit tests in `CraftLab-backend/tests/test_pack_validator.py`.
- [x] 3.2 Implement texture reference existence and mipmap dimension safety checks in `PreflightValidator.validate` in `CraftLab-backend/app/domain/pack_validator.py`, verifying that all texture paths in JSON models resolve to physical files on disk, checking power-of-two dimensions, and flagging animated textures missing `.png.mcmeta`. Verify with unit tests in `CraftLab-backend/tests/test_pack_validator.py`.

## 4. Texture Atlas Auto-Synthesis & Namespace Induction

- [x] 4.1 Implement `AtlasSynthesizer` in `CraftLab-backend/app/domain/pack_merger.py` to scan model texture references across layers, discover custom namespaces (e.g. `studio:`, plugin namespaces), and auto-inject grouped `directory` sources into `assets/minecraft/atlases/blocks.json`. Verify with unit tests in `CraftLab-backend/tests/test_pack_merger.py`.
- [x] 4.2 Implement GUI sprite atlas auto-induction in `AtlasSynthesizer` to scan `textures/gui/sprites/**` and inject corresponding directory sources into `assets/minecraft/atlases/gui.json`. Verify with unit tests in `CraftLab-backend/tests/test_pack_merger.py`.
- [x] 4.3 Upgrade `SemanticMerger.merge_atlas_json` to integrate `AtlasSynthesizer` and deduplicate redundant `single` sources covered by `directory` prefixes. Verify with unit tests in `CraftLab-backend/tests/test_pack_merger.py`.

## 5. Shader Routing Engine & Dual Projection Updates

- [x] 5.1 Implement `ShaderRouter` in `CraftLab-backend/app/domain/pack_merger.py` to classify shader compatibility and route 1.21.4+ modern shader programs to `overlay_v1_21_4/assets/minecraft/shaders/core/` while preserving legacy shaders in root assets. Verify with unit tests in `CraftLab-backend/tests/test_pack_merger.py`.
- [x] 5.2 Update `apply_dual_projection` and `merge_layers_to_directory` in `CraftLab-backend/app/domain/pack_merger.py` to orchestrate multi-overlay generation across `overlay_v1_21_2` and `overlay_v1_21_4`. Verify with integration test in `CraftLab-backend/tests/test_pack_merger.py`.

## 6. End-to-End Verification & Test Suite

- [x] 6.1 Execute the complete resource pack test suite (`pytest tests/test_pack_compiler.py tests/test_pack_merger.py tests/test_pack_validator.py tests/test_packs_api.py`) and verify all tests pass.
- [x] 6.2 Validate sample end-to-end pack compilation with custom studio models, shaders, and atlases, verifying SHA-1 determinism and multi-version `pack.mcmeta` output.
