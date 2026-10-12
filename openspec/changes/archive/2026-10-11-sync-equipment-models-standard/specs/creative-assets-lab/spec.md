# Spec Delta: Creative Assets Lab

## MODIFIED Requirements

### Requirement: 1.21.2+ Equipment Model and Armor Layer Authoring
The system SHALL provide an equipment model editor that generates standard Minecraft 1.21.4+ `assets/<namespace>/equipment/<id>.json` descriptors, supporting a `layers` object mapping valid layer type keys (`humanoid`, `humanoid_leggings`, `wings`, `horse_body`, `llama_body`, `wolf_body`, `pig_saddle`, `strider_saddle`, `camel_saddle`, `horse_saddle`, `donkey_saddle`, `mule_saddle`, `skeleton_horse_saddle`, `zombie_horse_saddle`, `humanoid_baby`) to lists of layer definitions with resource location `texture` strings, optional `dyeable` objects with integer `color_when_undyed` tints, and optional `use_player_texture` flags for wings, SHALL transparently discover and read legacy descriptors located at `assets/<namespace>/models/equipment/<id>.json`, and SHALL provide an interactive 2D/3D paper doll mannequin preview showing armor layers on Steve and Alex player models.

#### Scenario: Creating a multi-layer equipment model
- **WHEN** user configures an equipment model with base and dyeable overlay layers across `humanoid` and `humanoid_leggings` targets
- **THEN** system validates layer types and structures, renders the combined appearance on the paper doll mannequin preview, and generates a valid Minecraft 1.21.4+ descriptor under `assets/<namespace>/equipment/<id>.json`

#### Scenario: Transparent legacy descriptor ingestion
- **WHEN** user loads a workspace containing legacy descriptors at `assets/<namespace>/models/equipment/<id>.json`
- **THEN** system discovers and normalizes the models into the canonical layer-type structure without data loss

### Requirement: Zero-Boilerplate Automation and Bidirectional Raw Schema Drawer
The system SHALL automatically scaffold required resource pack directory paths (`font/`, `equipment/`, `sounds/`, `particles/`, `textures/`) and synthesize JSON metadata when assets are created in visual mode, and SHALL provide a collapsible "Schema & Raw JSON" drawer with live Monaco/code editing allowing manual edits with real-time schema validation against Minecraft 1.21.4+ equipment specifications.

#### Scenario: Synchronizing raw JSON edits
- **WHEN** user edits the raw JSON in the Schema Drawer and submits changes
- **THEN** system validates the payload against the official Minecraft equipment model schema, reports syntax or structural errors if invalid, and updates the visual editor controls when valid
