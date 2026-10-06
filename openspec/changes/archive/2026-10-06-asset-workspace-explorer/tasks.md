# Tasks

## 1. Backend Workspace Storage & REST API

- [x] 1.1 Implement workspace pack auto-initialization service in `backend/app/domain/workspace.py` that verifies `data/packs/workspace/`, creates `pack.mcmeta` (format 34..65) and directory scaffolding (`assets/minecraft/textures/`, `assets/minecraft/models/`, `assets/minecraft/items/`), and verify with unit tests.
- [x] 1.2 Implement Minecraft Resource Location resolver utility function in `backend/app/domain/workspace.py` mapping relative paths to `namespace:path`, and verify mappings for textures, models, 1.21.2+ item definitions, and sounds.
- [x] 1.3 Implement workspace filesystem endpoints (`GET /api/v1/packs/workspace/tree`, `GET /api/v1/packs/workspace/file`, `PUT /api/v1/packs/workspace/file`, `POST /api/v1/packs/workspace/directory`, `POST /api/v1/packs/workspace/upload`, `DELETE /api/v1/packs/workspace/file`) in `backend/app/api/packs.py` with traversal security and Minecraft regex validation, and verify with API tests.
- [x] 1.4 Implement metadata inspection endpoint (`GET /api/v1/packs/workspace/metadata`) computing Resource Location, image dimensions, file size, referencing models, and missing texture diagnostics, and verify with pytest.

## 2. Pack Compiler & Pre-flight Integration

- [x] 2.1 Update `backend/app/api/packs.py` compilation (`build_resource_pack`) and validation (`run_preflight_check`) to include `data/packs/workspace/` as an authoring layer with priority above external sources and below dynamic studio projections, and verify compilation includes workspace assets.
- [x] 2.2 Write automated pytest test suite in `backend/tests/test_workspace.py` validating auto-initialization, traversal protection, Minecraft regex name validation, metadata calculation, and compile-merging.

## 3. Frontend API Client & Resource Explorer

- [x] 3.1 Add API client methods in `frontend/src/api/client.ts` for workspace tree, file content, save file, upload, create folder, delete, and metadata fetching, and verify TypeScript compilation.
- [x] 3.2 Implement `ResourceExplorer.tsx` tree navigation component with collapsible folders, search bar, category filter pills (All, Textures, Models, Sounds), safe folder creation dialog, upload action, and verify rendering.

## 4. Frontend Content Viewer & Metadata Viewer

- [x] 4.1 Implement `ContentViewer.tsx` with adaptive rendering: nearest-neighbor pixelated PNG viewer with 1x-8x zoom and alpha checkerboard, direct monospace JSON text editor with real-time syntax checking, formatting, and `Ctrl+S` save, plus an HTML5 audio player for OGG files.
- [x] 4.2 Implement `MetadataViewer.tsx` displaying calculated Resource Location, 1-click copy buttons (Resource Location, `item_model` component tag, `"layer0"` line, and `/give` command), asset dimensions/file size, and cross-reference integrity alerts.

## 5. Main Workspace View & Studio Integration

- [x] 5.1 Implement `AssetWorkspaceView.tsx` assembling the 3-panel layout (Resource Explorer, Content Viewer, Metadata Viewer) with breadcrumbs and responsive styling, and add the "Assets Explorer" navigation tab in `frontend/src/App.tsx`.
- [x] 5.2 Implement `AssetPickerModal.tsx` and integrate with `frontend/src/features/items/ItemEditor.tsx` to allow selecting models and textures directly from the workspace pack into item definitions.
- [x] 5.3 Verify end-to-end integration: run frontend production build (`npm run build`), run backend test suite (`pytest`), and verify clean operation.
