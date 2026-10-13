# Design

## Context

See `proposal.md` for motivation and scope. Currently, `CraftLab-plugin` (`McpAgent`) uses a modular strategy pattern for 1.21 Item Data Components (`ItemComponentRegistry` + `ItemComponentApplier`) and soft-dependency hooks for third-party plugins (`OraxenCatalogHook`), while persisting deployed items locally in `ItemStorage` (`plugins/McpAgent/items/`). Glyphs are authored in the backend workspace (`assets/<namespace>/font/default.json`) with globally unique PUA codepoints (`\uE000`–`\uF8FF`), but are never transmitted to `CraftLab-plugin` or exposed via PlaceholderAPI.

## Goals / Non-Goals

**Goals:**
- Provide a clean, extensible PlaceholderAPI integration in `CraftLab-plugin` where `glyph` is the initial domain provider (`%craftlab_glyph_...%`) and new domain providers (`prop`, `item`, `pack`, `agent`) can be added by implementing a single interface.
- Keep `CraftLab-plugin` completely functional on servers without PlaceholderAPI installed (strict soft-dependency isolation).
- Synchronize glyphs only on resource pack compilation/publication (`resource_pack:ready`) and agent session handshake—never on workspace CRUD edits (`POST`/`DELETE /api/v1/assets/creative/glyphs`).
- Ensure raw PUA Unicode characters returned by PlaceholderAPI render everywhere in the Minecraft client by projecting custom namespace bitmap font providers into `assets/minecraft/font/default.json` during pack compilation.

**Non-Goals:**
- Real-time WebSocket broadcasting when a glyph is created, edited, or deleted in Creative Assets Lab (draft edits require resource pack compilation before client textures/fonts exist).
- Registering separate dynamic `PlaceholderExpansion` instances per custom resource pack namespace (all CraftLab placeholders share the canonical `craftlab` expansion identifier).

## Decisions

### 1. Decoupled Router + Provider Pattern (`PlaceholderRegistry` & `PlaceholderProvider`)
- **Choice**: Create `com.mcp.agent.placeholders.PlaceholderProvider` (`String getKey()`, `String resolve(OfflinePlayer player, String params)`) and `PlaceholderRegistry` (`register(PlaceholderProvider)`, `resolve(OfflinePlayer player, String rawParams)`). `PlaceholderRegistry` splits `rawParams` on the first `_` into `<domainKey>` and `<subParams>` and dispatches to the registered provider.
- **Rationale**: Mirrors `ItemComponentRegistry` + `ItemComponentApplier`. Business logic and unit tests in `CraftLab-plugin` do not depend on `PlaceholderExpansion` or Bukkit's plugin manager, and adding future domains (`%craftlab_prop_<id>_state%`, `%craftlab_item_<id>_name%`) requires zero changes to the PAPI expansion hook.
- **Alternatives Considered**:
  - *Monolithic `PlaceholderExpansion` with `if/else` parsing*: Harder to test without PAPI runtime and couples all domain managers (`PropManager`, `ItemStorage`, `GlyphStorage`) into a single class.

### 2. Soft-Dependency Isolation via `PlaceholderApiHook` and `CraftLabPlaceholderExpansion`
- **Choice**: Add `compileOnly("me.clip:placeholderapi:2.11.6")` (from `https://repo.extendedclip.com/content/repositories/placeholderapi/`) in `build.gradle.kts` and `softdepend: [Oraxen, PlaceholderAPI]` in `plugin.yml`. `PlaceholderApiHook` checks `Bukkit.getPluginManager().isPluginEnabled("PlaceholderAPI")` before instantiating `CraftLabPlaceholderExpansion(plugin, placeholderRegistry)` and calling `.register()`.
- **Rationale**: In Java, keeping the `PlaceholderExpansion` subclass in its own class (`CraftLabPlaceholderExpansion`) only referenced when `isPluginEnabled("PlaceholderAPI")` is true prevents the JVM classloader from loading `me.clip.placeholderapi.*` when PlaceholderAPI is absent.

