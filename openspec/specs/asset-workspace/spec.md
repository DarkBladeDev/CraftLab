# Asset Workspace

## Purpose
Provides a persistent file explorer, real-time visual viewer, live JSON editor, and Minecraft Resource Location metadata resolver for the project resource pack workspace.

## Requirements

### Requirement: Persistent Workspace Pack Storage and Auto-Initialization
The system SHALL maintain a dedicated resource pack workspace directory at `data/packs/workspace/`. When the workspace directory is non-existent or empty, the system SHALL automatically initialize standard Minecraft resource pack scaffolding including a valid `pack.mcmeta` manifest and standard directory structures.

#### Scenario: Auto-initialization of empty workspace
- **WHEN** the backend starts or a user navigates to the Asset Workspace and `data/packs/workspace/` is empty or missing
- **THEN** the system generates `pack.mcmeta` with supported format ranges (34 to 65) and scaffolds directory paths `assets/minecraft/textures/`, `assets/minecraft/models/`, and `assets/minecraft/items/`

#### Scenario: Preserving existing workspace contents
- **WHEN** the workspace directory already contains custom textures, models, or directories
- **THEN** the system reads and serves the existing filesystem tree without overwriting any user files

### Requirement: Controlled Filesystem Operations and Minecraft Namespace Validation
The system SHALL provide REST endpoints and UI controls to explore directory trees, create folders, upload assets, and delete files within the workspace, enforcing strict Minecraft resource naming rules matching regex `^[a-z0-9_.-]+$`.

#### Scenario: Folder creation with valid Minecraft naming
- **WHEN** a user creates a new folder or namespace named `ruby_weapons`
- **THEN** the system creates the directory on disk and refreshes the tree representation

#### Scenario: Rejection of invalid folder or file names
- **WHEN** a user attempts to create a directory or file containing uppercase letters, spaces, or illegal punctuation
- **THEN** the system rejects the operation with an informative validation error before modifying disk storage

#### Scenario: Asset upload into directory
- **WHEN** a user uploads a `.png`, `.json`, or `.ogg` file into a target directory in the workspace
- **THEN** the system stores the file, updates directory metadata, and displays the asset in the explorer tree

### Requirement: Adaptive Content Viewer with Nearest-Neighbor Zoom and Live JSON Editor
The system SHALL provide an adaptive content viewer supporting pixel-art image inspection with nearest-neighbor scaling (1x to 8x) and alpha transparency grids for PNGs, direct in-browser text editing with real-time JSON syntax linting and `Ctrl+S` saving for JSON files, and audio playback controls for OGG sound files.

#### Scenario: Inspecting PNG texture with crisp pixel rendering
- **WHEN** a user selects a PNG texture in the resource explorer
- **THEN** the content viewer renders the image with `image-rendering: pixelated`, zoom controls, and a checkered transparency canvas

#### Scenario: Editing JSON model in real time
- **WHEN** a user edits a geometric model or item definition JSON in the content viewer and triggers save via button or `Ctrl+S`
- **THEN** the system validates syntax and writes the updated JSON file to disk

#### Scenario: Blocking save on invalid JSON syntax
- **WHEN** a user introduces a syntax error (e.g., trailing comma or unclosed bracket) in the JSON editor
- **THEN** the system displays a syntax error banner and prevents writing corrupted content to disk

### Requirement: Dynamic Minecraft Resource Location and Metadata Resolution
The system SHALL dynamically compute the canonical Minecraft Resource Location (`namespace:path`) for the selected file by stripping Minecraft's implicit category directory prefixes (`textures/`, `models/`, `items/`, `sounds/`) and file extensions, providing one-click copy actions for Resource Locations, 1.21.2+ `item_model` component tags, JSON texture slot keys, and `/give` commands.

#### Scenario: Calculating Resource Location for item texture
- **WHEN** a user selects `assets/craftlab/textures/item/ruby_sword.png`
- **THEN** the metadata viewer displays the exact Resource Location `craftlab:item/ruby_sword` and copies it to clipboard on click

#### Scenario: Calculating Resource Location for modern item definition
- **WHEN** a user selects `assets/craftlab/items/ruby_sword.json`
- **THEN** the metadata viewer displays the exact Resource Location `craftlab:ruby_sword` and formats the component tag as `item_model="craftlab:ruby_sword"`

#### Scenario: Calculating Resource Location for sound file
- **WHEN** a user selects `assets/craftlab/sounds/weapon/slash.ogg`
- **THEN** the metadata viewer displays the sound identifier `craftlab:weapon/slash`

### Requirement: Dependency and Cross-Reference Integrity Tracking
The system SHALL inspect references across workspace assets and Studio items, displaying whether required textures exist for geometric models, detecting missing textures, and identifying which models or Studio items reference the active texture.

#### Scenario: Detecting missing texture in geometric model
- **WHEN** a model JSON declares a texture key pointing to a non-existent path in the workspace
- **THEN** the metadata viewer flags the missing texture with a visual warning indicator

#### Scenario: Finding referencing models for a texture
- **WHEN** a user selects a texture that is referenced by one or more model JSON files
- **THEN** the metadata viewer lists the referencing models with direct navigation links
