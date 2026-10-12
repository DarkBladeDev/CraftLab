# Spec Delta

## MODIFIED Requirements

### Requirement: 1.21.2+ Equippable Component Binding
The Item Studio component editor SHALL provide dedicated controls for authoring the modern `minecraft:equippable` item data component, allowing authors to select target equipment slots (`head`, `chest`, `legs`, `feet`, `body`, `mainhand`, `offhand`, `saddle`), bind the model reference via the official `asset_id` property (with transparent legacy `model` attribute ingestion), choose an equipment model from an autocomplete selector populated by registered models in Creative Assets Lab, configure optional advanced equippable properties (`camera_overlay`, `equip_sound`, `allowed_entities`, `dispensable`, `swappable`, `damage_on_hurt`, `can_be_sheared`), and display equipment model preview metadata directly within the item component inspector.

#### Scenario: Binding an equipment model to a custom item
- **WHEN** user enables the `minecraft:equippable` component on an item definition and selects an equipment model
- **THEN** system populates the component structure with the selected slot and `asset_id` identifier and verifies the model reference against the workspace equipment registry

#### Scenario: Ingesting legacy equippable item component
- **WHEN** an item definition contains a `minecraft:equippable` component with a `model` attribute
- **THEN** editor transparently upgrades the component to `asset_id` without losing the configured slot or identifier

#### Scenario: Authoring optional advanced equippable fields
- **WHEN** user expands the advanced equippable settings in the component editor
- **THEN** editor provides controls for camera overlay namespaced keys, equip sound identifiers, allowed entity types, and boolean flags (`dispensable`, `swappable`, `damage_on_hurt`), persisting them in the item's `minecraft:equippable` component dictionary
