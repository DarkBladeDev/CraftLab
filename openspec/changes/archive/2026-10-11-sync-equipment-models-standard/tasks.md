# Tasks: Sync Equipment Models to Minecraft Official Standard

## 1. Backend Domain & Schema Synchronization

- [x] 1.1 Update directory paths in `app/domain/equipment.py` from `models/equipment` to `equipment` and update path helper functions; verify path resolution unit tests.
- [x] 1.2 Update `validate_equipment_model_schema` in `app/domain/equipment.py` to validate `layers` as a dictionary keyed by valid layer types mapping to layer definition arrays (`texture`, optional `dyeable` dict with `color_when_undyed` int, `use_player_texture` bool); verify with unit tests.
- [x] 1.3 Implement transparent legacy descriptor ingestion in `list_equipment_models` and `get_equipment_model` to load and normalize legacy `models/equipment/*.json` flat lists into the layer-type dictionary format; verify with unit tests.
- [x] 1.4 Update `generate_equippable_component` and `save_equipment_model` to generate `asset_id` instead of `model` and include `body` and `saddle` in `VALID_EQUIPMENT_SLOTS`; verify component generation tests.

## 2. Backend API & Pack Compilation Pipeline

- [x] 2.1 Update `EquipmentModelRequest` schema in `app/api/creative.py` to accept `layers: Dict[str, List[Dict[str, Any]]]` and return `asset_id`; verify API responses.
- [x] 2.2 Update `PackMerger` in `app/domain/pack_merger.py` to discover descriptors at `assets/*/equipment/*.json`, stage into root and `overlay_v1_21_4`, and synthesize a backward-compatible mirror into `overlay_v1_21_2` under `assets/*/models/equipment/*.json`; verify compiler tests.
- [x] 2.3 Update and expand backend unit tests in `tests/test_equipment.py` to cover new schema, legacy ingestion, component generation, and compiler staging; verify with `pytest tests/test_equipment.py`.

## 3. Frontend Client & Studio Editors

- [x] 3.1 Update TypeScript interfaces in `CraftLab-frontend/src/api/client.ts` (`EquipmentModelItem`, `EquipmentLayer`) to reflect `layers: Record<string, EquipmentLayer[]>`; verify frontend type-check.
- [x] 3.2 Update `ComponentBuilder.tsx` in `CraftLab-frontend/src/features/items` to bind `asset_id` instead of `model`, support legacy `model` on load, and include `body` and `saddle` in slot options; verify UI and JSON serialization.
- [x] 3.3 Redesign layer management in `EquipmentStudioTab.tsx` in `CraftLab-frontend/src/features/creative/tabs` to organize layers by target category (`humanoid`, `humanoid_leggings`, `wings`, `mounts/pets`), configure `dyeable` options, and update the generated equippable snippet; verify UI interaction.

## 4. Documentation & Monorepo Validation

- [x] 4.1 Update technical documentation in `docs/en/craftlab-backend.md`, `docs/es/craftlab-backend.md`, `docs/en/craftlab-frontend.md`, and `docs/es/craftlab-frontend.md` to document the 1.21.4+ standard, `asset_id`, and hybrid overlay behavior.
- [x] 4.2 Run monorepo test suite and build checks (`pytest` in backend, `npm run build` in frontend) to verify zero regressions.
