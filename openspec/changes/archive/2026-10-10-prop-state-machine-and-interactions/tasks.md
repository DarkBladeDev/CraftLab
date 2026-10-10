# Tasks: Prop State Machine, Audio/Visual FX, and Dynamic Hitboxes

## 1. Backend Content Model & Schema

- [x] 1.1 Update `BlockModel` in `CraftLab-backend/app/models/block.py` and Pydantic schemas to include `default_state` and `states` JSON fields.
- [x] 1.2 Update validation in `CraftLab-backend/app/domain/blocks.py` to validate `default_state`, ensure `light_level` is between 0 and 15, verify transition targets, and maintain backward compatibility for single-state props.
- [x] 1.3 Add unit tests in `CraftLab-backend/tests/test_blocks.py` covering multi-state prop validation and verify all backend tests pass via `pytest`.

## 2. Frontend Block Studio

- [x] 2.1 Update `Block` interface and state types in `CraftLab-frontend/src/api/client.ts` to include `default_state` and `states`.
- [x] 2.2 Add "States & Variants" interface section to `CraftLab-frontend/src/features/blocks/BlockStudio.tsx` to author states, select block models, configure light levels (0–15), sound effects, and transitions.
- [x] 2.3 Verify TypeScript compilation and production build via `npm run build` in `CraftLab-frontend`.

## 3. Paper Agent Data & Storage Layer

- [x] 3.1 Update `PropDefinition.java` in `CraftLab-plugin` to represent `default_state` and a typed `PropState` structure (model, light level, sound key, collision override, next state).
- [x] 3.2 Update `PropInstance.java` and `PropStorage.java` to persist `current_state` in SQLite (`placed_props`), adding automatic migration for existing tables.
- [x] 3.3 Add unit tests in `CraftLab-plugin` verifying prop state deserialization and SQLite persistence.

## 4. Paper Agent Runtime, Lighting & Interaction

- [x] 4.1 Update `PropManager.java` to resolve the active `block_model` from `current_state`, manage `Material.LIGHT` block lifecycle, and broadcast `WrapperPlayServerEntityMetadata` updates without entity respawning.
- [x] 4.2 Update `PropInteractionListener.java` to execute state transitions on right click, enforce a 250ms anti-spam cooldown, play configured sounds, and execute safe velocity ejection when closing barrier hitboxes.
- [x] 4.3 Update `PropPlaceBreakListener.java` to clean up active light blocks when a prop is broken.
- [x] 4.4 Verify plugin compilation and unit tests via `./gradlew build` in `CraftLab-plugin`.

## 5. End-to-End Verification & Validation

- [x] 5.1 Run all test suites across the monorepo (backend pytest, frontend build, plugin gradle).
- [x] 5.2 Validate OpenSpec change artifacts via `openspec validate prop-state-machine-and-interactions`.
