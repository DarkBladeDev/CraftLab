---
title: CraftLab-plugin (Paper Minecraft Plugin)
description: In-game Paper 1.21+ agent plugin, PacketEvents virtual props, Oraxen sync, and command guide.
sidebar:
  order: 6
---

# CraftLab-plugin

**CraftLab-plugin** is the native in-game runtime component installed directly on **Paper 1.21.1 – 1.21.4+** Minecraft servers. It bridges the game server to `CraftLab-backend` over a secure WebSocket, interprets deployed item models and virtual prop definitions, distributes server resource packs, and interacts with ecosystem plugins such as Oraxen.

---

## Technical Specifications

- **Target Platform**: Paper / Purpur 1.21.1+ (Java 21).
- **Network Protocol**: Secure WebSocket (`/ws/agent`) with automatic reconnection and token authentication.
- **Dependencies**:
  - `PacketEvents` (Spigot / Paper) version 2.14.0+ (Required for virtual display entity rendering).
  - `Oraxen` (Optional soft-dependency for catalog synchronization).
- **Local Persistence**: Embedded SQLite storage (`plugins/McpAgent/data/props.db`) for placed block props, and `items.json` for deployed items.

---

## Core Capabilities

```
+---------------------------------------------------------------------------------+
|                                 CRAFTLAB-PLUGIN                                 |
+---------------------------------------------------------------------------------+
|                                                                                 |
|   +-------------------------------------------------------------------------+   |
|   |                       WebSocket Gateway Client                          |   |
|   |   Handshake (targetId + secret) -> Event Dispatcher -> Command Router   |   |
|   +------------------------------------+------------------------------------+   |
|                                        |                                        |
|         +------------------------------+------------------------------+         |
|         |                              |                              |         |
|         v                              v                              v         |
|  [Item Adapter]               [Prop Manager]              [Pack Distribution]   |
|  * Modern 1.21 Data           * PacketEvents displays     * PlayerJoinEvent     |
|    Components (item_model)    * Zero server tick lag        auto-prompt         |
|  * CustomModelData fallback   * Barrier collision anchors * Stored pack URL     |
|  * Local items.json sync      * Right-click sit mechanics   and SHA-1 checksum  |
+---------------------------------------------------------------------------------+
```

### 1. Item Adapter (`Paper121ItemAdapter`)
- Applies modern Minecraft 1.21 Data Components (`item_model`) reflectively when running on Paper 1.21.2+.
- Concurrently applies `CustomModelData` to maintain compatibility with legacy resource pack configurations.
- Persists all deployed item definitions locally so they remain accessible even if the server is offline from the backend.

### 2. Virtual Display Entity Engine & State Machine (`PropManager`)
- **Zero-Tick Lag**: Rather than creating resource-heavy ArmorStands or tile entities, props are rendered as client-side Display Entities via PacketEvents packets.
- **State Machine & Model Swapping**: Supports multiple named states per prop (`default_state` and `states`), instantly swapping displayed item models via `WrapperPlayServerEntityMetadata` (Data Component `item_model`) with zero entity respawn or flickering.
- **Native Dynamic Lighting**: Seamlessly manages Paper 1.21 `Material.LIGHT` blocks (levels 0–15), automatically placing and removing them upon state transition or prop destruction.
- **Dynamic Hitboxes & Safe Eviction**: Toggles collision between solid (`BARRIER`) and passable (`STRUCTURE_VOID`), applying a smooth horizontal velocity push vector to occupying entities before placing solid barriers to prevent suffocation.
- **Interaction & Audio Feedback**: Enforces a 250ms anti-spam interaction cooldown, plays configured sound effects (Bukkit enums and custom pack sounds), and integrates with sitting (`seat`) or lying (`lay`) mechanics.
- **Database Persistence**: Prop locations, rotation matrices, and active state keys (`current_state`) are saved persistently in `plugins/McpAgent/data/props.db`.

### 3. Resource Pack Distribution (`ResourcePackManager`)
- Listens for `PlayerJoinEvent` and prompts players with the official server resource pack.
- Sends both the HTTP download URL and the hexadecimal SHA-1 checksum to trigger instant caching in the Minecraft client.
- Can be reloaded on-demand without requiring players to reconnect.

### 4. Oraxen Compatibility Hook
- Inspects active Oraxen items reflectively without hard dependency errors.
- Facilitates bidirectional synchronization: exports Oraxen items into CraftLab Studio and synchronizes pack folders smoothly.

---

## In-Game Operator Commands

CraftLab-plugin registers the `/mcp` command namespace (requires permission `mcp.admin`):

| Command | Arguments | Description |
| :--- | :--- | :--- |
| `/mcp give` | `<player> <itemId> [amount]` | Gives the specified custom item or prop to a player. |
| `/mcp status` | None | Displays WebSocket connection state, targetId, and registered props. |
| `/mcp reloadpack` | `[player]` | Forces a resource pack re-send to all players or a specified target. |
| `/mcp reload` | None | Reloads local `config.yml` and reconnects to the backend gateway. |

---

## Configuration (`plugins/McpAgent/config.yml`)

```yaml
gateway:
  url: "ws://127.0.0.1:8000/ws/agent"
  targetId: "local-paper-server"
  secret: "your-gateway-secret"

props:
  enable_packetevents: true
  enable_sit_mechanic: true
```
