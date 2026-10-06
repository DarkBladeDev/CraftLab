# Resource Pack Pipeline

## Purpose
Provides automated resource pack management, semantic JSON merging of multi-source packs, pre-flight collision detection, deterministic zip packaging, SHA-1 integrity hashing, and HTTP distribution for Minecraft 1.21 assets.

## Requirements

### Requirement: Pack Source Storage and Ingestion
The system SHALL maintain a repository of pack sources comprising Studio project assets, uploaded third-party zip archives, and automated plugin pack snapshots synchronized from connected server agents, structured with an explicit layer priority hierarchy.

#### Scenario: Ingest external zip archive
- **WHEN** an operator uploads a valid resource pack `.zip` file via the web management interface
- **THEN** the system extracts and registers the pack source with metadata, layer precedence, and namespaces in the pack repository

#### Scenario: Ingest agent synchronized pack
- **WHEN** an agent uploads an extracted plugin pack snapshot from its local filesystem
- **THEN** the system registers or updates the corresponding agent pack source and records its synchronization timestamp

### Requirement: Pre-Flight Collision Detection
The system MUST perform pre-flight conflict analysis across all active pack layers prior to compilation, detecting CustomModelData overlaps on identical item materials, conflicting item model definitions, conflicting binary asset paths, and conflicting `item_model` component identifiers.

#### Scenario: CustomModelData collision detected
- **WHEN** a Studio item definition and an ingested plugin pack define the same CustomModelData integer on the same base Minecraft item material
- **THEN** the pre-flight check returns a validation error reporting the collision, both conflicting resource identifiers, and direct navigation links to the items

#### Scenario: Clean pre-flight validation
- **WHEN** all active layers contain non-overlapping CustomModelData indices and valid resource structures
- **THEN** the pre-flight check returns success with a summary of total textures, models, sound events, and font definitions

#### Scenario: Item model identifier collision detected
- **WHEN** two distinct items across active layers declare identical `item_model` identifiers
- **THEN** the pre-flight check flags an error with the colliding identifier and layer names

### Requirement: Universal Hybrid Pack Overlays Compilation
The resource pack compiler MUST construct a unified, backwards- and forwards-compatible resource pack archive with `pack_format: 34`, `supported_formats: {"min_inclusive": 34, "max_inclusive": 65}`, and versioned `overlays` targeting Minecraft 1.21.2 through 1.21.11 (`overlay_v1_21_2`), housing common assets in the root namespace and version-specific model dispatches inside the overlay directory.

#### Scenario: Compile universal multi-version pack archive
- **WHEN** the compiler builds a resource pack for distribution
- **THEN** the root `pack.mcmeta` includes `supported_formats` spanning 34 to 65 and an overlay entry mapping format range 42 to 65 to directory `overlay_v1_21_2`

#### Scenario: Shared assets asset placement
- **WHEN** the compiler packages textures, sound files, font providers, and atlas definitions
- **THEN** these assets are written strictly to the root `assets/` directory without duplication inside the overlay directory

### Requirement: Dual-Projection Item Model Synthesizer
The compiler and merger engine MUST synthesize dual model projections from an intermediate canonical model mapping: generating legacy `models/item/<material>.json` predicate overrides for 1.21.0 - 1.21.1 clients, and modern `items/<material>.json` Item Definition V2 select structures inside `overlay_v1_21_2` for 1.21.2+ clients.

#### Scenario: Synthesize modern item definition from legacy source
- **WHEN** an ingested pack layer defines custom model data overrides in `assets/minecraft/models/item/diamond_sword.json`
- **THEN** the compiler synthesizes a matching `items/diamond_sword.json` in `overlay_v1_21_2` with `minecraft:select` on `custom_model_data`

#### Scenario: Synthesize legacy override from modern definition
- **WHEN** an ingested pack layer defines `assets/minecraft/items/diamond_sword.json` with a `select` property on `custom_model_data`
- **THEN** the compiler synthesizes the corresponding `overrides` array inside `assets/minecraft/models/item/diamond_sword.json` in the base layer

### Requirement: Semantic JSON Configuration Merging
The merger engine MUST perform deep semantic merging for core Minecraft configuration files rather than raw file overwrites, specifically merging `sounds.json` audio event keys, concatenating `font/*.json` provider entries, and concatenating `atlases/*.json` sources.

#### Scenario: Merging multiple sound definitions
- **WHEN** two pack layers define entries in `assets/minecraft/sounds.json`
- **THEN** the compiled `sounds.json` preserves all distinct sound event keys and merges nested sound properties without dropping existing clips

#### Scenario: Merging item model overrides
- **WHEN** multiple layers define model overrides for a vanilla item like `diamond_sword.json`
- **THEN** the compiled item model merges all `overrides` entries sorted in ascending order of their `custom_model_data` values

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
