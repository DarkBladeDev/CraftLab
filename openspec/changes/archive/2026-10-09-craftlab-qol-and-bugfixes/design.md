# Design

## Context

See `proposal.md` for overall motivation.
CraftLab integrates a FastAPI backend (`CraftLab-backend`), a React/Tailwind frontend (`CraftLab-frontend`), and a Paper 1.21.1 plugin (`CraftLab-plugin`) using PacketEvents for packet manipulation. The current codebase contains initial work on block models, catalog building, and revision checks that must be reconciled into a clean, complete architecture.

## Goals / Non-Goals

**Goals:**
- Provide full filesystem CRUD (create, rename, upload, delete) in Asset Explorer with strict namespace security.
- Eliminate visual texture offset bugs in Content Viewer at any zoom multiplier (1x–16x).
- Enable full lifecycle control over pack layers (main workspace manifest attributes and external pack priorities/names).
- Clearly separate placed 3D block models from handheld item models across Studio UI, backend, and Paper plugin.
- Support "Lie Down" prop interactions via PacketEvents pose synchronization.
- Provide a responsive, collapsible multi-source asset browser backed by a complete 1,332-item vanilla catalog.

**Non-Goals:**
- Creating custom entities or mob models (limited to item display props and blocks).
- Modifying Bukkit vanilla bed sleeping logic or bed spawn points (lie-down is purely visual/cosmetic).

## Decisions

### 1. Asset Workspace Filesystem Operations & Security
- **Decision**: Introduce `POST /v1/packs/workspace/rename` accepting `{ "old_path": str, "new_path": str }`.
- **Validation**: Both paths are strictly validated through `safe_resolve_workspace_path` against `data/packs/workspace/`. All path segments must match `^[a-z0-9_.-]+$`. Existing destination paths trigger HTTP 409 Conflict.
- **Alternatives Considered**: Direct WebDAV or arbitrary shell rename; rejected due to security risks and lack of Minecraft identifier validation.

### 2. Content Viewer Display Layout Fix
- **Decision**: Replace arbitrary scale margins (`(zoomLevel - 1) * 20px`) with a synchronized layout box. The container with the checkered background dynamically dimensions to `naturalWidth * zoomLevel` and `naturalHeight * zoomLevel`, with the image rendered inside via CSS `image-rendering: pixelated; width: 100%; height: 100%`.
- **Alternatives Considered**: Using HTML5 Canvas or WebGL; rejected as plain CSS sizing is lighter, retains crisp pixel scaling, and eliminates layout desynchronization.

### 3. Resource Pack Layer Configuration Architecture
- **Decision**:
  - Expose workspace manifest controls via `GET /v1/packs/workspace/config` and `PUT /v1/packs/workspace/config`, directly mutating `data/packs/workspace/pack.mcmeta`.
  - Expose external source modification via `PATCH /v1/packs/sources/{source_id}` updating `name`, `layer_priority`, and `is_active` in SQLite via `PackRepository`.
- **Alternatives Considered**: Storing workspace metadata purely in database; rejected because `pack.mcmeta` must remain the single source of truth on disk for pack compilation.

### 4. Prop Dual-Model Representation & Barrier Rules
- **Decision**:
  - `block_model`: Model identifier used for the world-placed `ItemDisplay` entity.
  - `item_model`: Model identifier used for the item in hand, inventory, or dropped upon breaking.
  - If `block_model` is unspecified, it defaults to `item_model` for backwards compatibility.
  - When `hitbox_type === 'solid'`, the UI disables `hardness` and `tool_type`, displaying an explanatory note that barrier blocks are unbreakable in survival.
- **Runtime Agent ("Lie Down")**:
  - In `PropInteractionListener.java`, when `interaction_type === "lay"`, the player mounts an invisible marker armor stand positioned at `seat_height`.
  - PacketEvents dispatches an `EntityMetadata` packet with `EntityPose.SLEEPING` for the player entity to render the horizontal laying pose.

### 5. Vanilla Catalog Distribution
- **Decision**: Store `vanilla_items_1.21.json` within `CraftLab-backend/app/assets/vanilla_items_1.21.json` (tracked in version control) with fallback lazy loading.
- **Alternatives Considered**: Fetching on every server startup from GitHub; rejected because offline development and air-gapped environments must remain fully functional.

## Risks / Trade-offs

- **[Risk] Collision during file/folder rename** → Mitigation: Atomic existence check on destination; if target exists, return 409 and abort without file deletion.
- **[Risk] Breaking changes to existing prop definitions** → Mitigation: Database migration (`database.py`) adds `block_model` nullable; serialization defaults `block_model` to `item_model` when absent.
- **[Risk] PacketEvents metadata index variation across MC versions** → Mitigation: Validate target protocol version (1.21.1 uses index 6 for player pose) and wrap in graceful try-catch fallback.
