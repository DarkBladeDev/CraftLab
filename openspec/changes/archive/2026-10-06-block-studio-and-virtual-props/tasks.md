# Tasks

## 1. Backend Domain & Database Persistence

- [x] 1.1 Implement `BlockDefinition` in `backend/app/domain/blocks.py` with validation and `to_canonical_dict()`, and verify with unit tests
- [x] 1.2 Implement SQLAlchemy entity `BlockModel` in `backend/app/models/block.py` and register in database initialization, verifying table creation
- [x] 1.3 Extend `backend/app/domain/revisions.py` to support dual-collection canonical hashing over items and blocks, and verify deterministic hash equality with unit tests

## 2. Backend REST API

- [x] 2.1 Implement `/api/v1/blocks` CRUD endpoints in `backend/app/api/blocks.py` (list, get, create, update, delete) and verify with pytest API tests
- [x] 2.2 Wire the blocks router into the main FastAPI application and verify OpenAPI docs include the blocks endpoints

## 3. Paper Agent PacketEvents & Prop Engine

- [x] 3.1 Add PacketEvents repository and `com.github.retrooper:packetevents-spigot:2.14.0` dependency in `paper-agent/build.gradle.kts`, verifying Gradle compile
- [x] 3.2 Implement `PropDefinition` and `PropInstance` models and local SQLite storage `PropStorage` at `plugins/McpAgent/data/props.db`, verifying schema creation and persistence
- [x] 3.3 Implement `PropManager` with spatial chunk index, PacketEvents `ITEM_DISPLAY` virtual entity spawning, quaternion rotation calculations, and tracking range culling
- [x] 3.4 Implement `PropPlaceBreakListener` handling player cardinal facing detection, barrier collision placement/breaking, and item drops
- [x] 3.5 Implement `PropInteractionListener` for native "Sit" interactions with temporary invisible seat vehicles and dismount cleanup

## 4. Frontend Block Studio UI

- [x] 4.1 Create Block Studio navigation link and main page structure in `frontend/src/` alongside Item Studio
- [x] 4.2 Build block form editor with 3D transform controls (scale, translation sliders), hitbox collision grid selector, drop item selector, and seat toggle
- [x] 4.3 Integrate frontend API client with `/api/v1/blocks` and verify full CRUD flow

## 5. End-to-End Verification

- [x] 5.1 Run full backend pytest test suite verifying all item, block, revision, and API tests pass
- [x] 5.2 Run `./gradlew test` in `paper-agent` ensuring all Java tests pass
- [x] 5.3 Run `npm run build` in `frontend` ensuring clean build with zero TypeScript or bundler errors
