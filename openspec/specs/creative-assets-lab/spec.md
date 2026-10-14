# Creative Assets Lab

## Purpose

Provides a unified creative workspace for authoring, testing, and managing Minecraft 1.21.2+ equipment models, rank prefix glyphs, 3D spatialized sound events, and particle VFX with zero-boilerplate automation and live in-game simulators.

## Requirements

### Requirement: Unified Creative Assets Lab Navigation and Workspace
The system SHALL provide a dedicated top-level workspace view within the platform frontend entitled "Creative Assets Lab", presenting a segmented pill navigation bar allowing users to switch between four distinct sub-modules: "Glyphs & Rank Prefixes", "Equipment & Armor (1.21.2+)", "Sound Events (SFX)", and "Particles & VFX".

#### Scenario: Switching between sub-modules
- **WHEN** user clicks on any sub-module navigation pill (Glyphs, Equipment, Sounds, or Particles)
- **THEN** system immediately displays the corresponding workspace panel without reloading the application or losing unsaved draft state

### Requirement: PUA Unicode Glyph Allocation and Manual Hexadecimal Override
The system SHALL maintain a Private Use Area (PUA) unicode registry within the range `\uE000` through `\uF8FF` across project namespaces, automatically allocating the next unassigned codepoint when a new glyph sprite is registered, and SHALL allow authors to manually specify a 4-digit hexadecimal codepoint with real-time collision detection alerting when the codepoint is already bound to another glyph.

#### Scenario: Automatic glyph codepoint assignment
- **WHEN** user creates a new glyph with identifier `badge_vip` without specifying a custom codepoint
- **THEN** system assigns the lowest available PUA codepoint, updates the font configuration, and displays the allocated unicode value

#### Scenario: Manual codepoint collision detection
- **WHEN** user inputs a custom hexadecimal codepoint that is already bound to an active glyph in the project
- **THEN** system displays an active collision warning badge and prevents saving until an unused codepoint is provided

### Requirement: In-Game Chat and Tablist Simulator
The system SHALL provide an interactive preview simulator rendering live Minecraft-styled Chat and Tablist displays that visually updates whenever glyph attributes (height, baseline ascent, or sprite texture) are modified, and SHALL provide one-click copy actions for MiniMessage tags (`<font:namespace:default>\uXXXX</font>`), LuckPerms prefix formatting, and canonical PlaceholderAPI tokens (`%craftlab_glyph_<id>%` for the default `craftlab` namespace and `%craftlab_glyph_<namespace>:<id>%` for custom namespaces) without broadcasting WebSocket events during draft glyph creation, editing, or deletion.

#### Scenario: Real-time chat preview update
- **WHEN** user modifies the baseline ascent or height of an active rank glyph
- **THEN** system immediately adjusts the vertical alignment and rendered scale of the glyph in the live chat and tablist simulators

#### Scenario: Copying canonical PlaceholderAPI glyph token
- **WHEN** user views or registers a glyph in namespace `craftlab` with identifier `badge_vip` (or in custom namespace `ranks` with identifier `badge_vip`)
- **THEN** system displays and copies `%craftlab_glyph_badge_vip%` (or `%craftlab_glyph_ranks:badge_vip%` for custom namespaces) as the PlaceholderAPI snippet without emitting WebSocket synchronization messages on draft save

### Requirement: 1.21.2+ Equipment Model and Armor Layer Authoring
The system SHALL provide an equipment model editor that generates standard Minecraft 1.21.4+ `assets/<namespace>/equipment/<id>.json` descriptors, supporting a `layers` object mapping valid layer type keys (`humanoid`, `humanoid_leggings`, `wings`, `horse_body`, `llama_body`, `wolf_body`, `pig_saddle`, `strider_saddle`, `camel_saddle`, `horse_saddle`, `donkey_saddle`, `mule_saddle`, `skeleton_horse_saddle`, `zombie_horse_saddle`, `humanoid_baby`) to lists of layer definitions with resource location `texture` strings, optional `dyeable` objects with integer `color_when_undyed` tints, and optional `use_player_texture` flags for wings, SHALL transparently discover and read legacy descriptors located at `assets/<namespace>/models/equipment/<id>.json`, and SHALL provide an interactive 2D/3D paper doll mannequin preview showing armor layers on Steve and Alex player models.

