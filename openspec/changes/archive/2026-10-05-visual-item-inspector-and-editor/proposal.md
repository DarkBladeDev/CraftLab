# Proposal

## Why

Currently, item creation in the web client relies on basic text inputs and a rudimentary preview that strips formatting tags to plain yellow text, offering no visual fidelity for how items actually appear in Minecraft 1.21. Server administrators and creators cannot preview authentic MiniMessage colors, gradients, item sprites, Roman numeral enchantments, or combat attribute modifiers without repeatedly exporting or testing in-game. Providing a studio workspace with an authentic pixel-perfect tooltip, Minecraft inventory slot, MiniMessage formatting toolbar, and structured 1.21 Data Components significantly accelerates content authoring and eliminates trial-and-error deployments.

## What Changes

- **Backend & Data Model**:
  - Extend canonical `ItemDefinition` and `ItemModel` with an extensible `components: dict` mapping conforming to modern Minecraft 1.20.5+ / 1.21 Data Component namespaces (`minecraft:attribute_modifiers`, `minecraft:enchantments`, etc.).
  - Include `components` deterministically in canonical dictionary hashing for immutable revisions and drift detection.
- **Frontend Studio Workspace & Layout**:
  - Refactor the item editing interface into a 3-column "Studio" workspace: Column 1 for quick Draft switching and immutable Revision history; Column 2 for item definition form, MiniMessage formatting toolbar, and 1.21 component builders; Column 3 for a sticky Live Inspector.
- **Live Item Inspector**:
  - Render an authentic Minecraft 3D beveled inventory slot featuring 16x16 pixel-art PNG sprites for Minecraft 1.21 materials (with `image-rendering: pixelated`), stack badges, and Custom Model Data indicators.
  - Implement a pixel-perfect Minecraft Tooltip with `#100010` background, purple gradient borders (`#5000ff` to `#28007f`), dual drop-shadow pixel typography, and combat stat breakdowns (`When in Main Hand: +14 Attack Damage`).
- **Adventure MiniMessage Engine & Toolbar**:
  - Build a lightweight reactive MiniMessage parser supporting named Minecraft colors, hex `<#hex>`, multi-stop gradients `<gradient:#c1:#c2>`, text styling (`<bold>`, `<italic>`, etc.), and legacy color codes (`&`/`§`).
  - Add an interactive formatting toolbar for selection-based tag wrapping, a 16-color Minecraft palette, and an RPG gradient generator.

## Capabilities

### New Capabilities
- `item-studio`: Provides the 3-column studio interface, MiniMessage formatting toolbar, live pixel-perfect Minecraft tooltip renderer, and 1.21 sprite slot visualization.

### Modified Capabilities
- `content-model`: Extends canonical item models with structured 1.21 Data Components (`components: dict`) and updates deterministic revision hashing.

## Impact

- **Backend**: `backend/app/domain/items.py`, `backend/app/models/entities.py`, and API endpoints in `backend/app/api/items.py` to accept, validate, and serialize `components`.
- **Frontend**:
  - New modules in `frontend/src/features/items/`: `ItemStudio.tsx`, `LiveInspector.tsx`, `MinecraftTooltip.tsx`, `MinecraftSlot.tsx`, `MiniMessageToolbar.tsx`, and parser utility `minimessage.ts`.
  - Refactor `ItemEditor.tsx` to host the 3-column studio layout.
  - Public texture resolution for Minecraft 1.21 material sprites.
- **Dependencies & DB**: Backward-compatible database schema addition (`components` JSON column).
