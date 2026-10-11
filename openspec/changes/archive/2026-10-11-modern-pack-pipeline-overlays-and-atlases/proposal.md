# Proposal

## Why

Minecraft 1.21.2 and 1.21.4 introduced breaking changes to the client resource pack pipeline, including Item Definition V2 (`items/*.json`), core shader vertex format refactoring, and texture atlas requirements (`atlases/*.json`). CraftLab currently relies on a single hardcoded overlay (`overlay_v1_21_2` with fixed format 65), performs naive string-deduplication on atlas JSONs without namespace induction (leading to missing sprite bugs on custom items), overwrites shader files blindly during layer merging, and lacks manifest inspection for third-party ingested packs. Modernizing the resource pack pipeline provides automated overlay normalization, shader conflict auditing and version routing, and intelligent atlas auto-synthesis across multi-version Minecraft 1.21 clients.

## What Changes

- **Canonical Multi-Version Overlay Chaining**: Replace the single static overlay with a structured cumulative overlay chain: Root (formats 34-41 for 1.21.0 - 1.21.1), `overlay_v1_21_2` (formats 42 to `max_inclusive` for Item Definition V2), and `overlay_v1_21_4` (formats 46 to `max_inclusive` for modern shader pipelines and modern client render passes).
- **Dynamic Operator-Configurable Format Bounds**: Allow operators to configure `max_inclusive` (defaulting to 65) dynamically via the compilation API and workspace settings instead of hardcoded constants.
- **Pack Manifest Inspector & Overlay Normalizer**: Read and parse `pack.mcmeta` on ingested external pack archives (such as ItemsAdder, Oraxen, or custom zip archives), translating arbitrary external overlay directories and format bounds into CraftLab's canonical overlay architecture.
- **Pre-Flight Asset & Shader Conflict Audit**: Extend pre-flight validation to detect collisions across core shader files (`shaders/core/**`), verify the physical existence on disk of all textures referenced by JSON models (preventing missing texture errors), validate mipmap-safe dimensions (power-of-two constraints), and ensure animated textures have corresponding `.png.mcmeta` definitions.
- **Atlas Auto-Synthesis & Namespace Induction**: Upgrade `atlases/*.json` merging to scan all referenced model textures, discover custom namespaces (`studio:`, plugin namespaces), and automatically synthesize minimal, compact `directory` sources into `assets/minecraft/atlases/blocks.json` and `assets/minecraft/atlases/gui.json`.
- **Shader Routing Engine**: Automatically route legacy shaders (1.21.0 - 1.21.3) to the root assets layer and modernized 1.21.4+ shaders to `overlay_v1_21_4`.

## Capabilities

### New Capabilities
<!-- None: all functionality extends existing resource-pack-pipeline capability -->

### Modified Capabilities
- `resource-pack-pipeline`: Update `Universal Hybrid Pack Overlays Compilation` to support configurable `max_inclusive` and multi-overlay chaining (`overlay_v1_21_2` and `overlay_v1_21_4`); extend `Pack Source Storage and Ingestion` with manifest inspection and overlay normalization; extend `Pre-Flight Collision Detection` with shader collision auditing and physical texture/atlas integrity verification; and upgrade `Semantic JSON Configuration Merging` with atlas auto-synthesis and shader routing.

## Impact

- **Backend Domain Services**: Updates to `DeterministicPackCompiler`, `SemanticMerger`, `PreflightValidator`, and `PackRepository` in `CraftLab-backend/app/domain/`.
- **Backend API**: Endpoints in `CraftLab-backend/app/api/packs.py` (`POST /api/v1/packs/build`, `POST /api/v1/packs/preflight`) accept configurable format boundaries and report enhanced collision/audit diagnostics.
- **Test Suites**: Unit and integration tests in `CraftLab-backend/tests/` (`test_pack_compiler.py`, `test_pack_merger.py`, `test_pack_validator.py`, `test_packs_api.py`).
- **Dependencies & Performance**: Zero external dependency additions; purely standard library (`zipfile`, `hashlib`, `json`, `pathlib`) and existing PIL/image checks where texture dimensions are inspected.
