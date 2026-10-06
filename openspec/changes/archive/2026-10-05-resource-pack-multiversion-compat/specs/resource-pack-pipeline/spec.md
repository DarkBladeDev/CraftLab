# Spec Delta: Resource Pack Pipeline

## ADDED Requirements

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

## MODIFIED Requirements

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
