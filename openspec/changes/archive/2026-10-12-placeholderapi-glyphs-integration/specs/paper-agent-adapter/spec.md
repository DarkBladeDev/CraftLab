# Spec Delta

## ADDED Requirements

### Requirement: Extensible PlaceholderAPI Router and Soft-Dependency Hook
The Paper agent SHALL provide a soft-dependency integration for PlaceholderAPI using a decoupled, domain-routed provider registry under the root expansion identifier `craftlab`, allowing domain-specific placeholder providers to resolve `%craftlab_<domain>_<params>%` requests when PlaceholderAPI is enabled on the server and degrading gracefully when PlaceholderAPI is absent.

#### Scenario: Resolving placeholder through registered domain provider
- **WHEN** PlaceholderAPI is enabled on the Paper server and evaluates `%craftlab_<domain>_<params>%` for a registered domain key
- **THEN** the expansion delegates `<params>` and the target player context to the matching domain provider and returns the resolved string

#### Scenario: Persistence across PlaceholderAPI reloads
- **WHEN** an administrator executes `/papi reload` on the server
- **THEN** the `craftlab` expansion remains registered and active because it declares persistent expansion lifecycle semantics

#### Scenario: Graceful initialization when PlaceholderAPI is not installed
- **WHEN** the Paper server starts without PlaceholderAPI installed
- **THEN** the agent initializes normally without throwing `NoClassDefFoundError` or `ClassNotFoundException` and skips expansion registration

#### Scenario: Reporting PlaceholderAPI in session handshake
- **WHEN** PlaceholderAPI is present and enabled on the Paper server during the WebSocket `hello` handshake
- **THEN** the agent includes `PlaceholderAPI` with its version and enabled status in the `detectedPlugins` array

### Requirement: Glyph Placeholder Resolution and Local Storage Synchronization
The Paper agent SHALL maintain a local persistent glyph registry (`plugins/McpAgent/glyphs.json`) synchronized when a compiled resource pack is published (`resource_pack:ready`) or during initial session synchronization, and SHALL expose a `glyph` placeholder provider resolving glyph characters by identifier, namespace-qualified identifier, hexadecimal codepoint, and MiniMessage format.

#### Scenario: Resolving glyph by identifier
- **WHEN** PlaceholderAPI evaluates `%craftlab_glyph_badge_vip%` for a synchronized glyph with ID `badge_vip` and hex `E001`
- **THEN** the glyph provider returns the raw Unicode PUA character `\uE001`

#### Scenario: Resolving glyph by explicit namespace and identifier
- **WHEN** PlaceholderAPI evaluates `%craftlab_glyph_ranks:badge_vip%` for a glyph registered in namespace `ranks` with ID `badge_vip` and hex `E002`
- **THEN** the glyph provider returns the raw Unicode PUA character `\uE002`

#### Scenario: Resolving glyph by hexadecimal codepoint
- **WHEN** PlaceholderAPI evaluates `%craftlab_glyph_hex_E001%` for a registered glyph with hex `E001`
- **THEN** the glyph provider returns the corresponding Unicode PUA character `\uE001`

#### Scenario: Resolving glyph in MiniMessage format
- **WHEN** PlaceholderAPI evaluates `%craftlab_glyph_mm_badge_vip%` for a glyph in namespace `craftlab` with ID `badge_vip` and hex `E001`
- **THEN** the glyph provider returns `<font:craftlab:default>\uE001</font>`

#### Scenario: Synchronizing glyphs on resource pack publication
- **WHEN** the agent receives a `resource_pack:ready` event containing a `glyphs` manifest array
- **THEN** the agent updates its in-memory glyph registry and persists the catalog to `plugins/McpAgent/glyphs.json`

#### Scenario: Restoring glyphs from local disk across server restarts
- **WHEN** the Paper server restarts before establishing a WebSocket connection to the control plane
- **THEN** the agent loads previously persisted glyph definitions from `plugins/McpAgent/glyphs.json` and resolves `%craftlab_glyph_<id>%` placeholders immediately on boot
