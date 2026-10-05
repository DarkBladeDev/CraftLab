# Tasks

## 1. Database & Backend Domain Model

- [x] 1.1 Create `DiscoveredCatalogItemModel` in `backend/app/models/entities.py` and verify table initialization in database tests
- [x] 1.2 Implement `VanillaCatalogService` in `backend/app/domain/` with Minecraft 1.21 item taxonomy and verify category filtering unit test
- [x] 1.3 Implement repository and service methods for upserting and querying discovered items per target in `backend/app/domain/` and verify unit tests

## 2. Gateway & Protocol Extensions

- [x] 2.1 Extend `backend/app/gateway/manager.py` to handle `detectedPlugins` in handshake and route `catalog:manifest` and `catalog:refresh` envelopes, verified by gateway unit tests
- [x] 2.2 Create `backend/app/api/catalogs.py` with endpoints for vanilla items, discovered items, and catalog sync, and verify with FastAPI test client
- [x] 2.3 Implement plugin schema registry with `oraxen-item-v1.json` and endpoint `GET /api/schemas/plugins/{id}`, verified with JSON schema test

## 3. Paper Agent Oraxen Hooks & Exporter

- [x] 3.1 Configure `softdepend: [Oraxen]` in `paper-agent` and implement safe runtime reflection hook `OraxenCatalogHook.java`, verified by Gradle build
- [x] 3.2 Implement catalog inspection and manifest streaming in `paper-agent` for handshake and `catalog:refresh`, verified by agent test suite
- [x] 3.3 Implement `OraxenItemExporter.java` to write deployed item configurations to `plugins/Oraxen/items/platform_items.yml` and execute reload, verified by unit tests
- [x] 3.4 Update `backend/mock_agent.py` to simulate Oraxen plugin presence and stream mock catalog manifests, verified by running mock agent locally

## 4. Frontend Asset Browser & Hybrid Editor

- [x] 4.1 Build `AssetBrowser.tsx` in `frontend/src/features/items/` with tabs for Vanilla 1.21, Platform Drafts, and Oraxen, verified by UI search and filter behavior
- [x] 4.2 Implement "Fork as Base" action connecting `AssetBrowser` to `ItemEditor`, pre-filling material, display name, lore, and CMD, verified by component testing
- [x] 4.3 Create dynamic schema-driven form component for Oraxen fields with synchronized Raw YAML/JSON mode, verified by field editing and syntax toggle
- [x] 4.4 Update `ItemEditor.tsx` with export target selection (`native` vs `oraxen`) and target catalog sync trigger button, verified by frontend build test

## 5. End-to-End Verification

- [x] 5.1 Run full integration verification with FastAPI backend, `mock_agent.py`, and frontend production build (`npm run build`), verifying end-to-end catalog discovery and export
