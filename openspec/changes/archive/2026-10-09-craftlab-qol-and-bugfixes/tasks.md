# Tasks

## 1. Asset Workspace & Visual Quality

- [x] 1.1 Implement `POST /v1/packs/workspace/rename` endpoint in `CraftLab-backend/app/api/packs.py` supporting file and folder renames with path traversal protection, verifying via curl/pytest.
- [x] 1.2 Add `renameWorkspacePath` client method in `CraftLab-frontend/src/api/client.ts` and add rename and directory deletion actions in `ResourceExplorer.tsx`, verifying via UI tree operations.
- [x] 1.3 Fix texture preview alignment and checkerboard sizing in `CraftLab-frontend/src/features/assets/ContentViewer.tsx` by synchronizing container dimensions with the pixelated image, verifying visually at 1x, 4x, and 8x zoom.

## 2. Resource Pack Management & Workspace Config

- [x] 2.1 Implement `GET /v1/packs/workspace/config` and `PUT /v1/packs/workspace/config` in `CraftLab-backend/app/api/packs.py` to inspect and modify `pack.mcmeta` properties, verifying via API tests.
- [x] 2.2 Implement `PATCH /v1/packs/sources/{source_id}` in `CraftLab-backend/app/api/packs.py` allowing modification of layer priority, name, and active status, verifying via database persistence check.
- [x] 2.3 Add workspace pack configuration modal and external pack layer edit controls in `ResourcePackManagerView.tsx`, verifying that updating priorities and descriptions updates the table and backend.

## 3. Block Studio, Dual Model & Runtime Agent

- [x] 3.1 Verify and reconcile backend block model migrations (`block_model` column in SQLite and Pydantic validators) in `CraftLab-backend`, verifying test suite passes.
- [x] 3.2 Update `CraftLab-frontend/src/features/blocks/BlockStudio.tsx` to label `Block Model Identifier` (`block_model`) for placed 3D display and add `Item Model Identifier` (`item_model`) for inventory item representations, verifying state persistence.
- [x] 3.3 In `BlockStudio.tsx`, conditionally disable or hide Hardness and Optimal Tool when Hitbox Type is `Solid Barrier` with an explanatory badge, verifying reactive UI behavior.
- [x] 3.4 In `BlockStudio.tsx` and backend `BlockDefinition`, add `lay` ("Lie Down") interaction option, verifying block save and schema validation.
- [x] 3.5 In `CraftLab-plugin`, update `PropDefinition`, `PropManager`, `PropPlaceBreakListener`, and `PropInteractionListener` to render `block_model` for ItemDisplay and handle `lay` pose via PacketEvents `SLEEPING` metadata, verifying plugin compile with `./gradlew build`.
- [x] 3.6 Verify that creating a revision in `CraftLab-backend/app/api/items.py` succeeds when 0 items and >=1 blocks exist, verifying endpoint returns HTTP 200 with valid snapshot.

## 4. Item Studio & Vanilla Catalog Polish

- [x] 4.1 In `CraftLab-frontend/src/features/items/AssetBrowser.tsx`, add collapsible toggle state and button in the header, verifying expanding and collapsing preserves search state.
- [x] 4.2 In `AssetBrowser.tsx`, update category tab title from `Vanilla 1.21 (X)` to `Vanilla (X)`, verifying dynamic item count display.
- [x] 4.3 Move and track the generated 1,332-item vanilla catalog JSON into `CraftLab-backend/app/assets/vanilla_items_1.21.json` and update `VanillaCatalogService` in `CraftLab-backend/app/domain/catalogs.py`, verifying fast lookup with textures.
