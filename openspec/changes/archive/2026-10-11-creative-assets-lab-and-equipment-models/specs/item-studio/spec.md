# Spec Delta: item-studio

## ADDED Requirements

### Requirement: 1.21.2+ Equippable Component Binding
The Item Studio component editor SHALL provide dedicated controls for authoring the modern `minecraft:equippable` item data component, allowing authors to select the target equipment slot (`head`, `chest`, `legs`, `feet`, `mainhand`, `offhand`), choose an equipment model from an autocomplete selector populated by registered models in Creative Assets Lab, and SHALL display equipment model preview metadata directly within the item component inspector.

#### Scenario: Binding an equipment model to a custom item
- **WHEN** user enables the `minecraft:equippable` component on an item definition and selects an equipment model
- **THEN** system populates the component structure with slot and model identifier and verifies the model reference against the workspace equipment registry
