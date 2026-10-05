# Tasks

## 1. Backend Domain & Model Updates

- [x] 1.1 Extend `ItemDefinition` in `backend/app/domain/items.py` with `components: dict = Field(default_factory=dict)` and include it in `to_canonical_dict()`. Verify by running pytest domain item tests.
- [x] 1.2 Update `ItemModel` in `backend/app/models/entities.py` to add `components = Column(JSON, default=dict)` with backward-compatible SQLite table migration. Verify by inspecting database schema on application start.
- [x] 1.3 Update items API in `backend/app/api/items.py` and `client.ts` TypeScript types to pass, receive, and persist `components`. Verify via API endpoint test calls.

## 2. Adventure MiniMessage Parser & Toolbar

- [x] 2.1 Implement the MiniMessage tokenizer and parser in `frontend/src/features/items/minimessage/minimessage.ts` supporting standard Minecraft color names, hex `<#hex>`, multi-stop gradients `<gradient:#c1:#c2>`, text decorations (`<bold>`, `<italic>`), and legacy codes (`&c`/`§c`). Verify with unit tests checking parsed DOM trees.
- [x] 2.2 Create `MiniMessageToolbar.tsx` offering selection-aware tag wrapping (`[B]`, `[I]`, `[U]`, `[S]`), a 16-color Minecraft palette, and an RPG gradient builder. Verify interactive insertion on display name and lore textarea.

## 3. Minecraft Inventory Slot & Pixel Tooltip

- [x] 3.1 Create `MinecraftSlot.tsx` featuring 3D beveled borders, 16x16 PNG pixel-art sprite resolver with `image-rendering: pixelated`, stack badge, and Custom Model Data indicator. Verify crisp rendering with various vanilla materials.
- [x] 3.2 Create `MinecraftTooltip.tsx` rendering the authentic dark background (`#100010`), dual purple gradient border, pixel font drop shadows, combat stat calculations (`When in Main Hand:`), and Roman numeral enchantments. Verify visual fidelity against test items.

## 4. 1.21 Component Builders & 3-Column Studio Workspace

- [x] 4.1 Create `ComponentBuilder.tsx` to provide visual editors for `minecraft:attribute_modifiers` (attribute, slot, operation, value) and `minecraft:enchantments` (enchantment name and level). Verify modifications update the item's `components` dictionary.
- [x] 4.2 Refactor `ItemEditor.tsx` into the 3-column Studio workspace (Column 1: Drafts & Revisions, Column 2: Form/Toolbar/Builders/Schema, Column 3: Sticky Live Inspector) with instantaneous real-time preview updates. Verify draft switching and form interactions.

## 5. Verification & End-to-End Integration

- [x] 5.1 Run frontend production build (`npm run build`) and verify TypeScript compilation and bundle generation succeed without warnings or errors.
- [x] 5.2 Run backend pytest suite to verify canonical hashing, revision snapshotting, and item deployment remain consistent with the new component model.
