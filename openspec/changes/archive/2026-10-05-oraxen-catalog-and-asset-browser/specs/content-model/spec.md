# Spec Delta: Content Model

## ADDED Requirements

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
