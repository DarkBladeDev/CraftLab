# Spec Delta

## MODIFIED Requirements

### Requirement: In-Game Chat and Tablist Simulator
The system SHALL provide an interactive preview simulator rendering live Minecraft-styled Chat and Tablist displays that visually updates whenever glyph attributes (height, baseline ascent, or sprite texture) are modified, and SHALL provide one-click copy actions for MiniMessage tags (`<font:namespace:default>\uXXXX</font>`), LuckPerms prefix formatting, and canonical PlaceholderAPI tokens (`%craftlab_glyph_<id>%` for the default `craftlab` namespace and `%craftlab_glyph_<namespace>:<id>%` for custom namespaces) without broadcasting WebSocket events during draft glyph creation, editing, or deletion.

#### Scenario: Real-time chat preview update
- **WHEN** user modifies the baseline ascent or height of an active rank glyph
- **THEN** system immediately adjusts the vertical alignment and rendered scale of the glyph in the live chat and tablist simulators

#### Scenario: Copying canonical PlaceholderAPI glyph token
- **WHEN** user views or registers a glyph in namespace `craftlab` with identifier `badge_vip` (or in custom namespace `ranks` with identifier `badge_vip`)
- **THEN** system displays and copies `%craftlab_glyph_badge_vip%` (or `%craftlab_glyph_ranks:badge_vip%` for custom namespaces) as the PlaceholderAPI snippet without emitting WebSocket synchronization messages on draft save
