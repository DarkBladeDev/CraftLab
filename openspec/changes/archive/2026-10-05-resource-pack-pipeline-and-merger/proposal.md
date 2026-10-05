# Proposal: Resource Pack Pipeline & Merger

## Why

Minecraft 1.21 item customization relies heavily on client-side resource packs (textures, models, sounds, atlases, and item definitions). Currently, the platform defines and deploys server-side item components, but players cannot see custom models or textures unless an external resource pack is manually assembled and hosted. Furthermore, servers frequently use third-party plugins (like Oraxen or ModelEngine) that generate their own resource packs, leading to collisions in CustomModelData or overwritten sound and font configurations when merged naively.

This change introduces an automated, centralized Resource Pack Pipeline & Merger in the Python backend that ingests studio assets, merges third-party plugin packs with pre-flight collision detection, deterministically compiles optimized zip archives with reproducible SHA-1 hashes, and serves them directly via HTTP to Minecraft clients and connected Paper agents.

## What Changes

- **Pack Source Management & Ingestion**:
  - Store studio assets and support dual ingestion of third-party plugin packs: manual `.zip` uploads via Web UI and automated pack synchronization from connected Paper agents (e.g. Oraxen pack directory).
  - Priority-based layer hierarchy (Studio Overrides > Ingested Plugin Packs > Server Base Pack).

- **Pre-Flight Conflict Engine**:
  - Analyze CustomModelData (CMD), texture paths, and model identifiers across all layers before building.
  - Return clear diagnostic errors/warnings in the Web UI with direct shortcut links to colliding items so operators can resolve CMD collisions before building.

- **Semantic Resource Pack Merger**:
  - Deep-merge JSON configurations: `sounds.json` (key-level merge), `font/*.json` (provider array concatenation), `atlases/*.json` (source concatenation), and `lang/*.json`.
  - Reconcile item model overrides for Minecraft 1.21 base items.

- **Deterministic Zip Compiler & SHA-1 Hashing**:
  - Lexicographically sorted archive entries with normalized timestamps (epoch 2026-01-01) and fixed compression to ensure reproducible bit-for-bit archives.
  - Calculate 40-character hex SHA-1 checksum to prevent unnecessary client re-downloads.

- **HTTP Distribution & Public Reachability**:
  - High-performance FastAPI static endpoint (`GET /api/v1/packs/{target_id}/download`) with ETag, Content-Length, and aggressive client cache headers.
  - Configurable `public_url` per target or globally to ensure external players can reach the download endpoint.

- **Agent Protocol & Paper In-Game Delivery**:
  - Extend agent protocol with `resource_pack_source_sync` (uploading local plugin packs) and `resource_pack_ready` (notifying agent of new pack URL, SHA-1, prompt, and required flag).
  - Paper agent hooks `PlayerJoinEvent` to prompt joining players with `player.setResourcePack(...)`.
  - Add in-game command `/mcp reloadpack` (prompts executing player) and `/mcp reloadpack all` (prompts all online players).

## Capabilities

### New Capabilities
- `resource-pack-pipeline`: Covers pack source ingestion, pre-flight collision detection, semantic JSON merging, deterministic zip compilation, SHA-1 checksum calculation, and HTTP distribution.

### Modified Capabilities
- `agent-protocol`: Adds message types and schemas for agent-to-backend pack source synchronization and backend-to-agent resource pack notification envelopes.
- `paper-agent-adapter`: Adds local plugin pack discovery and sync, handling `resource_pack_ready` envelopes, prompting joining players in `PlayerJoinEvent`, and `/mcp reloadpack` commands.

## Impact

- **Backend**: New domain models for pack sources and compiled artifacts, `PackMerger` service, preflight validation endpoint, zip compilation engine, and static download route.
- **Frontend**: New Resource Pack Management view with build trigger, pre-flight conflict resolution modal with item shortcuts, and target download URL configuration.
- **Paper Agent**: Enhanced WebSocket message handlers for pack readiness, background pack folder sync, `PlayerJoinEvent` listener, and `/mcp reloadpack` command registration.
- **Protocols / API**: New WebSocket envelope types for resource pack state and HTTP endpoints for pack upload and download.
