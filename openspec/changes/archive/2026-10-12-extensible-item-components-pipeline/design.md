# Design: Extensible Item Components Pipeline & Full Equippable Support

## Context

See `proposal.md` for background and motivation. `CraftLab-plugin` currently compiles against `io.papermc.paper:paper-api:1.21.1-R0.1-SNAPSHOT` so that a single unified plugin artifact loads and executes cleanly across Paper 1.21.0 to 1.21.4+ servers. In `Paper121ItemAdapter`, only basic metadata and `item_model` are compiled, while the entire `components` mapping is dropped.

## Goals / Non-Goals

**Goals:**
- Provide a clean, modular component registry (`ItemComponentRegistry`) in `CraftLab-plugin` allowing components to be registered and applied independently.
- Implement full `minecraft:equippable` support in `EquippableComponentApplier` covering both required (`slot`, `asset_id`/`model`) and all optional fields (`camera_overlay`, `equip_sound`, `allowed_entities`, `dispensable`, `swappable`, `damage_on_hurt`, `can_be_sheared`).
- Provide appliers for `minecraft:attribute_modifiers` and `minecraft:enchantments` so that existing Item Studio definitions work in-game.
- Maintain seamless multi-version compatibility via reflective capability detection (`isSupported()`), gracefully degrading without throwing exceptions on Paper 1.21.0 - 1.21.1.
- Provide advanced authoring controls in `CraftLab-frontend` (`ComponentBuilder.tsx`) to edit all optional equippable properties.

**Non-Goals:**
- Upgrading plugin compile dependencies to Paper 1.21.4 (would break binary class compatibility on Paper 1.21.1).
- Implementing components beyond equippable, attributes, and enchantments in this change (the registry architecture makes adding them trivial later).

## Decisions

### 1. Registry & Strategy Pattern for Item Data Components

**Decision**: Introduce `ItemComponentApplier` and `ItemComponentRegistry` in package `com.mcp.agent.adapters.components`:
```java
public interface ItemComponentApplier {
    String getComponentKey();
    boolean isSupported();
    void apply(ItemStack stack, ItemMeta meta, JsonElement componentData);
}
```
`ItemComponentRegistry` maintains a map of appliers keyed by component string (e.g., `"minecraft:equippable"`). When `Paper121ItemAdapter.compile()` runs, it invokes `registry.applyAll(stack, meta, itemJson.getAsJsonObject("components"))`.

*Alternative considered*: Hardcoding `if (components.has("minecraft:equippable"))` directly in `Paper121ItemAdapter.compile()`.  
*Rationale*: Rejected because the user specifically requested an extensible architecture where adding future components (food, tools, custom data, etc.) requires only creating a new class and registering it.

### 2. Reflective Invocation for Paper 1.21.2+ `EquippableComponent`

**Decision**: Implement `EquippableComponentApplier` using public reflection on `ItemMeta` and `EquippableComponent`:
- Dynamically detect `getEquippable` and `setEquippable` on `meta.getClass()`.
- If absent (e.g., Paper 1.21.0 - 1.21.1), `isSupported()` returns `false` and gracefully logs a debug notice.
- If present, retrieve `equippable = getEquippable.invoke(meta)`.
- Mutate the snapshot:
  - `slot`: Map string to `EquipmentSlot` (`HEAD`, `CHEST`, `LEGS`, `FEET`, `BODY`, `SADDLE`, `HAND`, `OFF_HAND`).
  - `asset_id` (fallback `model`): Parse `NamespacedKey` and invoke `setModel(NamespacedKey)`.
  - `camera_overlay`: If present, parse `NamespacedKey` and invoke `setCameraOverlay(NamespacedKey)`.
  - `equip_sound`: If present, parse sound string and invoke `setEquipSound(Sound)`.
  - `allowed_entities`: If present as array, map to `Collection<EntityType>` and invoke `setAllowedEntities(...)`.
  - Boolean flags: Invoke `setDispensable`, `setSwappable`, `setDamageOnHurt`, and reflectively invoke `canBeSheared` if present in the runtime.
- Apply back: `setEquippable.invoke(meta, equippable)`.

*Alternative considered*: Shading or compiling separate jars per Paper version (e.g. `CraftLab-plugin-1.21.1.jar`, `CraftLab-plugin-1.21.4.jar`).  
*Rationale*: A multi-jar distribution drastically increases build complexity, CI overhead, and user friction. Reflective detection aligns with how `applyItemModel` already works reliably in production.

### 3. Native Bukkit Appliers for Attributes & Enchantments

**Decision**:
- `AttributeModifiersComponentApplier`: Parses `minecraft:attribute_modifiers` array. For each modifier, resolves `org.bukkit.attribute.Attribute` and adds an `AttributeModifier` to `ItemMeta`.
- `EnchantmentsComponentApplier`: Parses `minecraft:enchantments` map (`{"sharpness": 5}`). Resolves `Enchantment.getByKey(NamespacedKey)` and applies it via `meta.addEnchant(enchant, level, true)`.

### 4. Advanced Equippable Settings UI in Frontend

**Decision**:
In `ComponentBuilder.tsx`, keep the core `slot` and `asset_id` fields prominent, and provide a collapsible "Advanced Equippable Options" toggle:
- `camera_overlay`: text input for namespaced key.
- `equip_sound`: text input for sound identifier.
- `allowed_entities`: comma-separated text input or tags.
- Toggles: `dispensable` (default: true), `swappable` (default: true), `damage_on_hurt` (default: true).

## Risks / Trade-offs

- **[Risk] Method signature variations across Paper micro-versions (e.g. `SADDLE` enum added in 1.21.4)**  
  *Mitigation*: Wrap enum lookups and optional property setter reflections in individual try-catch blocks so a single unsupported optional property does not fail the entire equippable component application.
- **[Risk] Unrecognized sound or entity type strings in JSON payload**  
  *Mitigation*: Safely validate entity and sound strings with case-insensitive matching; ignore invalid tokens and log a warning rather than aborting item generation.
- **[Risk] Performance overhead of reflection**  
  *Mitigation*: Item compilation occurs only upon `/mcp give` or deployment ingestion, not per-tick. Method references can optionally be cached in static fields.
