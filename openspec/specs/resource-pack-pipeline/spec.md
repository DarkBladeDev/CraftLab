# Resource Pack Pipeline

## Purpose
Provides automated resource pack management, semantic JSON merging of multi-source packs, pre-flight collision detection, deterministic zip packaging, SHA-1 integrity hashing, and HTTP distribution for Minecraft 1.21 assets.

## Requirements

### Requirement: Pack Source Storage and Ingestion
The system SHALL maintain a repository of pack sources comprising Studio project assets, uploaded third-party zip archives, and automated plugin pack snapshots synchronized from connected server agents, structured with an explicit layer priority hierarchy, SHALL parse `pack.mcmeta` manifests on imported archives to normalize external overlay directories and format bounds into canonical CraftLab overlay targets (`root`, `overlay_v1_21_2`, and `overlay_v1_21_4`), and SHALL support updating layer metadata (name, priority, active state) and deleting registered pack sources.

#### Scenario: Ingest external zip archive
- **WHEN** an operator uploads a valid resource pack `.zip` file via the web management interface
- **THEN** the system extracts and registers the pack source, parses `pack.mcmeta` to normalize foreign overlay directories to canonical targets (`root`, `overlay_v1_21_2`, `overlay_v1_21_4`), and stores layer precedence and namespaces in the pack repository

#### Scenario: Ingest agent synchronized pack
- **WHEN** an agent uploads an extracted plugin pack snapshot from its local filesystem
- **THEN** the system registers or updates the corresponding agent pack source and records its synchronization timestamp

#### Scenario: Updating pack source attributes
- **WHEN** an operator modifies the display name, layer priority, or active status of a registered pack source
- **THEN** the system persists the updated layer attributes and reflects the new evaluation priority in pre-flight and compilation workflows

#### Scenario: Deleting a registered pack source
- **WHEN** an operator deletes an imported pack source
- **THEN** the system removes the source record and associated storage files from disk

### Requirement: Pre-Flight Collision Detection
The system MUST perform pre-flight conflict analysis across all active pack layers prior to compilation, detecting CustomModelData overlaps on identical item materials, conflicting item model definitions, conflicting binary asset paths, conflicting `item_model` component identifiers, overlapping core shader programs across layers, missing physical texture files referenced by JSON models, non-power-of-two texture dimensions violating mipmap safety, and animated textures lacking `.png.mcmeta` declarations.

#### Scenario: CustomModelData collision detected
- **WHEN** a Studio item definition and an ingested plugin pack define the same CustomModelData integer on the same base Minecraft item material
- **THEN** the pre-flight check returns a validation error reporting the collision, both conflicting resource identifiers, and direct navigation links to the items

#### Scenario: Clean pre-flight validation
- **WHEN** all active layers contain non-overlapping CustomModelData indices, valid resource structures, matching texture files, and non-conflicting shaders
- **THEN** the pre-flight check returns success with a summary of total textures, models, sound events, font definitions, and shader programs

#### Scenario: Item model identifier collision detected
- **WHEN** two distinct items across active layers declare identical `item_model` identifiers
- **THEN** the pre-flight check flags an error with the colliding identifier and layer names

#### Scenario: Core shader collision detected
- **WHEN** two active layers provide differing implementations of the same core shader program (e.g. `shaders/core/rendertype_text.vsh`)
- **THEN** the pre-flight check generates a collision warning detailing both source layers and identifying which layer takes precedence

#### Scenario: Missing texture reference detected
- **WHEN** a JSON model references a texture path (e.g. `studio:item/ruby_dagger`) that does not exist on disk in any active layer
- **THEN** the pre-flight check flags a validation error detailing the missing texture path and the referencing model

#### Scenario: Mipmap dimension and animation metadata warning
- **WHEN** an ingested PNG texture has dimensions that are not powers of two, or has a vertical aspect ratio indicating an animated spritesheet without an accompanying `.png.mcmeta` file
- **THEN** the pre-flight check returns a warning specifying the texture path and recommended correction

### Requirement: Universal Hybrid Pack Overlays Compilation
The resource pack compiler MUST construct a unified, backwards- and forwards-compatible resource pack archive with `pack_format: 34`, dynamic operator-configurable `supported_formats: {"min_inclusive": 34, "max_inclusive": <max_format>}` (defaulting to 65), and an ordered, cumulative overlay chain comprising `overlay_v1_21_2` (formats 42 to `max_inclusive`) for Item Definition V2 model dispatches and `overlay_v1_21_4` (formats 46 to `max_inclusive`) for modernized shader pipelines and render passes, while preserving common textures, sounds, and fonts strictly in the root namespace without duplication.

