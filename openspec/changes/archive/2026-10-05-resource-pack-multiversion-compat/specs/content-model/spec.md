# Spec Delta: Content Model

## MODIFIED Requirements

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
