# Item Studio

## Purpose
Provides a real-time 3-column studio interface, MiniMessage formatting toolbar, live pixel-perfect Minecraft tooltip renderer, and authentic 1.21 inventory slot sprite visualization for authoring Minecraft content.

## Requirements

### Requirement: 3-Column Studio Workspace
The system SHALL provide a 3-column studio workspace organizing content into a left draft navigator and revision history, a centered item definition editor with component builders, and a right sticky live visual inspector.

#### Scenario: Selecting a draft item
- **WHEN** a user selects an item from the draft items column
- **THEN** the editor and live inspector populate with the selected item's attributes, components, and plugin extensions without page reload

#### Scenario: Real-time synchronization
- **WHEN** a user alters any field in the editor or component builders
- **THEN** the live inspector updates the slot and tooltip preview instantaneously

### Requirement: Live Pixel-Perfect Minecraft Tooltip
The system SHALL render an authentic Minecraft 1.21 tooltip featuring a dark translucent background (`#100010`), double purple gradient borders (`#5000ff` to `#28007f`), dual pixel drop shadows, and automatic combat stat calculations.

#### Scenario: Rendering custom display name and lore
- **WHEN** an item has a MiniMessage display name and lore lines
- **THEN** the tooltip renders the text with pixel styling, authentic text shadow, and accurate color and font decorations

#### Scenario: Rendering combat attribute modifiers and enchantments
- **WHEN** an item contains `minecraft:attribute_modifiers` or `minecraft:enchantments`
- **THEN** the tooltip renders the standard "When in Main Hand:" section with colored stat modifiers and Roman numeral enchantment names

### Requirement: Minecraft 1.21 Inventory Slot and Sprite Visualization
The system SHALL render an authentic Minecraft 3D beveled inventory slot displaying the crisp 16x16 PNG pixel-art sprite of the selected material, item stack count, and Custom Model Data / Item Model indicator.

#### Scenario: Rendering vanilla 1.21 material sprite
- **WHEN** an item has a valid Minecraft material such as `NETHERITE_SWORD` or `MACE`
- **THEN** the slot displays the corresponding 16x16 pixel-art PNG sprite scaled with nearest-neighbor crisp pixel rendering

#### Scenario: Displaying stack count and Custom Model Data badge
- **WHEN** an item defines an amount greater than 1 or a Custom Model Data value
- **THEN** the slot displays the stack count number in the lower right corner and an indicator badge for the Custom Model Data

#### Scenario: Displaying item_model badge
- **WHEN** an item defines an explicit `item_model` identifier
- **THEN** the slot displays a modern model indicator badge alongside the CMD badge

### Requirement: Multi-Version Item Model Configuration Editor
The Studio editor SHALL provide input controls for configuring modern `item_model` namespaced identifiers alongside classic `custom_model_data`, displaying version compatibility indicators (1.21.1 legacy fallback vs 1.21.2+ modern definition) in real-time.

#### Scenario: Editing item_model identifier
- **WHEN** an author enters a custom `item_model` key in the studio item editor
- **THEN** the editor validates the format and shows active compatibility for both 1.21.1 and 1.21.2+ clients

#### Scenario: Auto-generating item_model from custom model data
- **WHEN** an author leaves `item_model` empty but defines `custom_model_data`
- **THEN** the editor displays the auto-derived identifier placeholder used for the 1.21.2+ overlay projection

### Requirement: Adventure MiniMessage Parser and Formatting Toolbar
The system SHALL provide an interactive MiniMessage toolbar and reactive parser supporting Minecraft color names, hex colors, gradients, font styles, and selection-based tag wrapping.

#### Scenario: Wrapping selected text with format tags
- **WHEN** a user selects text within the display name or lore input and clicks a toolbar button
- **THEN** the system wraps the selected substring with the matching MiniMessage tags and retains input focus

#### Scenario: Rendering multi-stop gradients
- **WHEN** an item name or lore contains `<gradient:#c1:#c2>` tags
- **THEN** the parser interpolates characters across the gradient stops and applies matching text shadows to each character

### Requirement: Resource Pack Workspace Asset Picker Integration
The Item Studio editor SHALL provide an interactive asset picker dialog allowing authors to browse models, definitions, and textures in the active workspace pack and insert their exact Minecraft Resource Location strings into item model and configuration fields.

#### Scenario: Selecting item model via asset picker
- **WHEN** an author clicks the asset picker button next to the `item_model` or model input in the item editor
- **THEN** an asset picker modal opens displaying the workspace directory tree filtered to valid models and item definitions

#### Scenario: Applying selected asset to item definition
- **WHEN** an author selects a model or item definition within the asset picker modal and confirms selection
- **THEN** the modal closes and the exact calculated Resource Location (`namespace:path`) is populated into the target input field