#### Scenario: Compile universal multi-version pack archive
- **WHEN** the compiler builds a resource pack for distribution with operator-configured format boundaries
- **THEN** the root `pack.mcmeta` includes `supported_formats` spanning format 34 to `max_inclusive` (default 65), `overlay_v1_21_2` mapping formats 42 to `max_inclusive`, and `overlay_v1_21_4` mapping formats 46 to `max_inclusive`

#### Scenario: Shared assets asset placement
- **WHEN** the compiler packages textures, sound files, font providers, and atlas definitions
- **THEN** these assets are written strictly to the root `assets/` directory without duplication inside the overlay directory

#### Scenario: Overlay evaluation ordering
- **WHEN** a Minecraft 1.21.4 client (format 46) loads the compiled resource pack
- **THEN** the client sequentially evaluates root assets, applies `overlay_v1_21_2` for modern item definitions, and applies `overlay_v1_21_4` for updated shader pipelines

### Requirement: Dual-Projection Item Model Synthesizer
The compiler and merger engine MUST synthesize dual model projections from an intermediate canonical model mapping: generating legacy `models/item/<material>.json` predicate overrides for 1.21.0 - 1.21.1 clients, and modern `items/<material>.json` Item Definition V2 select structures inside `overlay_v1_21_2` for 1.21.2+ clients.

#### Scenario: Synthesize modern item definition from legacy source
- **WHEN** an ingested pack layer defines custom model data overrides in `assets/minecraft/models/item/diamond_sword.json`
- **THEN** the compiler synthesizes a matching `items/diamond_sword.json` in `overlay_v1_21_2` with `minecraft:select` on `custom_model_data`

#### Scenario: Synthesize legacy override from modern definition
- **WHEN** an ingested pack layer defines `assets/minecraft/items/diamond_sword.json` with a `select` property on `custom_model_data`
- **THEN** the compiler synthesizes the corresponding `overrides` array inside `assets/minecraft/models/item/diamond_sword.json` in the base layer

### Requirement: Semantic JSON Configuration Merging
The merger engine MUST perform deep semantic merging for core Minecraft configuration files rather than raw file overwrites, specifically merging `sounds.json` audio event keys, concatenating `font/*.json` provider entries, synthesizing texture atlas definitions in `atlases/blocks.json` and `atlases/gui.json` via namespace induction, merging `lang/*.json` translation mappings, and merging item model definitions and overrides.

#### Scenario: Merging multiple sound definitions
- **WHEN** two pack layers define entries in `assets/minecraft/sounds.json`
- **THEN** the compiled `sounds.json` preserves all distinct sound event keys and merges nested sound properties without dropping existing clips

#### Scenario: Merging item model overrides
- **WHEN** multiple layers define model overrides for a vanilla item like `diamond_sword.json`
- **THEN** the compiled item model merges all `overrides` entries sorted in ascending order of their `custom_model_data` values

#### Scenario: Merging translation mappings
- **WHEN** multiple pack layers supply translations in `assets/*/lang/*.json`
- **THEN** the compiled language files contain the union of translation keys with higher priority layers overriding lower priority ones

### Requirement: Deterministic Zip Compilation and SHA-1 Hashing
The compiler MUST build resource pack `.zip` archives with deterministic entry ordering, normalized timestamps, and fixed compression levels so that byte-identical archives produce identical 40-character hexadecimal SHA-1 checksums across builds.

#### Scenario: Repeated compilation without changes
- **WHEN** the pack compiler builds a resource pack archive twice from identical source content
- **THEN** both resulting `.zip` files have identical file byte sizes and produce the exact same SHA-1 hash

### Requirement: HTTP Distribution and Cache Headers
The distribution service MUST serve compiled resource pack archives over HTTP via `GET /api/v1/packs/{target_id}/download` with `Content-Type: application/zip`, `ETag` matching the archive's SHA-1 hash, and aggressive client cache-control headers.

#### Scenario: Client downloads resource pack with ETag
- **WHEN** an HTTP client requests the resource pack download URL
- **THEN** the server streams the zip archive with `ETag` containing the SHA-1 hash and `Content-Disposition` specifying the pack filename

#### Scenario: Client conditional request with matching ETag
- **WHEN** an HTTP client issues a `GET` request with `If-None-Match` matching the current pack SHA-1
- **THEN** the server returns HTTP `304 Not Modified` with empty body

