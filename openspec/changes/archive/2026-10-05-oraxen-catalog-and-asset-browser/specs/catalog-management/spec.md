# Spec Delta: Catalog Management

## Purpose
The Catalog Management capability provides unified access to multi-source asset catalogs, encompassing vanilla Minecraft items, discovered external plugin assets (such as Oraxen), and declarative configuration schemas for dynamic attribute mapping and asset forking.

## ADDED Requirements

### Requirement: Vanilla Minecraft Asset Taxonomy
The system SHALL provide a queryable catalog of native Minecraft 1.21 materials organized by standard gameplay categories (Combat, Tools, Armor, Building, Ingredients, Redstone, Food) with search and filtering capabilities.

#### Scenario: Querying vanilla material catalog
- **WHEN** a client requests the vanilla catalog with an optional category or name query
- **THEN** the system returns matching vanilla materials with identifier, display name, category, and standard properties

### Requirement: Target-Linked Discovered Item Persistence
The system SHALL persist external items discovered on connected targets (including Oraxen items) into a target-linked catalog database table (`discovered_catalog_items`) to allow offline querying and inspection.

#### Scenario: Storing discovered external items
- **WHEN** a target agent transmits a catalog manifest containing discovered Oraxen items
- **THEN** the system upserts the items into the target's discovered catalog with source, item ID, base material, display name, custom model data, and raw properties

#### Scenario: Querying discovered catalog while target is offline
- **WHEN** a client queries discovered catalog items for a target that is currently disconnected
- **THEN** the system returns the persisted catalog items with the last synchronized timestamp

### Requirement: Config Schemas and Mappings Registry
The system SHALL maintain a registry of declarative configuration schemas for external plugins (such as `oraxen-item-v1`) that define UI sections, typed fields, and serialization rules for plugin-specific properties.

#### Scenario: Retrieving plugin configuration schema
- **WHEN** a client requests the configuration schema for `oraxen`
- **THEN** the system returns the schema definition containing field specifications, types, default values, and section groupings

### Requirement: Asset Forking into Content Drafts
The system SHALL support forking any catalog entry (Vanilla or discovered external item) into a new editable platform content draft with pre-populated properties.

#### Scenario: Forking an Oraxen item as a new platform item
- **WHEN** a user selects an Oraxen discovered item and invokes "Fork as Base"
- **THEN** the editor loads the base material, display name, lore, custom model data, and mapped plugin properties into a new editable draft item
