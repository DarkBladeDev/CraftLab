# Proposal

## Why

The Creative Assets Lab already allows authoring custom PUA Unicode glyphs (`\uE000`–`\uF8FF`) and displays PlaceholderAPI integration snippets in the UI, but `CraftLab-plugin` (`McpAgent`) currently has no PlaceholderAPI hook, no local glyph storage, and no synchronization mechanism when resource packs are compiled and published. Integrating PlaceholderAPI via an extensible provider architecture enables servers to immediately resolve custom glyphs (and future domain placeholders like props, items, and packs) across chat, tablists, scoreboards, and GUIs without manual configuration.

## What Changes

- **Extensible PlaceholderAPI Architecture in `CraftLab-plugin`**:
  - Add `PlaceholderAPI` as an optional `compileOnly` dependency and `softdepend` in `plugin.yml`.
  - Introduce `PlaceholderProvider` (strategy interface) and `PlaceholderRegistry` (domain router decoupled from PAPI classes) under `com.mcp.agent.placeholders`.
  - Implement `CraftLabPlaceholderExpansion` (`identifier = "craftlab"`, `persist = true`) and `PlaceholderApiHook` for safe conditional registration when PlaceholderAPI is present on the server, reporting `PlaceholderAPI` in `detectedPlugins` during the WebSocket `hello` handshake.
- **Glyph Placeholder Provider & Local Persistence (`GlyphStorage`)**:
  - Implement `GlyphStorage` in `CraftLab-plugin` (`plugins/McpAgent/glyphs.json`) to persist synchronized glyph definitions across server restarts and `/mcp reload`.
  - Implement `GlyphPlaceholderProvider` (`key = "glyph"`) resolving:
    - `%craftlab_glyph_<id>%` (and explicit namespace `%craftlab_glyph_<namespace>:<id>%`) -> raw Unicode PUA character (`\uXXXX`).
    - `%craftlab_glyph_hex_<hex>%` -> raw Unicode character by 4-digit PUA hex code.
    - `%craftlab_glyph_mm_<id>%` (and `<namespace>:<id>`) -> MiniMessage formatted string `<font:<namespace>:default>\uXXXX</font>`.
- **Publication-Bound Glyph Synchronization (No Real-Time CRUD Broadcast)**:
  - Keep workspace glyph authoring (`POST`/`DELETE /api/v1/assets/creative/glyphs`) strictly local to the workspace without triggering WebSocket broadcasts on draft edits.
  - Synchronize the compiled glyph catalog during resource pack build/publication (`POST /api/v1/packs/build` via the `resource_pack:ready` event payload and `build_summary`) and upon agent session establishment when an active compiled pack exists for the target.
- **Root Font Projection in Resource Pack Merger**:
  - Project custom namespace bitmap font providers (`assets/<namespace>/font/default.json`) into `assets/minecraft/font/default.json` during pack compilation (`SemanticMerger`) so raw PUA characters returned by PlaceholderAPI render directly in legacy chat, scoreboards, and tablists without requiring `<font:...>` tags.
- **Canonical Placeholder Snippet Alignment**:
  - Update `register_glyph` in `CraftLab-backend` and `GlyphStudioTab.tsx` in `CraftLab-frontend` so the PlaceholderAPI copy snippet consistently uses the canonical `%craftlab_glyph_<id>%` (or `%craftlab_glyph_<namespace>:<id>%` for non-default namespaces) format.

## Capabilities

### New Capabilities
<!-- None: all changes extend existing capabilities -->

### Modified Capabilities
- `paper-agent-adapter`: Add extensible PlaceholderAPI integration (`PlaceholderRegistry`, `PlaceholderProvider`, `CraftLabPlaceholderExpansion`), local `GlyphStorage` persistence (`glyphs.json`), `GlyphPlaceholderProvider` resolution rules, and glyph catalog updates upon `resource_pack:ready` / session sync.
- `resource-pack-pipeline`: Project custom namespace `font/default.json` bitmap providers into `assets/minecraft/font/default.json` during compilation and include the compiled glyph catalog in `build_summary` and `resource_pack:ready` notifications.
- `creative-assets-lab`: Align generated PlaceholderAPI tokens in glyph registration and the simulator UI to the canonical `%craftlab_glyph_...%` syntax.

## Impact

- **`CraftLab-plugin`**: `build.gradle.kts`, `plugin.yml`, `McpAgentPlugin.java`, `AgentWebSocketClient.java`, new `com.mcp.agent.storage.GlyphStorage`, and new `com.mcp.agent.placeholders.*` package with unit tests.
- **`CraftLab-backend`**: `app/domain/glyphs.py`, `app/domain/pack_merger.py`, `app/api/packs.py`, `app/gateway/manager.py`, and backend test suite.
- **`CraftLab-frontend`**: `src/features/creative/tabs/GlyphStudioTab.tsx`.
