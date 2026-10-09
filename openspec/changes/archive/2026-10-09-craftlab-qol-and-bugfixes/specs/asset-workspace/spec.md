# Spec Delta

## MODIFIED Requirements

### Requirement: Controlled Filesystem Operations and Minecraft Namespace Validation
The system SHALL provide REST endpoints and UI controls to explore directory trees, create folders, upload assets, rename directories and files, and delete files and directories within the workspace, enforcing strict Minecraft resource naming rules matching regex `^[a-z0-9_.-]+$`.

#### Scenario: Folder creation with valid Minecraft naming
- **WHEN** a user creates a new folder or namespace named `ruby_weapons`
- **THEN** the system creates the directory on disk and refreshes the tree representation

#### Scenario: Rejection of invalid folder or file names
- **WHEN** a user attempts to create a directory or file containing uppercase letters, spaces, or illegal punctuation
- **THEN** the system rejects the operation with an informative validation error before modifying disk storage

#### Scenario: Asset upload into directory
- **WHEN** a user uploads a `.png`, `.json`, or `.ogg` file into a target directory in the workspace
- **THEN** the system stores the file, updates directory metadata, and displays the asset in the explorer tree

#### Scenario: Renaming workspace directory or file
- **WHEN** a user requests to rename a directory or file path from `old_path` to `new_path`
- **THEN** the system validates that the target path does not violate namespace rules or path boundaries, renames the resource on disk, and updates the explorer tree

#### Scenario: Deleting workspace directory and its contents
- **WHEN** a user confirms deletion of a workspace folder
- **THEN** the system removes the directory and its child assets from disk and cleans up explorer selection

### Requirement: Adaptive Content Viewer with Nearest-Neighbor Zoom and Live JSON Editor
The system SHALL provide an adaptive content viewer supporting pixel-art image inspection with nearest-neighbor scaling (1x to 16x) and alpha transparency grids for PNGs with pixel-aligned viewport synchronization, direct in-browser text editing with real-time JSON syntax linting and `Ctrl+S` saving for JSON files, and audio playback controls for OGG sound files.

#### Scenario: Inspecting PNG texture with crisp pixel rendering
- **WHEN** a user selects a PNG texture in the resource explorer and adjusts zoom level
- **THEN** the content viewer renders the image with `image-rendering: pixelated` and locks the checkerboard canvas bounds directly to the scaled image dimensions without positional offset

#### Scenario: Editing JSON model in real time
- **WHEN** a user edits a geometric model or item definition JSON in the content viewer and triggers save via button or `Ctrl+S`
- **THEN** the system validates syntax and writes the updated JSON file to disk

#### Scenario: Blocking save on invalid JSON syntax
- **WHEN** a user introduces a syntax error (e.g., trailing comma or unclosed bracket) in the JSON editor
- **THEN** the system displays a syntax error banner and prevents writing corrupted content to disk
