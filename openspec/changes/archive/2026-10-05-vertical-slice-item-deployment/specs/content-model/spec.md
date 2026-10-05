# Spec Delta

## ADDED Requirements

### Requirement: Paper 1.21 Item Data Components
The canonical content model SHALL validate and store Paper 1.21 item data components including identifier, material, display name, lore, custom model data, and item flags.

#### Scenario: Valid item component authoring
- **WHEN** an item definition is submitted with valid material, display name, lore, custom model data, and item flags
- **THEN** the system validates all fields against the canonical schema and persists the item in the project draft

#### Scenario: Rejection of invalid item fields
- **WHEN** an item definition specifies an invalid Minecraft material name or negative custom model data
- **THEN** the system rejects the item definition with a field-level validation error
