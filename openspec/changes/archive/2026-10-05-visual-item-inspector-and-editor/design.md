# Design

## Context

See proposal.md for motivation and problem background. Currently, item definitions are edited via a standard two-column form with basic string fields and a stripped-text preview. Minecraft 1.20.5+ and 1.21 replaced traditional NBT with typed Data Components (`minecraft:attribute_modifiers`, `minecraft:enchantments`, etc.) and modern servers use Adventure MiniMessage formatting for names and lore.

## Goals / Non-Goals

**Goals:**
- Provide a 3-column "Studio" workspace: Drafts/Revisions (Col 1), Item Form & Builders (Col 2), and Sticky Live Inspector (Col 3).
- Implement an authentic Minecraft 1.21 Tooltip with dark translucent background (`#100010`), dual purple gradient borders, pixel typography with dual drop shadows, combat stat calculations (`When in Main Hand:`), and Roman numeral enchantments.
- Implement an authentic 3D beveled Minecraft inventory slot rendering 16x16 pixel-art PNG sprites for vanilla 1.21 materials with `image-rendering: pixelated`, stack badges, and Custom Model Data indicators.
- Implement a reactive Adventure MiniMessage parser and an interactive selection-aware formatting toolbar (16 Minecraft colors, formatting tags, gradient builder).
- Extend `ItemDefinition` and `ItemModel` with an extensible `components: dict` mapping and include it in deterministic revision hashing.

**Non-Goals:**
- 3D WebGL rendering of complex custom resource pack JSON models (handled via material base sprite + CMD indicator).
- Full client-side resource pack compilation or ZIP generation (scoped to a separate pipeline capability).

## Decisions

### Decision 1: Extensible `components: dict` in Backend Domain & Database
- **Choice**: Add `components: dict = Field(default_factory=dict)` to `ItemDefinition` and a `components = Column(JSON, default=dict)` to `ItemModel`. Include `components` sorted deterministically in `to_canonical_dict()`.
- **Rationale**: Minecraft 1.20.5+ / 1.21 components evolve frequently. An extensible dictionary avoids database migrations for every newly supported component while enabling client-side builders for high-value components (`minecraft:attribute_modifiers`, `minecraft:enchantments`, `minecraft:food`).
- **Alternative considered**: Top-level typed fields (`attributes: List`, `enchantments: Dict`). Rejected because it introduces schema rigidity and requires migrations for each Mojang component.

### Decision 2: 3-Column Studio Workspace Layout
- **Choice**: Reorganize `ItemEditor` into three distinct columns:
  - Column 1 (22% width): Draft item switcher, quick actions (Create New Draft, Delete), and immutable revision history.
  - Column 2 (48% width): Main definition form, MiniMessage toolbar, lore textarea, 1.21 component builders, and Oraxen schema extensions.
  - Column 3 (30% width, Sticky): Live Inspector holding the Minecraft slot and live pixel tooltip.
- **Rationale**: Keeps the live visual preview immediately visible during scrolling and form modifications, while providing one-click switching across draft items.

### Decision 3: Sprite Resolution via 16x16 PNG Assets & Fallback Mechanism
- **Choice**: Resolve vanilla materials to 16x16 PNG item sprites (e.g. `diamond_sword.png`, `mace.png`, `wind_charge.png`) rendered with `image-rendering: pixelated` and `image-rendering: crisp-edges`.
- **Rationale**: Gives true pixel-perfect in-game fidelity. If a texture fails to load or is not yet cached, fallback gracefully to category-based SVG icon placeholders.

### Decision 4: Lightweight Client-Side MiniMessage Parser
- **Choice**: Implement a TypeScript parser in `frontend/src/features/items/minimessage/` that tokenizes MiniMessage tags (`<color>`, `<#hex>`, `<gradient:#c1:#c2>`, `<bold>`, etc.) and legacy codes (`&c`, `§c`), outputting structured React elements with calculated character gradients and double text drop shadows (`rgba(0,0,0,0.8)`).
- **Rationale**: Instant sub-millisecond feedback while typing without requiring a server round-trip or WebAssembly overhead.

## Risks / Trade-offs

- **[Risk]** Obscure material missing PNG sprite.
  - **Mitigation**: Category-based fallback icon with material label to ensure the slot never appears blank.
- **[Risk]** Heavy gradient text parsing causing UI lag on massive lore text.
  - **Mitigation**: Memoize the parse tree using `useMemo` keyed on the raw string and limit maximum lore length.
- **[Risk]** Database schema drift with legacy items without `components`.
  - **Mitigation**: Default `components` column to empty dict `{}` and sanitize legacy SQLite rows on load.

## Migration Plan

1. Backend: Add `components` column to `items` table in SQLite (`ALTER TABLE items ADD COLUMN components JSON DEFAULT '{}'`).
2. API: Existing items returned with empty `components: {}` maintain complete backwards compatibility.
