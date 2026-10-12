# Tasks: Extensible Item Components Pipeline & Full Equippable Support

## 1. Plugin Component Registry & Contracts

- [x] 1.1 Create `ItemComponentApplier` interface and `ItemComponentRegistry` in `CraftLab-plugin/src/main/java/com/mcp/agent/adapters/components/`; verify compilation with `./gradlew compileJava`.
- [x] 1.2 Integrate `ItemComponentRegistry` into `Paper121ItemAdapter.java` to dispatch `components` map entries during `compile()`; verify adapter unit tests.

## 2. Equippable Component Applier

- [x] 2.1 Implement `EquippableComponentApplier` in `CraftLab-plugin/src/main/java/com/mcp/agent/adapters/components/` with reflective access to `getEquippable` and `setEquippable`, mapping `slot`, `asset_id`/`model`, and all optional attributes (`camera_overlay`, `equip_sound`, `allowed_entities`, boolean flags); verify with unit tests.
- [x] 2.2 Add unit tests for `EquippableComponentApplier` in `CraftLab-plugin/src/test/java/com/mcp/agent/adapters/` testing field parsing, reflective setter invocation, and safe degradation when methods are absent; verify with `./gradlew test`.

## 3. Attribute Modifiers & Enchantment Appliers

- [x] 3.1 Implement `AttributeModifiersComponentApplier` and `EnchantmentsComponentApplier` in `CraftLab-plugin/src/main/java/com/mcp/agent/adapters/components/`; verify with unit tests.
- [x] 3.2 Register all default appliers in `ItemComponentRegistry` within `Paper121ItemAdapter`; verify end-to-end item compilation tests.

## 4. Frontend Item Studio Advanced Equippable Controls

- [x] 4.1 Update `ComponentBuilder.tsx` in `CraftLab-frontend/src/features/items/` to add collapsible advanced equippable controls (`camera_overlay`, `equip_sound`, `allowed_entities`, `dispensable`, `swappable`, `damage_on_hurt`); verify UI interaction and JSON serialization.
- [x] 4.2 Verify frontend build with `npm run build` in `CraftLab-frontend`.

## 5. End-to-End Verification & Documentation

- [x] 5.1 Run full backend test suite (`pytest`) and Gradle test suite (`./gradlew test`) to verify zero regressions.
- [x] 5.2 Update technical documentation in `docs/en/` and `docs/es/` documenting the extensible component pipeline and supported data components.
