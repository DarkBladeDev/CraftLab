# Design: Resource Pack Pipeline & Merger

## Context

The platform currently manages canonical item definitions, data components, and deployments to Paper servers running Minecraft 1.21. However, client-side visual assets (textures, 3D model JSONs, sounds, fonts, and atlases) are not packaged or distributed automatically. Furthermore, server environments often run plugins (such as Oraxen) that generate their own local resource packs.

See `proposal.md` for motivation and scope boundaries.

## Goals / Non-Goals

**Goals:**
- Centralize resource pack compilation, deterministic packaging, and SHA-1 calculation in the Python backend.
- Provide a multi-layer merger that combines Studio project assets, base server packs, and third-party plugin packs.
- Implement pre-flight conflict detection to catch CustomModelData collisions and path collisions before compilation, providing direct navigation links to conflicting items.
- Ensure bit-for-bit reproducible `.zip` generation with stable SHA-1 checksums to maximize Minecraft client caching.
- Serve compiled packs directly from FastAPI with HTTP caching (`ETag`, `Content-Length`, `Cache-Control`).
- Enable Paper agents to synchronize local plugin packs, receive compiled pack announcements, prompt joining players, and support `/mcp reloadpack` for online testing.

**Non-Goals:**
- Real-time client-side hot-swapping without client reload (Minecraft's client engine always reloads textures when a pack packet is applied).
- Modifying vanilla client code or requiring custom client-side mods (uses standard Bukkit/Paper resource pack packets).
- Automatic remapping of colliding CustomModelData numbers (deliberately avoided to prevent breaking third-party configuration files; operator is alerted with shortcuts instead).

## Decisions

### 1. Centralized Backend Pipeline vs. In-Server Paper Merger
- **Decision**: All asset merging, JSON reconciliation, zip packaging, and SHA-1 hashing take place in the Python FastAPI backend.
- **Rationale**: Keeps server CPU and RAM free for gameplay. Allows Web UI previews and enables a single compiled pack to be served to multiple server targets.
- **Alternatives Considered**: Java-side merger in `paper-agent` (rejected due to excessive server memory consumption and complexity when managing multi-server networks).

### 2. Multi-Layer Pack Precedence & Semantic Merger
- **Decision**: Represent pack sources as ordered layers:
  1. *Layer 3 (Highest)*: Studio Custom Items & Overrides
  2. *Layer 2 (Middle)*: Ingested Third-Party Plugin Packs (Oraxen, uploaded zips)
  3. *Layer 1 (Lowest)*: Server Base Pack (`pack.mcmeta`, base GUI, default fonts)
- **Deep Merge Strategy**:
  - `sounds.json`: Recursive dictionary merge per sound event key.
  - `font/*.json`: Concatenate provider arrays and deduplicate character mappings.
  - `atlases/*.json`: Concatenate atlas source definitions.
  - `lang/*.json`: Merge translation key-value dictionaries.
  - `models/item/*.json`: Merge vanilla override arrays sorted by `custom_model_data`.

### 3. Pre-Flight Validation with Deep Link Diagnostics
- **Decision**: Execute a validation pass prior to packaging that indexes `(material, custom_model_data)` tuples across all layers.
- **Rationale**: Silent overwrites cause subtle in-game visual bugs (e.g., custom sword showing as a custom scythe). Presenting collisions with direct links to the Studio editor allows operators to adjust CMDs immediately.

### 4. Deterministic Zip Archive Compilation
- **Decision**: Construct `.zip` archives with sorted entry paths, normalized timestamps (`1980-01-01 00:00:00` or fixed epoch `2026-01-01 00:00:00`), and fixed compression (`ZIP_DEFLATED`, level 6).
- **Rationale**: Python's standard `zipfile` uses the current system time and arbitrary filesystem iteration order. Without determinism, rebuilding an unchanged pack changes the SHA-1 hash, forcing every player to re-download the pack upon reconnecting.

### 5. Dual Ingestion: UI Upload + Agent Sync
- **Decision**: Support both manual `.zip` uploads via the frontend and automated multipart stream uploads from connected Paper agents (`plugins/Oraxen/pack/`).
- **Rationale**: Operators can upload base packs or third-party assets easily, while live servers running Oraxen keep their assets synchronized automatically.

### 6. Delivery Strategy & Player Experience
- **Decision**:
  - Automatically prompt joining players in `PlayerJoinEvent`.
  - Do not force-kick or interrupt currently connected players on background builds.
  - Provide `/mcp reloadpack` for self-testing and `/mcp reloadpack all` (admin permission) for mass re-prompting.
  - Make `required` (boolean) and `prompt` (message) configurable per target.

## Risks / Trade-offs

- **[Risk] High network bandwidth consumption when many players download large packs simultaneously** → **Mitigation**: Serve packs with HTTP `ETag` matching the SHA-1, return `304 Not Modified` on cache hits, and allow configuring `MCP_PUBLIC_URL` pointing to a CDN or external reverse proxy if needed.
- **[Risk] Large plugin packs exhausting backend memory during extraction/merging** → **Mitigation**: Process file streams and stage extractions on disk (`/data/packs/sources/...`) rather than holding entire uncompressed archives in RAM.
- **[Risk] External players unable to download pack if backend binds to localhost** → **Mitigation**: Add target-level `public_download_url` setting and global `MCP_PUBLIC_URL` environment variable to ensure public address resolution.

## Migration Plan

1. Database schema migration: Add tables for `pack_sources` and `compiled_packs` associated with targets.
2. Backend API: Implement endpoints for preflight validation, source ingestion, packaging, and static downloads.
3. Frontend UI: Add Resource Pack tab in Target / Studio dashboards with build triggers, conflict dialog, and download settings.
4. Paper Agent: Add WebSocket handlers for pack readiness, sync watcher for plugin directories, and `/mcp reloadpack` command.
