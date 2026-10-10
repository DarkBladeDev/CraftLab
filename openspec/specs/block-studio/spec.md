# Block Studio

## Purpose
The Block Studio capability provides visual authoring, 3D transform tuning, collision grid definition, and interaction mechanics for custom blocks and furniture props.

## Requirements

### Requirement: Visual Block and Prop Authoring
The system SHALL provide a dedicated visual studio interface allowing users to inspect, create, and edit custom block and prop definitions with real-time property validation, supporting distinct Block Model Identifiers (`block_model`) for placed world displays and Item Model Identifiers (`item_model`) for inventory/hand representations, and SHALL allow creating snapshot revisions when only blocks and props exist.

#### Scenario: Creating a valid block definition
- **WHEN** a user creates a block definition with a valid identifier, display name, mode `display_prop`, and model reference
- **THEN** the system validates the definition against the canonical block schema and saves it to the draft workspace

#### Scenario: Rejecting invalid block configuration
- **WHEN** a user submits a block definition with an invalid identifier or missing model reference
- **THEN** the system rejects the submission with descriptive field-level error messages

#### Scenario: Authoring with separate block model and item model
- **WHEN** a user configures a prop specifying a 3D placed model in `block_model` and an item representation in `item_model`
- **THEN** the system persists both attributes, utilizing `block_model` for world entity rendering and `item_model` for item stacks

#### Scenario: Creating revision snapshot without items
- **WHEN** a project contains one or more valid block definitions but 0 items and the user requests a revision snapshot
- **THEN** the system creates a valid canonical revision snapshot containing the block definitions without raising a validation error

### Requirement: 3D Transform and Model Calibration
The system SHALL support configuring 3D display transformations including scale vectors [x, y, z] and anchor translation offsets [x, y, z] for `display_prop` entities.

#### Scenario: Customizing transform scale and translation
- **WHEN** a user adjusts the scale factors and translation offsets of a display prop
- **THEN** the system updates the block definition and validates that the scale factors are non-negative and translation coordinates are within valid bounds

### Requirement: Multi-Block Hitbox and Collision Configuration
The system SHALL support defining relative grid coordinates for collision hitboxes (`solid` barrier blocks or `passable` structures) occupied by the prop, and SHALL conditionally disable hardness and tool type requirements when the hitbox is configured as a solid barrier.

#### Scenario: Single-block solid prop hitbox
- **WHEN** a prop is configured with standard single-block dimensions
- **THEN** its hitbox offset is defined as `[[0, 0, 0]]` with hitbox type `solid`

#### Scenario: Multi-block furniture hitbox configuration
- **WHEN** a user configures a multi-block prop (e.g. 1x2 bench or 2x2 table)
- **THEN** the system records the relative integer offset coordinates where barrier anchors must be placed upon installation

#### Scenario: Disabling break properties for solid barrier hitboxes
- **WHEN** a prop's hitbox type is set to `solid`
- **THEN** the interface disables or hides hardness and optimal tool inputs, treating the barrier as unbreakable in survival gameplay

### Requirement: Prop Seat and Interaction Settings
The system SHALL support configuring interactive behaviors for blocks and props, including native seat mechanics (`seat`) and laying mechanics (`lay`) with customizable vertical offset adjustments.

#### Scenario: Enabling chair seat interaction
- **WHEN** a user marks a prop with `interaction_type: "seat"` and sets a seat height offset (e.g. 0.5)
- **THEN** the definition records the seat capability to enable mounting players at runtime

#### Scenario: Enabling lie down interaction
- **WHEN** a user marks a prop with `interaction_type: "lay"` and configures an offset
- **THEN** the definition records the laying capability, causing the runtime agent to mount and pose the interacting player in a sleeping position on right-click

### Requirement: Drop Item Binding
The system SHALL support binding a block definition to an existing `ItemDefinition` that will be dropped into the world when the block or prop is broken.

#### Scenario: Setting custom drop item
- **WHEN** a user selects an existing item identifier from the project catalog as the block's `drop_item_id`
- **THEN** the system validates that the referenced item exists and links it as the block's drop reward

### Requirement: Prop State Machine Authoring
The system SHALL provide interface controls within Block Studio allowing authors to configure multiple named states for a prop definition (such as `off`, `on`, `open`, `closed`), designate a `default_state`, and for each state configure a distinct `block_model`, an optional `light_level` (integer from 0 to 15), an entry `sound` effect with volume and pitch settings, an optional collision override (`solid` or `passable`), and a transition target `next_state`.

#### Scenario: Authoring a two-state toggle prop
- **WHEN** a user defines a prop with `default_state: "off"`, an `"off"` state pointing to `studio:props/lamp_off` with `light_level: 0`, and an `"on"` state pointing to `studio:props/lamp_on` with `light_level: 14` and entry sound `block.wooden_button.click_on`
- **THEN** the system validates both states, links their transition targets cyclically, and saves the configuration to the draft workspace

#### Scenario: Authoring a cyclic multi-state prop
- **WHEN** a user creates a prop with three sequential states (`off` -> `low` -> `high` -> `off`)
- **THEN** the system records the custom state sequence and validates that all `next_state` references point to existing state keys

#### Scenario: Validating light level boundaries
- **WHEN** a user enters a light level outside the integer range 0 to 15 (e.g. -1 or 16)
- **THEN** the system rejects the input and displays a validation error constraining light levels between 0 and 15

