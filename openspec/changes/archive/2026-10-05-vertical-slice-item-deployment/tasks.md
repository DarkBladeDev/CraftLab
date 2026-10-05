# Tasks

## 1. Monorepo Setup and Scaffolding

- [x] 1.1 Create monorepo directory layout (`backend/`, `frontend/`, `paper-agent/`) and verify directory structure
- [x] 1.2 Setup backend dependencies (`requirements.txt` with FastAPI, Uvicorn, Pydantic, SQLAlchemy, aiosqlite, websockets) and verify virtual environment installation
- [x] 1.3 Setup Paper plugin Gradle project (`build.gradle.kts`, `settings.gradle.kts` targeting Paper API 1.21.1 and Java 21) and verify `./gradlew build` runs
- [x] 1.4 Setup React frontend (`package.json`, Vite, TypeScript, Tailwind CSS, Lucide icons) and verify `npm run build` succeeds

## 2. Backend Domain Models and Gateway

- [x] 2.1 Implement canonical Pydantic models for Paper 1.21 item definitions and verify field validation against valid and invalid payloads
- [x] 2.2 Implement SQLAlchemy async models (Target, Item, Revision, DeploymentPlan, Deployment) and verify database table creation
- [x] 2.3 Implement deterministic SHA-256 revision hashing service and verify with unit tests that identical items yield identical hashes
- [x] 2.4 Implement WebSocket Agent Gateway with session registry, `agent.hello` handshake, and periodic heartbeat tracking
- [x] 2.5 Implement deployment plan generator creating `create_or_update_item` operations and test plan approval API endpoints
- [x] 2.6 Implement deployment execution dispatcher with correlation tracking for `agent.operation.result` envelopes

## 3. Paper 1.21 Server Agent Plugin

- [x] 3.1 Implement core Paper plugin bootstrap (`plugin.yml`, `config.yml`, and `McpAgentPlugin.java`) and verify plugin loads
- [x] 3.2 Implement WebSocket client with resilient reconnection backoff and `agent.hello` handshake reporting Paper 1.21 metadata
- [x] 3.3 Implement `ItemAdapter` interface and `Paper121ItemAdapter` using native Paper 1.21 Data Components (display name, lore, custom model data, flags)
- [x] 3.4 Implement local item persistence in `items.json` and verify items persist and reload across plugin reloads
- [x] 3.5 Implement in-game command `/mcp give <player> <item_id>` and verify that an operator receives the configured ItemStack

## 4. Web Client Interface

- [x] 4.1 Implement Target Server monitor component displaying real-time online/offline status and Paper version
- [x] 4.2 Implement Item Editor form supporting Material selection, MiniMessage display name, lore list, custom model data, and flags
- [x] 4.3 Implement Deployment Plan modal displaying item diff, approval button, and live execution progress indicator

## 5. End-to-End Verification

- [x] 5.1 Run automated end-to-end integration test simulating agent WebSocket connection, plan generation, and deployment execution
- [x] 5.2 Validate complete workflow: author custom item in Web UI, snapshot revision, approve deployment, apply to Paper agent, and verify item in server storage
