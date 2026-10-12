# Proposal: Sync Equipment Models to Minecraft Official Standard

## Why

Minecraft 1.21.4 (snapshot 24w45a) finalized the Equipment Models specification by moving definition files from `assets/<namespace>/models/equipment/` to `assets/<namespace>/equipment/`, restructuring `layers` into a dictionary keyed by layer types, and renaming the `model` property in the `minecraft:equippable` item data component to `asset_id`. CraftLab's current implementation is based on the early, obsolete 1.21.2 snapshot (24w36a), causing generated equipment models and equippable components to be ignored or rejected by modern Minecraft clients.

## What Changes

- **Equipment File Path Migration**: Canonical workspace files are written to and read from `assets/<namespace>/equipment/<id>.json` instead of `assets/<namespace>/models/equipment/<id>.json`.
- **Transparent Backward-Compatibility Ingestion**: Backend will transparently discover and read legacy models located at `models/equipment/<id>.json`, upgrading their schema in-memory.
- **Official Layer Schema**: Redefine `"layers"` as a JSON object mapping layer type keys (`humanoid`, `humanoid_leggings`, `wings`, `wolf_body`, `horse_body`, `llama_body`, `pig_saddle`, etc.) to arrays of layer objects (`texture`, optional `dyeable` object with `color_when_undyed` RGB integer, and optional `use_player_texture` boolean).
- **Hybrid Multi-Version Pack Pipeline**: The compiler (`PackMerger`) will stage canonical `equipment/<id>.json` in the root pack and `overlay_v1_21_4`, while synthesizing a backward-compatible mirror into `overlay_v1_21_2` under `models/equipment/<id>.json` for clients on pack format 37–42.
- **Equippable Data Component Standardization**: Update `minecraft:equippable` component generation in Backend and Frontend to use `asset_id` instead of `model`, and expand supported slots to include `body` and `saddle`.
- **Frontend Equipment Studio Redesign**: Reorganize layer editing into grouped targets (`humanoid`, `humanoid_leggings`, `wings`, `mounts/pets`) with proper `dyeable` controls, live preview, and updated code snippets.
- **Frontend Item Studio Update**: Update `ComponentBuilder.tsx` to bind `asset_id` with autocomplete and provide the full slot set.

## Capabilities

### Modified Capabilities

- `creative-assets-lab`: Updates equipment model authoring to generate standard `assets/<namespace>/equipment/<id>.json` descriptors with layer-type-keyed layers and official `dyeable` schemas.
- `resource-pack-pipeline`: Updates the compiler and merger engine to package canonical `equipment/<id>.json` for modern clients while auto-generating `models/equipment/` mirrors in `overlay_v1_21_2`.
- `item-studio`: Updates the `minecraft:equippable` component editor in Item Studio to bind and serialize `asset_id` instead of `model`, expanding selectable slots to include `body` and `saddle`.

## Impact

- **Backend**: `app/domain/equipment.py`, `app/domain/pack_merger.py`, `app/api/creative.py`, and unit tests in `tests/test_equipment.py`.
- **Frontend**: `src/api/client.ts`, `src/features/creative/tabs/EquipmentStudioTab.tsx`, `src/features/items/ComponentBuilder.tsx`.
- **Specs & Documentation**: `openspec/specs/creative-assets-lab/spec.md`, `openspec/specs/resource-pack-pipeline/spec.md`, `openspec/specs/item-studio/spec.md`, and docs in `docs/en` and `docs/es`.