#### Scenario: Creating a multi-layer equipment model
- **WHEN** user configures an equipment model with base and dyeable overlay layers across `humanoid` and `humanoid_leggings` targets
- **THEN** system validates layer types and structures, renders the combined appearance on the paper doll mannequin preview, and generates a valid Minecraft 1.21.4+ descriptor under `assets/<namespace>/equipment/<id>.json`

#### Scenario: Transparent legacy descriptor ingestion
- **WHEN** user loads a workspace containing legacy descriptors at `assets/<namespace>/models/equipment/<id>.json`
- **THEN** system discovers and normalizes the models into the canonical layer-type structure without data loss

### Requirement: Sound Events and Spatial Mono Audio Diagnostic
The system SHALL provide a sound event authoring interface managing `assets/<namespace>/sounds.json` definitions with multi-sample audio variations, pitch ranges, and volume weights, SHALL automatically probe uploaded `.ogg` audio files to detect audio channel count, SHALL display a warning badge when an uploaded audio is 2-channel Stereo alerting that stereo audio bypasses 3D spatial distance attenuation in Minecraft, and SHALL provide a 1-click action to downmix stereo audio into a single mono channel.

#### Scenario: Detecting stereo audio upload
- **WHEN** user uploads a 2-channel stereo `.ogg` audio file into a sound event intended for positional playback
- **THEN** system displays a warning badge indicating that stereo audio bypasses positional 3D attenuation in Minecraft

#### Scenario: Downmixing stereo to mono
- **WHEN** user clicks the "Convert to Mono" action on a stereo audio sample
- **THEN** system performs a symmetric channel downmix `(Left + Right) / 2`, updates the audio file to single-channel mono, and updates the diagnostic status to verified 3D positional audio

### Requirement: Real-Time Particle VFX Authoring and 60 FPS Canvas Simulator
The system SHALL provide a particle definition editor generating valid `assets/<namespace>/particles/<id>.json` files referencing custom sprite textures, featuring a real-time 60 FPS HTML5 canvas particle emitter simulator with configurable upward velocity (gravity/lift), dispersion spread, and spawn rate, and SHALL generate ready-to-use in-game `/particle` commands.

#### Scenario: Simulating particle emission
- **WHEN** user adjusts the spread and velocity sliders in the particle editor
- **THEN** canvas emitter immediately simulates the adjusted particle trajectory and updates the generated `/particle` command string

### Requirement: Zero-Boilerplate Automation and Bidirectional Raw Schema Drawer
The system SHALL automatically scaffold required resource pack directory paths (`font/`, `equipment/`, `sounds/`, `particles/`, `textures/`) and synthesize JSON metadata when assets are created in visual mode, and SHALL provide a collapsible "Schema & Raw JSON" drawer with live Monaco/code editing allowing manual edits with real-time schema validation against Minecraft 1.21.4+ equipment specifications.

#### Scenario: Synchronizing raw JSON edits
- **WHEN** user edits the raw JSON in the Schema Drawer and submits changes
- **THEN** system validates the payload against the official Minecraft equipment model schema, reports syntax or structural errors if invalid, and updates the visual editor controls when valid

### Requirement: Legacy Shader Metadata and Multi-Version Equipment Diagnostics
The Creative Assets Lab Equipment Model editor SHALL provide a dedicated Multi-Version Compatibility Diagnostic panel within the equipment inspector. The system MUST compute and display the model's assigned legacy shader layer index, 24-bit integer ID, RGB hexadecimal color code (e.g. `#000001`), and vertical atlas offset percentage for clients on Minecraft 1.20.0 through 1.21.3, alongside the canonical Minecraft 1.21.4+ `assets/<namespace>/equipment/<id>.json` structure and 1.21.2-1.21.3 `models/equipment/<id>.json` mirror status.

#### Scenario: Inspecting multi-version equipment diagnostics
- **WHEN** user selects an active equipment model in Creative Assets Lab
- **THEN** inspector displays the canonical 1.21.4+ asset key (`namespace:id`), the calculated legacy shader index, the assigned 24-bit RGB hex tint, and the paper doll preview showing combined layers

#### Scenario: Alerting when textures are incompatible with vertical atlas
- **WHEN** user uploads layer textures with non-standard aspect ratios or differing dimensions across humanoid layers
- **THEN** diagnostic panel warns of potential atlas alignment distortion and provides a one-click action to normalize texture dimensions to canonical 64x32 or 64x64 dimensions