### Requirement: Workspace Pack Layer Integration in Build Pipeline
The resource pack compiler and merger engine MUST incorporate the local workspace pack directory (`data/packs/workspace/`) into the compilation and pre-flight validation workflow as an authoring layer with priority above external imported sources and beneath dynamic studio database projections, and SHALL provide endpoints and UI controls to inspect and update the base workspace pack manifest attributes.

#### Scenario: Compiling pack with workspace assets
- **WHEN** an operator or deployment triggers `build_resource_pack`
- **THEN** the compiler merges assets from `data/packs/workspace/` into the staging directory before synthesizing the final `.zip` archive

#### Scenario: Pre-flight validation includes workspace assets
- **WHEN** the system executes pre-flight conflict validation
- **THEN** models, textures, and definitions in `data/packs/workspace/` are scanned alongside studio items and imported sources for identifier or collision errors

#### Scenario: Configuring workspace pack manifest attributes
- **WHEN** an operator updates the workspace pack description or supported format bounds in the management interface
- **THEN** the system updates `pack.mcmeta` in the workspace directory and uses the updated metadata on subsequent builds

### Requirement: Shader Pipeline Routing and Version Isolation
The compiler and merger engine MUST route shader programs according to target Minecraft client version compatibility, ensuring legacy core shaders targeting 1.21.0 - 1.21.3 are staged in root assets and modern 1.21.4+ shader pipelines are isolated within `overlay_v1_21_4`.

#### Scenario: Modern shader routing to overlay
- **WHEN** an active pack layer provides core shaders compatible with 1.21.4+ vertex formats
- **THEN** the compiler stages those shader programs inside `overlay_v1_21_4/assets/minecraft/shaders/core/`, preserving legacy shaders in root assets for older clients

#### Scenario: Legacy client shader isolation
- **WHEN** a Minecraft 1.21.1 client connects
- **THEN** the client does not load shaders from `overlay_v1_21_4`, preventing GLSL vertex format compilation errors

### Requirement: Texture Atlas Auto-Synthesis and Namespace Induction
The merger engine MUST scan all texture resource locations across compiled models and item definitions, discover all custom namespaces and directory prefixes, and automatically inject deduplicated directory and single sources into `assets/minecraft/atlases/blocks.json` and `assets/minecraft/atlases/gui.json` to prevent client missing sprite rendering failures.

#### Scenario: Custom namespace blocks atlas induction
- **WHEN** Studio models reference textures in `studio:item/*` and `studio:props/*`
- **THEN** the compiled `assets/minecraft/atlases/blocks.json` includes directory sources for `studio:item` with prefix `item/` and `studio:props` with prefix `props/`

#### Scenario: GUI sprites atlas induction
- **WHEN** pack layers contain GUI textures under `assets/*/textures/gui/sprites/**`
- **THEN** the compiled `assets/minecraft/atlases/gui.json` includes corresponding directory sources ensuring custom UI sprites are loaded into the Minecraft 1.20.2+ GUI texture atlas

#### Scenario: Deduplication and source consolidation
- **WHEN** multiple layers define single and directory sources covering overlapping paths in an atlas
- **THEN** the synthesizer consolidates entries to eliminate redundant single sprite entries covered by directory prefixes

### Requirement: Equipment Models and Armor Trims Packaging
The compiler and merger engine MUST discover and package Minecraft 1.21.4+ canonical equipment model descriptors located at `assets/<namespace>/equipment/<id>.json`, SHALL stage them within root assets and modern client overlay targets (`overlay_v1_21_4`), SHALL automatically generate backward-compatible mirror descriptors under `assets/<namespace>/models/equipment/<id>.json` within `overlay_v1_21_2` targets to maintain compatibility with 1.21.2-1.21.3 clients, SHALL verify that referenced texture paths under `textures/entity/equipment/<layer_type>/` exist during pre-flight conflict analysis, and SHALL synthesize required texture slots into `assets/minecraft/atlases/armor_trims.json`.

#### Scenario: Packaging equipment models during pack compilation
- **WHEN** resource pack compilation is triggered with custom equipment models defined in the workspace
- **THEN** compiler stages canonical descriptors under `assets/<namespace>/equipment/<id>.json` in the root archive and generates backward-compatible mirror files under `overlay_v1_21_2/assets/<namespace>/models/equipment/<id>.json`, while verifying that all referenced layer textures exist in the asset tree

### Requirement: Semantic Font Provider, Sounds, and Particle Merging
The compiler and merger engine MUST perform semantic deduplication and merging across multi-source layers for font provider definitions (`font/*.json`), concatenating bitmap and space providers while verifying that no identical PUA codepoint conflicts exist across layers, SHALL project custom namespace bitmap providers from `assets/<namespace>/font/default.json` into the root `assets/minecraft/font/default.json` so raw PUA characters render without explicit font tags, SHALL include the compiled glyph catalog in the pack `build_summary` and `resource_pack:ready` agent notifications, MUST merge `sounds.json` audio event structures combining sound sample lists, and MUST package particle definition files (`particles/*.json`) and their associated texture atlas references into the compiled archive.

