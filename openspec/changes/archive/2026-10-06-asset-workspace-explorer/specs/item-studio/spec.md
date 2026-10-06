# Spec Delta: Item Studio

## ADDED Requirements

### Requirement: Resource Pack Workspace Asset Picker Integration
The Item Studio editor SHALL provide an interactive asset picker dialog allowing authors to browse models, definitions, and textures in the active workspace pack and insert their exact Minecraft Resource Location strings into item model and configuration fields.

#### Scenario: Selecting item model via asset picker
- **WHEN** an author clicks the asset picker button next to the `item_model` or model input in the item editor
- **THEN** an asset picker modal opens displaying the workspace directory tree filtered to valid models and item definitions

#### Scenario: Applying selected asset to item definition
- **WHEN** an author selects a model or item definition within the asset picker modal and confirms selection
- **THEN** the modal closes and the exact calculated Resource Location (`namespace:path`) is populated into the target input field
