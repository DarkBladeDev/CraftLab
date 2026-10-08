---
name: plugin-docs-versioning
description: Technical specification and guidelines for agents on the documentation versioning format, schema, and rules required by the DarkBladeDev loader (github-docs-loader). Use when configuring, updating, or validating metadata.yml and historical plugin documentation.
---

# Plugin Documentation Versioning Specification

This skill instructs agents on how to structure, document, and maintain version history within plugin repositories across the **DarkBladeDev** ecosystem, ensuring that the portal's content loader (`github-docs-loader.ts`) can seamlessly ingest, cache, and serve multi-version documentation in Astro + Starlight.

---

## 1. Loader Operating Model

The DarkBladeDev documentation portal statically compiles documentation at build time following this lifecycle:

```
+-----------------------------------------------------------------------------------------+
|                               GITHUB-DOCS-LOADER LIFECYCLE                              |
+-----------------------------------------------------------------------------------------+

  1. PRIMARY INGESTION (Branch 'main' or localPath)
     └── Reads 'docs/metadata.yml'
         └── Extracts the 'versions: [...]' array

  2. CURRENT VERSION (LATEST)
     └── ALWAYS the first element in 'versions' (index 0).
     └── Extracted directly into the canonical root path:
         src/content/docs/[lang]/docs/<plugin-id>/[page].md
     └── Resulting URL route:
         /[lang]/docs/<plugin-id>/[page]/

  3. ARCHIVED VERSIONS (HISTORICAL)
     └── All subsequent elements (index >= 1) defining 'reference' and 'hasDocs !== false'.
     └── Downloaded as GitHub tarballs via the Git reference:
         https://api.github.com/repos/<repo>/tarball/<reference>
     └── Saved to an immutable local disk cache:
         .cache/docs-archives/<repo>_<reference>.tar.gz
     └── Extracted into version-prefixed subdirectories:
         src/content/docs/[lang]/docs/<plugin-id>/v<version>/[page].md
     └── Resulting URL route:
         /[lang]/docs/<plugin-id>/v<version>/[page]/

  4. VERSIONS WITHOUT DOCUMENTATION OR WITH ERRORS
     └── If hasDocs === false or 'reference' is omitted: skipped from documentation generation
         but preserved in catalog releases/downloads.
     └── If 'reference' does not exist or download fails: the loader emits a 'logger.warn'
         in the deployment logs and continues the build without breaking the website.
+-----------------------------------------------------------------------------------------+
```

---

## 2. Official `metadata.yml` Schema (`versions`)

Inside each plugin repository, at `docs/metadata.yml`, the `versions` block must follow this structure:

```yaml
id: craftingengine
name: CraftingEngine
description: Plugin description...

# ... other configurations (platforms, minecraft, folia, dependencies, links) ...

versions:
  # -------------------------------------------------------------
  # CURRENT VERSION (LATEST) -> Always the first entry [0]
  # -------------------------------------------------------------
  - version: "2.9.0"
    releaseDate: "2026-10-02"
    reference: "720aa8a"    # Commit SHA, release tag, or branch name
    downloadUrl: "https://github.com/Cypherlink-Studios/CraftingEngine/releases"
    changelog: "Property inheritance pipeline for ingredient PDC tags (PropertyInheritance)."
    minecraft:
      - "1.20.4"
      - "1.21.x"

  # -------------------------------------------------------------
  # ARCHIVED VERSIONS (HISTORICAL) -> With documentation
  # -------------------------------------------------------------
  - version: "2.8.0"
    releaseDate: "2026-10-02"
    reference: "v2.8.0"     # Immutable release Git tag or commit hash
    downloadUrl: "https://github.com/Cypherlink-Studios/CraftingEngine/releases"
    changelog: "Transactional input reservation (InputMode.RESERVE) and safe item returns."

  - version: "2.7.0"
    releaseDate: "2026-10-01"
    reference: "v2.7.0"
    downloadUrl: "https://github.com/Cypherlink-Studios/CraftingEngine/releases"
    changelog: "Consumable and dynamic workstation capabilities (CapabilityDrainPolicy)."

  # -------------------------------------------------------------
  # HISTORICAL VERSION WITHOUT DOCUMENTATION (Catalog / changelog only)
  # -------------------------------------------------------------
  - version: "2.6.1"
    releaseDate: "2026-09-30"
    hasDocs: false          # Skips docs download and page generation for this version
    downloadUrl: "https://github.com/Cypherlink-Studios/CraftingEngine/releases"
    changelog: "Root command alias migrated to /cfe and flight recorder added."
```

