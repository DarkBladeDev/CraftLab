# Proposal

## Why
The Minecraft Content Platform requires an end-to-end working vertical slice to validate its core architectural decisions before expanding into advanced content types and third-party integrations. This change implements the complete pipeline—from web authoring to live server deployment—using native Paper 1.21 item definitions.

## What Changes
- **Backend Modular Monolith**: Establish FastAPI backend with async WebSockets, Pydantic v2 schemas, and SQLite persistence for targets, revisions, items, and deployment plans.
- **WebSocket Agent Gateway**: Implement outbound TLS/WSS session manager, `agent.hello` handshake, heartbeats, and typed operation dispatching (`create_or_update_item`).
- **Paper 1.21 Server Agent Plugin**: Implement Java 21 Paper plugin with outbound WebSocket connection, extensible `ItemAdapter` interface, local persistence in `items.json`, and `/mcp give` in-game command.
- **Web Client UI**: Implement React + Vite + Tailwind interface with Item Editor, Target server monitor, and deployment plan approval view.
- **End-to-End Item Deployment**: Connect all layers so an authored item definition is validated, snapshotted in an immutable revision, packaged in a deployment plan, transmitted via WebSocket, and applied on Paper 1.21.

## Capabilities

### New Capabilities
<!-- No new capabilities; all work refines and realizes the 5 foundational capabilities. -->

### Modified Capabilities
- `content-model`: Add concrete canonical schemas and validation for Paper 1.21 item definitions and deterministic revision snapshots.
- `agent-protocol`: Add concrete payload schemas for `agent.hello`, `agent.heartbeat`, `operation.execute` (`create_or_update_item`), and `agent.operation.result`.
- `target-management`: Add target registration, online session tracking via heartbeat, and environment metadata persistence.
- `deployment-engine`: Add deterministic plan generation for item operations, manual publisher approval flow, and execution lifecycle tracking.
- `paper-agent-adapter`: Add Paper 1.21 Data Components item translation, local file persistence in `items.json`, and operator `/mcp give` command.

## Impact
- **Monorepo Structure**: Introduces `backend/`, `frontend/`, and `paper-agent/` project directories.
- **API Contracts**: Establishes initial REST endpoints under `/api/` and WebSocket endpoint under `/ws/agent`.
- **Runtime Dependencies**: Python 3.11+, Node 18+, Java 21, and Paper 1.21.x.
