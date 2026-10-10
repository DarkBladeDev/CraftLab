# Design

## Context

The current `CraftLab-ctl/web` interface consists of an ~800-line monolithic React component (`Dashboard.tsx`) using hardcoded inline styles (`#0b0f19`, `#1e293b`) that bundles lifecycle management, psutil telemetry, environmental doctor checks, release packaging/rollback, and WebSocket logs into a single flat view.

In parallel, `CraftLab-frontend` in the same monorepo is built with React 18, Vite, Lucide-react, and Tailwind CSS. The user requested:
1. Categorized pages navigated via top horizontal tabs to prevent viewport width loss.
2. A modular Paginated Data Container system using a hybrid pagination architecture (`subviews` and `records`).
3. Declarative typed preset schemas in TypeScript/JSON.
4. User-customizable drag-and-drop reordering and resizing of panels, persisted in `localStorage`.
5. Designing components with Tailwind CSS for future portability into `CraftLab-frontend`.

## Goals / Non-Goals

**Goals:**
- Decompose the flat dashboard into a categorized view driven by top horizontal tabs (`System & Telemetry`, `Lifecycle & Supervisor`, `Releases & Deployment`, `Doctor & Diagnostics`, `Audit & Logs`).
- Implement a reusable `<ContainerEngine />` and preset registry supporting:
  - `paginationMode: "subviews"` for multi-step mode switching within compact cards.
  - `paginationMode: "records"` for paginating collection rows/tables.
  - `paginationMode: "none"` for single-surface status panels.
- Build a lightweight CSS Grid layout system supporting drag-to-reorder, column/row resize controls, `localStorage` persistence, and a "Reset Layout" action.
- Define a formal TypeScript contract (`PaginatedContainerPreset`) decoupling output primitives (`MetricStat`, `Gauge`, `KeyValueList`, `StatusPill`, `LogStream`) and input primitives (`ActionButton`, `ToggleSwitch`, `TextInput`, `NumberStepper`, `Select`).
- Implement Role-Based Access Control (RBAC) guards directly on input action primitives based on current user roles (`admin`, `operator`, `viewer`, `is_break_glass`).
- Configure Tailwind CSS in `CraftLab-ctl/web` ensuring style tokens and primitive components match `CraftLab-frontend`.

**Non-Goals:**
- Modifying `craftctld` Python daemon supervisor endpoints or backend business logic.
- Cloud or database sync for dashboard layout customization (layout state is stored per-browser in `localStorage`).
- Porting the entire `CraftLab-frontend` application in this change; this change establishes the shared architecture and proves it in `CraftLab-ctl/web`.

## Decisions

### Decision 1: Horizontal Navigation Tabs over Sidebar
- **Rationale**: A sidebar reduces available horizontal width, which degrades wide data containers like log streams, tabular telemetry, and multi-column forms. Horizontal top tabs keep 100% of the screen width available for dashboard grid cards.
- **Alternatives considered**: Collapsible left sidebar (rejected to preserve full screen width for multi-column grids).

### Decision 2: Hybrid Pagination Architecture (`subviews` vs `records`)
- **Rationale**:
  - `subviews` provides internal carousel-like mode switching within a single card (e.g., Page 1: High-level CPU/RAM $\rightarrow$ Page 2: Granular Thread/Disk metrics $\rightarrow$ Page 3: Trigger Diagnostics).
  - `records` handles collections where item counts vary dynamically (Releases, rollbacks, audit log events, connected targets).
- **Alternatives considered**:
  - Subviews only: Would force awkward splitting of tabular data into arbitrary slides.
  - Tabular records only: Would not solve the challenge of embedding compact controls and telemetry in the same card slot.

### Decision 3: Typed Declarative Preset Schema
- **Architecture**:
  ```typescript
  export interface PaginatedContainerPreset {
    id: string;
    title: string;
    icon?: string;
    category: "system" | "lifecycle" | "releases" | "doctor" | "logs";
    defaultGrid: { cols: number; rows: number; minCols?: number; maxCols?: number };
    paginationMode: "subviews" | "records" | "none";
    pages?: ContainerSubViewPage[];
    collection?: ContainerCollectionConfig;
  }
  ```
- **Rationale**: Presets can be registered statically or dynamically without altering the rendering engine. New diagnostic cards or audit cards can be added in single declarative files.

### Decision 4: Lightweight Drag & Resize Grid
- **Architecture**:
  - Container items use responsive CSS Grid (`grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4`).
  - Cards support drag reordering via HTML5 Drag and Drop handles (`[::]`) and resize step buttons (`- / + Cols`).
  - Layout configuration is stored in `localStorage` under key `craftlab_ctl_layout_v1:<category>` with schema validation. A "Reset Layout" button restores default geometries.
- **Alternatives considered**:
  - Heavy 3rd-party canvas/grid libraries (`react-grid-layout`, `gridstack`): Introduce large bundles and DOM mutation conflicts with React 18 state. A lightweight CSS Grid with native drag-and-drop handles provides better performance and predictability.

### Decision 5: Adopting Tailwind CSS in `CraftLab-ctl/web`
- **Architecture**:
  - Add `tailwindcss`, `postcss`, and `autoprefixer` to `CraftLab-ctl/web/package.json`.
  - Configure `tailwind.config.js` with dark theme color tokens aligned with `CraftLab-frontend`.
  - Replace inline style dictionaries in `Dashboard.tsx` with semantic utility classes.

### Decision 6: RBAC Guarding in Input Primitives
- **Architecture**:
  - Every input primitive specifies `requiredRoles?: string[]` and `allowBreakGlass?: boolean`.
  - The primitive evaluates active session `user.roles` and `user.is_break_glass`. If unauthorized, it renders with disabled visual indicators and displays a tooltip explaining required privileges.

## Risks / Trade-offs

- **[Risk: Stale or corrupt layout in `localStorage`]** $\rightarrow$ **Mitigation**: Wrap `localStorage` read operations in try-catch with fallback to default preset geometries, and provide a one-click "Reset Layout" button in the category header.
- **[Risk: Tailwind CSS style collisions during migration]** $\rightarrow$ **Mitigation**: Configure Tailwind's preflight and standard dark theme tokens, thoroughly validating that existing modals and components retain their high-contrast dark aesthetic.
- **[Risk: Performance overhead of frequent telemetry updates across multiple paginated containers]** $\rightarrow$ **Mitigation**: Centralize the 3-second polling interval and WebSocket listener in a React context (`SupervisorDataContext`), passing sliced data to containers via props/memo to avoid unnecessary re-renders.

## Migration Plan

1. Configure Tailwind CSS in `CraftLab-ctl/web` (`package.json`, `tailwind.config.js`, `postcss.config.js`, `src/index.css`).
2. Implement schema types in `src/types/presets.ts`.
3. Implement primitive output components (`MetricStat`, `Gauge`, `KeyValueGrid`, `StatusPill`, `LogStream`) and input components (`ActionButton`, `ToggleSwitch`, `TextInput`, `Select`).
4. Build `<ContainerEngine />` supporting `subviews`, `records`, and `none`.
5. Build `<CategoryTabBar />` and `<DraggableGrid />` with `localStorage` persistence.
6. Migrate existing dashboard panels into registered presets:
   - `overview-telemetry` (subviews)
   - `lifecycle-supervisor` (subviews)
   - `doctor-diagnostics` (subviews)
   - `releases-manager` (records)
   - `live-log-stream` (none, full width)
7. Update `Dashboard.tsx` to mount the new architecture and verify existing functionality.
