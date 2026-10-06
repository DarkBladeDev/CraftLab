# Tasks: Multi-Version Resource Pack Compatibility (1.21.1 - 1.21.11)

## 1. Content Model and Schema Extensions

- [x] 1.1 Add `item_model` optional field to `ItemDefinition` Pydantic schemas and SQLAlchemy entity models in `backend/app/models/` and verify unit tests pass
- [x] 1.2 Update item draft CRUD endpoints in `backend/app/api/items.py` to validate and persist `item_model` values

## 2. Pre-Flight Validator Multi-Version Checks

- [x] 2.1 Extend `PreflightValidator` in `backend/app/domain/pack_validator.py` to inspect and detect collisions on `item_model` identifiers across active layers
- [x] 2.2 Add unit tests in `backend/tests/test_pack_validator.py` verifying collision errors when two items declare identical `item_model` keys

## 3. Canonical Model AST and Dual-Projection Compiler

- [x] 3.1 Implement `ItemModelMapping` AST in `backend/app/domain/pack_merger.py` to represent canonical mappings between material, CMD, model path, and item_model
- [x] 3.2 Implement dual projection in `SemanticMerger`: generating legacy `models/item/<mat>.json` overrides for base layer and modern `items/<mat>.json` Item Definitions in `overlay_v1_21_2` matching `vanilla-mcdoc` schemas
- [x] 3.3 Implement bidirectional format translation for pack source ingestion (converting legacy plugin packs to modern definitions and modern packs to legacy overrides)
- [x] 3.4 Update `DeterministicPackCompiler` in `backend/app/domain/pack_compiler.py` to generate `pack.mcmeta` with `supported_formats: {"min_inclusive": 34, "max_inclusive": 65}` and overlay `overlay_v1_21_2`
- [x] 3.5 Add unit tests in `backend/tests/test_pack_merger.py` and `backend/tests/test_pack_compiler.py` testing dual projection and overlay packaging

## 4. Paper Agent Runtime Compatibility

- [x] 4.1 Update `PaperItemAdapter` in `paper-agent` to apply `setCustomModelData` and reflectively set `item_model` component on Paper 1.21.2+ runtimes
- [x] 4.2 Add unit test in `paper-agent/src/test/java/` verifying item metadata assembly with both CustomModelData and ItemModel keys

## 5. Frontend Studio and Pack Manager UI

- [x] 5.1 Add `item_model` input field and auto-derivation indicator in `frontend/src/features/items/`
- [x] 5.2 Add multi-version badges (1.21.1 legacy and 1.21.2+ modern) in the inventory slot preview and tooltip
- [x] 5.3 Update `ResourcePackManagerView.tsx` to display Universal Hybrid Pack details and overlay layers

## 6. End-to-End Verification

- [x] 6.1 Add E2E tests in `backend/tests/test_e2e_full_workflow.py` compiling a universal hybrid pack with studio items and verifying zip structure and SHA-1
- [x] 6.2 Verify full test suite across Backend (`pytest backend`), Paper Agent (`gradlew test`), and Frontend (`npm run build`)
