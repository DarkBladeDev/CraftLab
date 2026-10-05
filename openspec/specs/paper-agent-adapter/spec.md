# Paper Agent and Adapter

## Purpose
The Paper Agent and Adapter capability provides the in-server runtime execution environment via a lightweight Paper plugin, managing outbound connectivity, environment discovery, local state persistence, and native Paper item manipulation.

## Requirements

### Requirement: Outbound Connectivity and Agent Bootstrap
The agent plugin MUST initiate an outbound TLS WebSocket connection to the configured control plane gateway, maintaining resilient reconnections without requiring inbound open ports on the server.

#### Scenario: Agent bootstrap and connection
- **WHEN** the Paper server starts with valid control plane configuration
- **THEN** the plugin initiates an outbound connection, completes authentication, and begins sending periodic heartbeats

#### Scenario: Automatic reconnection on disconnect
- **WHEN** network connectivity between the agent and gateway is interrupted
- **THEN** the agent attempts exponential backoff reconnections and resynchronizes its session journal upon reconnecting

### Requirement: Paper Item Adapter Execution
The agent MUST include a Paper adapter capable of translating canonical item definitions into native Paper item components and persisting them on the server.

#### Scenario: Applying an item definition
- **WHEN** the agent receives an allowlisted `create_or_update_item` operation
- **THEN** the Paper adapter parses material, display name, lore, and custom model data, updates the local item storage, and verifies the resulting item representation

#### Scenario: Local item persistence across restarts
- **WHEN** the Paper server restarts
- **THEN** the plugin loads previously deployed items from its local persistent storage without requiring an active control plane connection during boot

### Requirement: In-Game Verification Command
The agent MUST provide a dedicated, permission-gated verification command for server administrators to inspect and test deployed items in-game.

#### Scenario: Giving a deployed custom item to a player
- **WHEN** an authorized server operator executes `/mcp give <item_id>`
- **THEN** the plugin instantiates the deployed item with all configured components and places it into the operator's inventory

### Requirement: Paper 1.21 Component Item Assembly
The Paper adapter SHALL assemble native Paper 1.21 ItemStacks using modern item data components, persist deployed items to `items.json`, and serve them via the `/mcp give` command.

#### Scenario: Item compilation and local persistence
- **WHEN** the Paper adapter handles `create_or_update_item`
- **THEN** it maps the canonical JSON definition to a native Paper 1.21 ItemStack, persists the definition in `items.json`, and records the item in the active item registry

#### Scenario: Giving item to player via command
- **WHEN** an operator runs `/mcp give <player> <item_id>` for an existing deployed item
- **THEN** the plugin retrieves the item definition from the active registry and gives the assembled ItemStack with correct name, lore, model data, and components to the target player