### 3. Canonical `%craftlab_glyph_...%` Syntax and Sub-Selectors
- **Choice**: Under `GlyphPlaceholderProvider` (`getKey() == "glyph"`), support:
  1. `%craftlab_glyph_mm_<selector>%` -> Returns `<font:<namespace>:<font_name>>\uXXXX</font>` (where `font_name` defaults to `default`, stripped of `.json`).
  2. `%craftlab_glyph_hex_<hex>%` -> Looks up a registered glyph by 4-digit hex (or converts valid PUA hex `E000`–`F8FF`) and returns the raw Unicode character.
  3. `%craftlab_glyph_<namespace>:<id>%` -> Looks up the glyph in `<namespace>` with identifier `<id>` and returns its raw character `\uXXXX`.
  4. `%craftlab_glyph_<id>%` -> Looks up `<id>` prioritizing the `craftlab` namespace first, falling back to any namespace match if unambiguous, and returns `\uXXXX`.
- **Rationale**: PlaceholderAPI routes expansions strictly by the prefix before the first underscore (`craftlab`). Supporting `<namespace>:<id>` inside the `glyph` provider allows custom namespaces while keeping a single expansion root (`%craftlab_...%`).

### 4. Publication-Bound Synchronization & Local `GlyphStorage`
- **Choice**:
  - Do **not** broadcast WebSocket messages from `creative.py` when glyphs are created, updated, or deleted.
  - During `POST /api/v1/packs/build` (`packs.py`), scan the merged pack directory (`scan_registered_glyphs(merged_dir)`), store the resulting list in `build_summary["glyphs"]`, and include `"glyphs": compiled_glyphs` inside the `resource_pack:ready` event sent to the target agent (or all online targets if `target_id` is global/unspecified).
  - During the WebSocket `hello` handshake in `gateway/manager.py`, if a latest compiled pack exists for the target (or global fallback) and has `build_summary.glyphs`, send a `resource_pack:glyphs_sync` (or include `glyphs` in the post-handshake sync) so newly connected servers immediately populate their `GlyphStorage`.
  - In `CraftLab-plugin`, `GlyphStorage` stores the glyph list in memory (indexed by `namespace:id`, `id`, and `hex`) and persists it to `plugins/McpAgent/glyphs.json`.
- **Rationale**: Guarantees that in-game placeholders always match the glyphs actually compiled into the active resource pack and remain available immediately on server restart even if the control plane is unreachable.

### 5. Root `assets/minecraft/font/default.json` Bitmap Projection
- **Choice**: In `SemanticMerger.merge_layers_to_directory` (`pack_merger.py`), after merging all layers, collect all `bitmap` providers from `assets/*/font/default.json` (where `<namespace> != "minecraft"`) and merge them into `assets/minecraft/font/default.json` using `SemanticMerger.merge_font_json`.
- **Rationale**: Legacy chat plugins, TAB, scoreboards, and hologram plugins render strings returned by PlaceholderAPI using Minecraft's default font (`minecraft:default`). Because CraftLab already enforces global PUA uniqueness (`\uE000`–`\uF8FF`) across all namespaces, projecting custom namespace `default.json` bitmap providers into `assets/minecraft/font/default.json` makes raw `\uXXXX` characters render out-of-the-box everywhere while preserving `<font:<namespace>:default>` compatibility.

## Risks / Trade-offs

- **[Risk] Relative texture paths in `font/default.json` when projected to `minecraft:default`** → **Mitigation**: When projecting a bitmap provider from `assets/<ns>/font/default.json` into `assets/minecraft/font/default.json`, normalize its `"file"` property to include the explicit `<ns>:` prefix if it lacks a namespace prefix (e.g., `"font/badge.png"` becomes `"<ns>:font/badge.png"`), ensuring Minecraft resolves the PNG in the original namespace's `textures/` directory.
- **[Risk] Duplicate glyph IDs across different custom namespaces** → **Mitigation**: `GlyphStorage` indexes both `<namespace>:<id>` and unqualified `<id>` (preferring `craftlab:<id>` first, then first registered), while the UI generates `%craftlab_glyph_<id>%` for `craftlab` and `%craftlab_glyph_<namespace>:<id>%` for custom namespaces.
