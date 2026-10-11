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
- **Equippable Components (1.21.2+)**: Bind custom armor and equipment models with slot selection and autocompletion populated directly from Creative Assets Lab.
- **CustomModelData Support**: Provide fallback numeric IDs for legacy resource packs and plugins.
- **Visual Attributes Editor**: Customize item names, colorized lore formatting (MiniMessage / legacy colors), rarity, enchantments, and item flags.
- **Real-Time Deployment**: Push modified item definitions directly into active Paper servers with a single click.

### 2. Block Studio (Virtual Props & State Machines)
Author custom furniture, 3D decorative blocks, and props without registering tile entities or lagging server performance:
- **PacketEvents Display Previews**: Visual configuration of display entity scales, translation offsets, and rotation angles.
- **State Machines & Variants**: Dedicated tab to configure multiple named states (`default_state`, `states`), distinct block models, light levels (0–15), entry sound effects, particle VFX triggers, and quick presets (Lamps, Doors/Gates).
- **Audio & VFX Triggers**: Bind registered sound events and custom particle effects with 3-axis offset calibration to state transitions.
- **Dynamic Hitboxes**: Configure solid (`solid`) or passable (`passable`) collision per state with safe horizontal player ejection on close.
- **Physical Collision Anchors**: Automatically bind invisible barrier or structure void blocks across relative footprint coordinates.
- **Interactive Sit & Lay Mechanics**: Attach passenger seats to furniture props allowing players to sit or lie down by right-clicking.
- **Break Lifecycle**: Link custom prop drops and sound effects upon block destruction.

### 3. Creative Assets Lab
Unified creative hub for authoring client-side audio, font, equipment, and particle effects:
- **Dynamic Multi-Namespace Architecture**: Native multi-namespace support across all tabs with explicit namespace selectors, workspace datalist suggestions, automatic colon decomposition (`namespace:id`), and scoped sidebar badges.
- **Glyphs & Fonts**: Automatic PUA unicode allocator (`\uE000`–`\uF8FF`), manual hexadecimal override with real-time collision detection, MiniMessage tags, and live Minecraft Chat and Tablist preview simulators.
- **Equipment & Armor (1.21.2+)**: Multi-layer armor builder supporting `humanoid`, `humanoid_leggings`, and `wings` layers, dyeable overlay tint masks, 2D/3D paper doll mannequin preview, and 1-click `minecraft:equippable` JSON generator.
- **Sound Events (SFX)**: Visual `sounds.json` editor with multi-sample variations, Vorbis channel probe (Mono vs. Stereo), and 1-click downmix converting stereo audio into symmetric `(L+R)/2` Mono `.ogg` for 3D positional distance attenuation.
- **Particles & VFX**: Custom `particles/<id>.json` editor with sprite texture validator, real-time 60 FPS HTML5 canvas emitter simulator, and in-game `/particle` command builder.
- **Schema & Raw JSON Drawer**: Collapsible editor drawer supporting bidirectional synchronization between visual forms and Minecraft 1.21.2+ JSON schema validation.

### 4. Pack Manager
Comprehensive workspace for packaging visual assets:
- **Universal Multi-Version Matrix**: Real-time visualization of the 4-layer packaging architecture: Base Layer (1.21.0 - 1.21.1, formats 34..41), Items V2 (1.21.2+, formats 42..max), Modern Shaders (1.21.4+, formats 46..max), and auto-synthesized texture atlases.
- **Layer Precedence Manager**: Drag-and-drop or configure layer evaluation priority for Studio assets, workspace files, and ingested third-party pack sources.
- **Pre-Flight Conflict Auditor**: Interactive diagnostic modal displaying blocking CustomModelData collisions, missing physical texture references, core shader overlaps, and mipmap/animation safety warnings.
- **Pack Manifest Configurator**: Define base format, operator-configurable maximum format boundaries (`max_inclusive`), and description metadata.
- **One-Click Build**: Trigger server-side compilation, review deterministic SHA-1 digests, and verify player download links.

### 5. Target Management
Centralized fleet dashboard for all linked Paper servers:
- **Real-Time Status**: Observe WebSocket connectivity, latency, and agent build versions.
- **Instant Actions**: Broadcast catalog refreshes, reload resource packs, or test player delivery.