---

## 3. Version Field Definitions

| Field | Type | Required | Description and Rules |
| :--- | :--- | :--- | :--- |
| `version` | `string` | **Yes** | Semantic version number (e.g., `"2.9.0"`, `"2.8.0"`). Automatically normalized into a `v`-prefixed slug in URL paths (`v2.8.0`). |
| `reference` | `string` | Conditional | Git identifier for the release: can be a **release tag** (e.g., `"v2.8.0"`), a **commit SHA** (e.g., `"720aa8a"`), or a **branch** (`"release/2.8"`). **Required** for historical versions that should generate documentation. |
| `releaseDate` | `string` | No | Release date in ISO `YYYY-MM-DD` format (e.g., `"2026-10-02"`). |
| `downloadUrl` | `string` | No | Valid HTTP/HTTPS URL where users can download the binary `.jar` or inspect the release on GitHub, Modrinth, or Hangar. |
| `changelog` | `string` | No | Text summary or release notes highlighting notable changes introduced in this version. |
| `minecraft` | `string[]` | No | List of Minecraft versions specifically tested or supported by this version of the plugin. |
| `hasDocs` | `boolean` | No (default: `true`) | When `false`, the loader **will not attempt to download documentation** for this version, excluding it from the docs navigation tree while keeping it in catalog releases and changelogs. |
| `docPath` | `string` | No (default: `"docs"`) | Subfolder within the remote repository where documentation files reside, if different from `docs/`. |

---

## 4. Critical Rules for Agents

1. **Strict Ordering for the Active Version**:
   * The loader treats `versions[0]` as the **current active release**.
   * This version is always served at the canonical root path `/[lang]/docs/<plugin-id>/...` without any version prefix in the URL.
   * Archived versions (`versions[1..N]`) are served at `/[lang]/docs/<plugin-id>/v<version>/...`.

2. **Immutability and Caching**:
   * Git references for archived versions should preferably be **fixed release tags** (e.g., `v2.8.0`) or **commit SHAs** (`720aa8a`).
   * The loader caches downloads permanently under `.cache/docs-archives/`. Never use moving branches (such as `dev` or `latest`) as the `reference` for archived releases.

3. **Slug Parity Across Locales in Historical Releases**:
   * In each referenced historical release, Markdown filenames in `docs/es/` and `docs/en/` must match identically (e.g., `docs/es/animations.md` and `docs/en/animations.md`).
   * If an older release lacks translations, the loader emits a warning to prevent navigation mismatches in Starlight.

4. **CI/CD and Deployment Resilience**:
   * If a historical version specifies an invalid or unreachable `reference`, the loader **will not fail the build**. It emits a `logger.warn` message and skips that archived version.
   * To prevent unnecessary network lookups for releases that never contained a `/docs` folder, explicitly set `hasDocs: false` or omit the `reference` field.

---

## 5. Agent Validation Checklist

Before finalizing version configuration on any plugin repository:

- [ ] Is the latest / current version located at the first position in `versions`?
- [ ] Do all archived versions that need documentation define a valid `reference` (tag or commit SHA)?
- [ ] Do older versions without documentation specify `hasDocs: false` or omit `reference`?
- [ ] Are all `downloadUrl` fields valid, absolute URLs?
- [ ] Were `pnpm test` and `pnpm check` executed in the portal repository to ensure the schema passes Zod validation?
