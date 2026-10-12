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

### 1. Item Adapter (`Paper121ItemAdapter`) & Extensible Data Components Pipeline
- **Extensible Component Registry (`ItemComponentRegistry`)**: Implements an extensible Strategy pattern (`ItemComponentApplier`) that dynamically dispatches all entries declared in an item's `components` definition map during compilation and `/mcp give`.
- **Equippable Component (`minecraft:equippable`)**:
  - Full support for Minecraft 1.21.2 - 1.21.4+ `minecraft:equippable` components.
  - Supports core attributes: `slot` (`head`, `chest`, `legs`, `feet`, `body`, `mainhand`, `offhand`, `saddle`) and canonical `asset_id` (with backwards-compatible `model` fallback).
  - Supports all optional fields: `camera_overlay` (vignette texture overlay), `equip_sound` (Bukkit sound enums and custom sound keys), `allowed_entities` (entity type filtering), and boolean behavioral flags (`dispensable`, `swappable`, `damage_on_hurt`, `can_be_sheared`).
  - Employs reflective capability detection (`isSupported()`) to run safely across Paper 1.21.0 - 1.21.4+ servers without causing `NoClassDefFoundError` or classloader linking exceptions.
- **Attribute Modifiers (`minecraft:attribute_modifiers`)**:
  - Compiles attribute modifier arrays and objects into native Bukkit `AttributeModifier` instances.
  - Supports modern 1.21 `NamespacedKey` and `EquipmentSlotGroup` semantics while maintaining graceful fallback for legacy UUID-based servers.
- **Enchantments (`minecraft:enchantments`)**:
  - Compiles enchantment levels with unrestricted caps (`ignoreLevelRestriction = true`), supporting custom and high-level RPG equipment.
- **Item Models & CustomModelData**:
  - Reflectively applies native `item_model` on Paper 1.21.2+ while concurrently setting `CustomModelData` for legacy pack compatibility.
- **Persistence**: Persists all deployed item definitions locally in `items.json` so they remain accessible even if the server is offline from the backend.

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
