# Tasks

## 1. Backend Domain & Storage Models

- [x] 1.1 Create SQLAlchemy models for `PackSourceModel` and `CompiledPackModel` in `backend/app/models/entities.py` and verify table initialization in test database.
- [x] 1.2 Implement repository methods in `backend/app/domain/` for managing pack sources, layer ordering, and compiled pack metadata, and verify unit tests pass.

## 2. Pre-Flight Conflict Engine & Semantic Merger

- [x] 2.1 Implement `PreflightValidator` in `backend/app/domain/pack_validator.py` that extracts `(material, custom_model_data)` mappings across layers and reports collisions, and verify with pytest.
- [x] 2.2 Implement `SemanticMerger` in `backend/app/domain/pack_merger.py` handling deep merge for `sounds.json`, `font/*.json`, `atlases/*.json`, and item model overrides, and verify with test cases.

## 3. Deterministic Zip Compiler & HTTP Distribution

- [x] 3.1 Implement `DeterministicPackCompiler` with sorted entries, normalized timestamps, and 40-character SHA-1 calculation, and verify bit-for-bit reproducibility in unit tests.
- [x] 3.2 Add FastAPI routes `POST /api/v1/packs/preflight`, `POST /api/v1/packs/build`, and `GET /api/v1/packs/{target_id}/download` with ETag caching, and verify with test client.
- [x] 3.3 Add multipart upload route `POST /api/v1/packs/sources/upload` for third-party `.zip` archives and verify disk extraction into source storage.

## 4. Agent Protocol & Paper Agent In-Game Delivery

- [x] 4.1 Update agent protocol envelope definitions and WebSocket manager to handle `resource_pack_source_sync` and `resource_pack_ready` messages, and verify envelope serialization tests.
- [x] 4.2 Implement local plugin pack scanner in `paper-agent` to detect and synchronize local Oraxen pack folders to the backend, and verify sync dispatch.
- [x] 4.3 Implement `PlayerJoinEvent` listener in `paper-agent` that applies `player.setResourcePack(...)` with stored URL and SHA-1 hash, and verify listener logic in Paper tests.
- [x] 4.4 Register in-game commands `/mcp reloadpack` and `/mcp reloadpack all` with permission gating, and verify command execution in Paper agent test suite.

## 5. Frontend UI & Verification

- [x] 5.1 Create Resource Pack Management view in the frontend with build actions, layer priority controls, and download URL display, and verify build with `npm run build`.
- [x] 5.2 Create Pre-Flight Conflict Resolution modal with deep-link navigation to conflicting items, and verify component render in browser.
- [x] 5.3 Execute end-to-end integration test flow (ingestion -> pre-flight -> build -> agent dispatch -> HTTP download) and verify all backend and frontend tests pass.
