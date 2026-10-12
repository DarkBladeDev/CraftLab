# Spec Delta: Item Studio

## MODIFIED Requirements

### Requirement: 1.21.2+ Equippable Component Binding
The Item Studio component editor SHALL provide dedicated controls for authoring the modern `minecraft:equippable` item data component, allowing authors to select target equipment slots (`head`, `chest`, `legs`, `feet`, `body`, `mainhand`, `offhand`, `saddle`), bind the model reference via the official `asset_id` property, choose an equipment model from an autocomplete selector populated by registered models in Creative Assets Lab, SHALL transparently read legacy item definitions containing `model` in place of `asset_id`, and SHALL display equipment model preview metadata directly within the item component inspector.

#### Scenario: Binding an equipment model to a custom item
- **WHEN** user enables the `minecraft:equippable` component on an item definition and selects an equipment model
- **THEN** system populates the component structure with the selected slot and `asset_id` identifier and verifies the model reference against the workspace equipment registry

#### Scenario: Ingesting legacy equippable item component
- **WHEN** an item definition contains a `minecraft:equippable` component with a `model` attribute
- **THEN** editor transparently upgrades the component to `asset_id` without losing the configured slot or identifier
