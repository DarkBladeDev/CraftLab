---
title: CraftLab-frontend (Web Studio UI)
description: Visual authoring suite, Item Studio, Block Studio, and Pack Manager interface guide.
sidebar:
  order: 5
---

# CraftLab-frontend

**CraftLab-frontend** is the browser-based authoring environment for Minecraft server administrators, builders, and developers. Built with **React 18**, **Vite**, and **Tailwind CSS**, it empowers users to design custom items, preview 3D display blocks, and manage resource packs without editing raw YAML or JSON files manually.

---

## Studio Workspaces

```
+---------------------------------------------------------------------------------+
|                               CRAFTLAB-FRONTEND                                 |
+---------------------------------------------------------------------------------+
|                                                                                 |
|   +-----------------------+  +-----------------------+  +--------------------+  |
|   |      ITEM STUDIO      |  |     BLOCK STUDIO      |  |    PACK MANAGER    |  |
|   | Custom item models    |  | Display entity props  |  | Textures & models  |  |
|   | Data Components       |  | Barrier collision     |  | Sound manifests    |  |
|   | CustomModelData       |  | Seat interactions     |  | ZIP compilation    |  |
|   +-----------------------+  +-----------------------+  +--------------------+  |
|                                                                                 |
|   +-------------------------------------------------------------------------+   |
|   |                           TARGET MANAGEMENT                             |   |
|   | Fleet connection monitor, live health indicators, and sync commands     |   |
|   +-------------------------------------------------------------------------+   |
+---------------------------------------------------------------------------------+
```

---

## Workspaces in Detail

### 1. Item Studio
Design custom items with full fidelity for modern Minecraft versions:
- **Minecraft 1.21 Data Components**: Configure native `item_model` keys pointing to custom definitions.
- **CustomModelData Support**: Provide fallback numeric IDs for legacy resource packs and plugins.
- **Visual Attributes Editor**: Customize item names, colorized lore formatting (MiniMessage / legacy colors), rarity, enchantments, and item flags.
- **Real-Time Deployment**: Push modified item definitions directly into active Paper servers with a single click.

### 2. Block Studio (Virtual Props & State Machines)
Author custom furniture, 3D decorative blocks, and props without registering tile entities or lagging server performance:
- **PacketEvents Display Previews**: Visual configuration of display entity scales, translation offsets, and rotation angles.
- **State Machines & Variants**: Dedicated tab to configure multiple named states (`default_state`, `states`), distinct block models, light levels (0–15), entry sounds, and quick presets (Lamps, Doors/Gates).
- **Dynamic Hitboxes**: Configure solid (`solid`) or passable (`passable`) collision per state with safe horizontal player ejection on close.
- **Physical Collision Anchors**: Automatically bind invisible barrier or structure void blocks across relative footprint coordinates.
- **Interactive Sit & Lay Mechanics**: Attach passenger seats to furniture props allowing players to sit or lie down by right-clicking.
- **Break Lifecycle**: Link custom prop drops and sound effects upon block destruction.

### 3. Pack Manager
Comprehensive workspace for packaging visual assets:
- **Asset Hierarchy Tree**: Inspect textures, block models, item models, and localization strings.
- **Pack Manifest Configurator**: Define `pack_format`, description strings, and custom pack icons.
- **One-Click Build**: Trigger server-side compilation, review SHA-1 digests, and verify player download links.

### 4. Target Management
Centralized fleet dashboard for all linked Paper servers:
- **Real-Time Status**: Observe WebSocket connectivity, latency, and agent build versions.
- **Instant Actions**: Broadcast catalog refreshes, reload resource packs, or test player delivery.