#### Scenario: Merging multi-source font providers
- **WHEN** compiler merges workspace font providers with external layer font configurations
- **THEN** compiler produces a unified `assets/<namespace>/font/default.json` containing all distinct bitmap providers and reports warnings if duplicate character codepoints are encountered

#### Scenario: Projecting custom namespace glyphs into root default font
- **WHEN** compiler builds a resource pack containing custom bitmap providers in `assets/<namespace>/font/default.json`
- **THEN** compiler also merges those PUA bitmap providers into `assets/minecraft/font/default.json` so that raw PUA Unicode characters render in standard Minecraft UI contexts without requiring explicit `<font:...>` tags

#### Scenario: Publishing compiled glyph catalog on pack build
- **WHEN** resource pack compilation completes for a target server
- **THEN** compiler records the compiled glyph definitions in `build_summary.glyphs` and includes the `glyphs` array in the `resource_pack:ready` WebSocket event payload sent to the target agent

### Requirement: Legacy Armor Core Shader and Vertical Atlas Synthesis
The pack compiler and merger engine SHALL provide automated vertical armor atlas synthesis and core shader packaging for clients prior to Minecraft 1.21.2 when the workspace compatibility profile is configured to `hybrid_shaders`. The engine MUST discover all canonical equipment model descriptors (`assets/<namespace>/equipment/<id>.json`), collect their referenced `humanoid` (layer 1) and `humanoid_leggings` (layer 2) texture PNG files, dynamically stitch them into vertical atlas sheets placed at `assets/minecraft/textures/models/armor/leather_layer_1.png` and `leather_layer_2.png`, assign a deterministic 1-based layer index $k \in [1, N]$ mapped to a 24-bit RGB value to each equipment model, and inject an adapted LessFancyPants GLSL core shader (`rendertype_armor_cutout_no_cull.json`, `.vsh`, `.fsh`) into root assets (`assets/minecraft/shaders/core/`) targeting client formats 34 through 45 (1.20.0 to 1.21.3) with `#define TOTAL_LAYERS` dynamically configured, while strictly omitting legacy shaders from `overlay_v1_21_4`.

#### Scenario: Vertical armor atlas generation
- **WHEN** pack compilation is triggered with 3 custom equipment models in `hybrid_shaders` mode
- **THEN** compiler produces `leather_layer_1.png` and `leather_layer_2.png` vertically stacking the base leather texture followed by the 3 custom armor textures with height matching `64 * (total_layers)` (or equivalent base resolution multiple) and injects the corresponding layer mappings into the build summary

#### Scenario: LessFancyPants core shader injection
- **WHEN** compiler runs in `hybrid_shaders` mode
- **THEN** root assets contain `shaders/core/rendertype_armor_cutout_no_cull.vsh` with constant-time vertex UV remapping and `shaders/core/rendertype_armor_cutout_no_cull.fsh` with lightweight cutout sampling, while modern `overlay_v1_21_4` remains free of legacy shaders

#### Scenario: Shader omission in modern-only mode
- **WHEN** workspace compatibility profile is set to `modern_native`
- **THEN** compiler stages canonical equipment descriptors in root and `overlay_v1_21_2` without synthesizing `leather_layer_*.png` vertical atlases and without injecting legacy core shaders

### Requirement: Workspace Pack Compatibility Profile Resolution
The resource pack compiler MUST support a `compatibility_profile` configuration in workspace pack manifests with three distinct options: `modern_native` (1.21.2+ canonical descriptors only), `hybrid_shaders` (native descriptors alongside legacy LessFancyPants core shaders and stitched leather atlases), and `hybrid_trims` (native descriptors alongside armor trim fallbacks), persisting the active profile in `data/packs/workspace/manifest.json` and exposing it in compilation metadata.

#### Scenario: Resolving default compatibility profile
- **WHEN** a workspace does not define an explicit `compatibility_profile`
- **THEN** system defaults to `hybrid_shaders` to ensure backward compatibility for legacy clients

#### Scenario: Changing compatibility profile
- **WHEN** an operator selects `modern_native` in workspace settings
- **THEN** subsequent pack builds omit legacy armor shaders and stitched leather atlases, packaging only canonical 1.21.2+ equipment descriptors and item definitions

