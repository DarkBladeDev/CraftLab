# Spec Delta

## Purpose

Provides a real-time 3-column studio interface, MiniMessage formatting toolbar, live pixel-perfect Minecraft tooltip renderer, and authentic 1.21 inventory slot sprite visualization for authoring Minecraft content.

## ADDED Requirements

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
The system SHALL render an authentic Minecraft 3D beveled inventory slot displaying the crisp 16x16 PNG pixel-art sprite of the selected material, item stack count, and Custom Model Data indicator.

#### Scenario: Rendering vanilla 1.21 material sprite
- **WHEN** an item has a valid Minecraft material such as `NETHERITE_SWORD` or `MACE`
- **THEN** the slot displays the corresponding 16x16 pixel-art PNG sprite scaled with nearest-neighbor crisp pixel rendering

#### Scenario: Displaying stack count and Custom Model Data badge
- **WHEN** an item defines an amount greater than 1 or a Custom Model Data value
- **THEN** the slot displays the stack count number in the lower right corner and an indicator badge for the Custom Model Data

### Requirement: Adventure MiniMessage Parser and Formatting Toolbar
The system SHALL provide an interactive MiniMessage toolbar and reactive parser supporting Minecraft color names, hex colors, gradients, font styles, and selection-based tag wrapping.

#### Scenario: Wrapping selected text with format tags
- **WHEN** a user selects text within the display name or lore input and clicks a toolbar button
- **THEN** the system wraps the selected substring with the matching MiniMessage tags and retains input focus

#### Scenario: Rendering multi-stop gradients
- **WHEN** an item name or lore contains `<gradient:#c1:#c2>` tags
- **THEN** the parser interpolates characters across the gradient stops and applies matching text shadows to each character
