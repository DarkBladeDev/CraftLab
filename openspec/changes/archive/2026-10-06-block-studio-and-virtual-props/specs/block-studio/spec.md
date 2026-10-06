# Spec Delta

## Purpose

The Block Studio capability provides visual authoring, 3D transform tuning, collision grid definition, and interaction mechanics for custom blocks and furniture props.

## ADDED Requirements

### Requirement: Visual Block and Prop Authoring
The system SHALL provide a dedicated visual studio interface allowing users to inspect, create, and edit custom block and prop definitions with real-time property validation.

#### Scenario: Creating a valid block definition
- **WHEN** a user creates a block definition with a valid identifier, display name, mode `display_prop`, and model reference
- **THEN** the system validates the definition against the canonical block schema and saves it to the draft workspace

#### Scenario: Rejecting invalid block configuration
- **WHEN** a user submits a block definition with an invalid identifier or missing model reference
- **THEN** the system rejects the submission with descriptive field-level error messages

### Requirement: 3D Transform and Model Calibration
The system SHALL support configuring 3D display transformations including scale vectors [x, y, z] and anchor translation offsets [x, y, z] for `display_prop` entities.

#### Scenario: Customizing transform scale and translation
- **WHEN** a user adjusts the scale factors and translation offsets of a display prop
- **THEN** the system updates the block definition and validates that the scale factors are non-negative and translation coordinates are within valid bounds

### Requirement: Multi-Block Hitbox and Collision Configuration
The system SHALL support defining relative grid coordinates for collision hitboxes (`solid` barrier blocks or `passable` structures) occupied by the prop.

#### Scenario: Single-block solid prop hitbox
- **WHEN** a prop is configured with standard single-block dimensions
- **THEN** its hitbox offset is defined as `[[0, 0, 0]]` with hitbox type `solid`

#### Scenario: Multi-block furniture hitbox configuration
- **WHEN** a user configures a multi-block prop (e.g. 1x2 bench or 2x2 table)
- **THEN** the system records the relative integer offset coordinates where barrier anchors must be placed upon installation

### Requirement: Prop Seat and Interaction Settings
The system SHALL support configuring interactive behaviors for blocks and props, including native seat mechanics with customizable seat height offsets.

#### Scenario: Enabling chair seat interaction
- **WHEN** a user marks a prop with `interaction_type: "seat"` and sets a seat height offset (e.g. 0.5)
- **THEN** the definition records the seat capability to enable mounting players at runtime

### Requirement: Drop Item Binding
The system SHALL support binding a block definition to an existing `ItemDefinition` that will be dropped into the world when the block or prop is broken.

#### Scenario: Setting custom drop item
- **WHEN** a user selects an existing item identifier from the project catalog as the block's `drop_item_id`
- **THEN** the system validates that the referenced item exists and links it as the block's drop reward
