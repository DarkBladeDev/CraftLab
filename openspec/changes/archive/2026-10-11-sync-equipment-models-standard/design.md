# Design: Sync Equipment Models to Minecraft Official Standard

## Context

See `proposal.md` for motivation. Currently, CraftLab generates equipment descriptors in `assets/<namespace>/models/equipment/<id>.json` using a flat list of layer objects with an embedded `type` field, and references them via `model` in `minecraft:equippable`.

Minecraft 1.21.4+ expects descriptors directly at `assets/<namespace>/equipment/<id>.json`, with a `layers` object mapping layer types (`humanoid`, `humanoid_leggings`, `wings`, `wolf_body`, etc.) to arrays of layer objects, resolving textures to `assets/<namespace>/textures/entity/equipment/<layer_type>/<path>.png`, and referencing them via `asset_id` in `minecraft:equippable`.

## Goals / Non-Goals

**Goals:**
- Provide full compatibility with official Minecraft Java Edition 1.21.4+ specifications.
- Maintain seamless backward compatibility for 1.21.2-1.21.3 clients by having `PackMerger` mirror descriptors into `overlay_v1_21_2`.
- Ensure zero data loss for existing CraftLab workspaces by transparently migrating legacy `models/equipment/<id>.json` descriptors and `model` data component fields.
- Provide a clean, organized user interface in Equipment Studio that groups layers by body target.

**Non-Goals:**
- Custom 3D entity geometry for armor (Minecraft equipment models are texture-mapping overlays applied to standard entity rigs).
- Modifying Paper runtime plugin packet pipelines (modern Paper natively handles 1.21.2+ data components).

## Decisions

### Decision 1: Canonical Storage in `assets/<namespace>/equipment/`
- **Choice**: Store and write new equipment descriptors to `assets/<namespace>/equipment/<id>.json`.
- **Rationale**: This is the official location standardized in Minecraft 24w45a / 1.21.4+.
- **Alternative considered**: Keeping `models/equipment/` and symlinking or generating `equipment/` at compile time. Rejected because it would leave the workspace out of sync with official resource pack directory structures.

### Decision 2: Schema Normalization & Legacy Ingestion
- **Choice**: In `app/domain/equipment.py`, `get_equipment_model` and `list_equipment_models` will inspect `assets/<namespace>/equipment/` first. If missing, they check `assets/<namespace>/models/equipment/`. If a legacy descriptor (with flat `layers: [...]`) is encountered, normalize it on read to the dictionary format:
  ```json
  {
    "layers": {
      "humanoid": [
        { "texture": "craftlab:custom_paladin" }
      ]
    }
  }
  ```
- **Rationale**: Guarantees existing projects continue functioning without manual user migration.

### Decision 3: Hybrid Overlay Mirroring in `PackMerger`
- **Choice**: When building resource packs:
  - Root and `overlay_v1_21_4`: stage `assets/<ns>/equipment/<id>.json`.
  - `overlay_v1_21_2`: automatically copy/convert descriptors to `overlay_v1_21_2/assets/<ns>/models/equipment/<id>.json`.
- **Rationale**: Fulfills the decision to maintain full hybrid multi-version compatibility across 1.21.2, 1.21.3, and 1.21.4+.

### Decision 4: `asset_id` Binding in `minecraft:equippable`
- **Choice**: Standardize the component generator and Item Studio editor on `asset_id`. If an item contains `model` upon loading, map `model` to `asset_id`.
- **Rationale**: In Minecraft 1.21.4+, vanilla ignores `model` and strictly reads `asset_id`.

### Decision 5: Target-Categorized UI in Equipment Studio
- **Choice**: Organize layers in `EquipmentStudioTab.tsx` by target category:
  - **Humanoid** (`humanoid` - helmet, chestplate, boots)
  - **Leggings** (`humanoid_leggings` - leggings)
  - **Wings** (`wings` - elytra with `use_player_texture` option)
  - **Mounts & Pets** (`wolf_body`, `horse_body`, `llama_body`, etc.)
- **Rationale**: Matches how armor sets are constructed in Minecraft while preventing invalid layer combinations.

## Risks / Trade-offs

- **[Risk] Existing packs compiled with older CraftLab might have broken equipment in 1.21.4**:
  - *Mitigation*: Re-compiling the pack with the updated pipeline immediately produces both canonical `equipment/` and `models/equipment/` overlay targets.
- **[Risk] Dyeable layer hides when color is omitted**:
  - *Mitigation*: In Minecraft, omitting `color_when_undyed` intentionally hides the layer if the item is undyed. The UI will clearly explain this behavior and offer a default undyed tint color when enabling dyeable overlays.

## Migration Plan

1. Backend domain models and schema validators updated with backward-compatible normalization.
2. PackMerger pipeline updated to package `equipment/` and mirror into `overlay_v1_21_2`.
3. Frontend API client and studio tabs updated to reflect the new target structure.
4. Existing unit tests updated and expanded to test both new and legacy formats.
