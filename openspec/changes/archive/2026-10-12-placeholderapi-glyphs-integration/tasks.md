# Tasks

## 1. Backend & Frontend Canonical Glyph Snippets and Pack Font Projection

- [x] 1.1 Update `register_glyph` in `CraftLab-backend/app/domain/glyphs.py` and `CraftLab-frontend/src/features/creative/tabs/GlyphStudioTab.tsx` to generate canonical PlaceholderAPI tokens (`%craftlab_glyph_<id>%` for `craftlab` and `%craftlab_glyph_<namespace>:<id>%` for custom namespaces) without WebSocket broadcasts on CRUD, and verify with `pytest tests/test_glyphs.py tests/test_creative_api.py`
- [x] 1.2 Update `SemanticMerger.merge_layers_to_directory` in `CraftLab-backend/app/domain/pack_merger.py` to project custom namespace bitmap font providers (`assets/<ns>/font/default.json`) with normalized `<ns>:` file paths into `assets/minecraft/font/default.json`, and verify with unit tests in `tests/test_pack_merger.py`
- [x] 1.3 Update `build_resource_pack` in `CraftLab-backend/app/api/packs.py` and handshake handling in `CraftLab-backend/app/gateway/manager.py` to scan compiled glyphs from `merged_dir`, store them in `build_summary["glyphs"]`, and include `"glyphs"` in `resource_pack:ready` and initial session synchronization, verifying with `pytest tests/test_packs_api.py tests/test_gateway.py`

## 2. Paper Agent Local Glyph Storage & WebSocket Synchronization

- [x] 2.1 Implement `GlyphStorage` (`com.mcp.agent.storage.GlyphStorage`) in `CraftLab-plugin` to store synchronized glyphs in memory (indexed by `namespace:id`, `id`, and `hex`) and persist/load them from `plugins/McpAgent/glyphs.json`, verifying with a new JUnit test `GlyphStorageTest`
- [x] 2.2 Update `AgentWebSocketClient` and `McpAgentPlugin` in `CraftLab-plugin` to ingest the `glyphs` array from `resource_pack:ready` events into `GlyphStorage`, reload `GlyphStorage` on `/mcp reload`, and report `PlaceholderAPI` in `detectedPlugins` during `hello` when enabled, verifying with JUnit tests in `AgentWebSocketClientTest`

## 3. Extensible PlaceholderAPI Router, Hook, and Glyph Provider

- [x] 3.1 Add `PlaceholderAPI` repository and `compileOnly` / `testImplementation` dependency in `CraftLab-plugin/build.gradle.kts` and add `PlaceholderAPI` to `softdepend` in `CraftLab-plugin/src/main/resources/plugin.yml`, verifying that `./gradlew compileJava` succeeds
- [x] 3.2 Implement `PlaceholderProvider` interface and `PlaceholderRegistry` router in `com.mcp.agent.placeholders` to dispatch `<domainKey>_<subParams>` requests, and implement `GlyphPlaceholderProvider` (`key = "glyph"`) supporting `<id>`, `<namespace>:<id>`, `hex_<hex>`, and `mm_<id>` selectors, verifying with JUnit tests in `PlaceholderRegistryTest`
- [x] 3.3 Implement `CraftLabPlaceholderExpansion` (`identifier = "craftlab"`, `persist = true`) and `PlaceholderApiHook` in `com.mcp.agent.placeholders` and wire registration in `McpAgentPlugin.onEnable()`, verifying the full plugin test suite passes via `./gradlew test`
