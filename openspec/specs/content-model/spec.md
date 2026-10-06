# Content Model

## Purpose
The Content Model capability manages canonical, typed Minecraft content definitions (such as items, recipes, and future resource types) within project workspaces, providing authoritative schema validation and immutable revision snapshots.

## Requirements

### Requirement: Canonical Item Definitions
The system MUST support a canonical, typed representation for Minecraft item definitions that is decoupled from runtime plugin classes while supporting modern Paper and Minecraft component fields.

#### Scenario: Valid item definition authoring
- **WHEN** a user or client submits an item definition with valid identifier, material, display name, lore, and optional custom model data or components
- **THEN** the system validates the definition against the canonical schema and persists it in the project draft

#### Scenario: Validation failure on invalid item schema
- **WHEN** an item definition contains an invalid material, negative stack sizes, or malformed data components
- **THEN** the system rejects the definition with descriptive field-level validation errors

### Requirement: Immutable Project Revisions
Projects MUST create immutable revision snapshots representing the exact desired state of all project resources at a point in time.

#### Scenario: Creating a revision snapshot
- **WHEN** a user creates a revision from current project draft definitions
- **THEN** the platform freezes the resource states into an immutable revision, records author and timestamp, and prevents any subsequent modification of that revision

#### Scenario: Attempting to modify an existing revision
- **WHEN** any operation attempts to update or delete resources within an existing revision snapshot
- **THEN** the system rejects the operation, preserving the immutability of historical revisions

### Requirement: Deterministic Content Hashing
Every project revision MUST have a deterministic hash computed over its canonical resource definitions to enable tamper-evident verification and drift detection.

#### Scenario: Computing revision hash
- **WHEN** a revision is created
- **THEN** a SHA-256 content hash is computed over the canonical, canonically ordered JSON serialization of all contained resources

#### Scenario: Identical contents produce identical hash
- **WHEN** two revisions contain identical resource definitions and schemas
- **THEN** their computed content hashes match

### Requirement: Paper 1.21 Item Data Components
The canonical content model SHALL validate and store Paper 1.21 item data components including identifier, material, display name, lore, custom model data, optional `item_model` namespaced identifier, item flags, and an extensible dictionary of modern Minecraft 1.21 Data Components (`components`).

#### Scenario: Valid item component authoring
- **WHEN** an item definition is submitted with valid material, display name, lore, custom model data, item flags, or custom data components
- **THEN** the system validates all fields against the canonical schema and persists the item in the project draft

#### Scenario: Item definition with structured 1.21 components
- **WHEN** an item definition includes a `components` map containing components such as `minecraft:attribute_modifiers`, `minecraft:enchantments`, or `minecraft:food`
- **THEN** the system validates the component payload and deterministically hashes the definition into revisions

#### Scenario: Rejection of invalid item fields
- **WHEN** an item definition specifies an invalid Minecraft material name or negative custom model data
- **THEN** the system rejects the item definition with a field-level validation error

#### Scenario: Item definition with custom item_model identifier
- **WHEN** an item definition specifies an `item_model` such as `studio:ruby_sword`
- **THEN** the system validates the namespaced format and stores it alongside `custom_model_data` in the item components

### Requirement: Multi-Target Exporter Specification
The canonical content model SHALL support specifying an export target format (`native` or `oraxen`) on item definitions.

#### Scenario: Item definition with Oraxen export format
- **WHEN** an item definition specifies `export_format: "oraxen"`
- **THEN** the system validates that the target server supports the `oraxen` adapter before allowing deployment

### Requirement: Plugin Mappings and Raw Extensions Payload
The canonical content model SHALL support structured plugin properties conforming to a registered schema and optional unformatted raw YAML/JSON extensions.

#### Scenario: Item definition with structured Oraxen properties
- **WHEN** an item definition includes an `oraxen` property block matching the `oraxen-item-v1` schema
- **THEN** the model validates the fields against the schema and preserves them in drafts and revisions

#### Scenario: Item definition with raw extensions block
- **WHEN** an item definition contains arbitrary raw YAML/JSON plugin extension strings
- **THEN** the system validates syntax and includes the raw extensions in the canonical revision payload
