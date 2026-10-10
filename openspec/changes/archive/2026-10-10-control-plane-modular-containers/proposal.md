# Proposal

## Why

The CraftLab Control Plane web administration interface currently renders all supervisor functions, telemetry metrics, doctor diagnostics, release management controls, and real-time logs in a single monolithic dashboard view (`Dashboard.tsx`). As the CraftLab supervisor ecosystem expands to include security auditing, granular database diagnostics, runtime socket monitoring, and server agents, a flat single-screen dashboard suffers from visual clutter, poor information density, and lack of layout customization. 

Introducing a categorized navigation system alongside a modular, declaratively configured "Paginated Data Container" engine allows operators to navigate focused operational domains via top horizontal tabs while interacting with dense, adaptable panels that support both multi-step internal subviews and tabular data pagination without overloading viewport space. Furthermore, structuring container presets with a typed declarative schema and Tailwind CSS lays the groundwork for cross-frontend portability into `CraftLab-frontend`.

## What Changes

- **Horizontal Categorized Pages Navigation**: Replace the single-page flat grid layout with a top horizontal tab navigation bar categorizing panels into dedicated domains (`Overview / System`, `Lifecycle & Supervisor`, `Releases & Deployment`, `Doctor & Diagnostics`, `Audit & Logs`), preserving 100% horizontal viewport width for panel grids.
- **Paginated Data Container Component Engine**: Implement a modular `<ContainerEngine />` and preset registry supporting a hybrid pagination architecture:
  - `paginationMode: "subviews"`: Internal carousel-style multi-step views (e.g. Overview metrics -> Fine-grained thread counters -> Operational action forms) within a compact 1x1 or 2x1 card slot.
  - `paginationMode: "records"`: Tabular / collection pagination (pages of rows, offset/limit) for dynamic sets (releases, audit events, connected agents).
  - `paginationMode: "none"`: Static single-surface card for simple status indicators.
- **Typed Declarative Preset Schema**: Define a formal TypeScript/JSON schema specification (`PaginatedContainerPreset`) decoupling container layout, output display primitives (`metric_stat`, `gauge`, `progress_bar`, `key_value`, `status_pill`, `log_stream`), input control primitives (`button`, `toggle`, `text_input`, `number_input`, `select`), and data endpoints from imperative UI code.
- **Draggable & Resizable Grid Layout with Persistence**: Provide interactive drag handles (`[::]`) and resize handles to customize panel order and column/row spans, with automatic local persistence in browser `localStorage` and a "Reset to Default Layout" button per category.
- **Role-Based Input Access Control (RBAC)**: Enforce role requirements (`admin`, `operator`, `viewer`, `is_break_glass`) on input action primitives within container presets, disabling or hiding unauthorized triggers.
- **Styling Architecture Modernization with Tailwind CSS**: Configure Tailwind CSS in `CraftLab-ctl/web` aligning with `CraftLab-frontend`, ensuring container primitives and preset styles are cleanly exportable for future monorepo cross-frontend sharing.

## Capabilities

### New Capabilities

*(None. All changes enhance and expand the control system web administration capability.)*

### Modified Capabilities

- `control-system`: Extends requirements for the embedded web administration dashboard to mandate categorized page navigation, modular paginated data containers supporting both sub-views and record pagination, user-customizable draggable/resizable grid persistence, typed declarative container preset schemas, and role-based input action authorization.

## Impact

- **Frontend (`CraftLab-ctl/web`)**:
  - `package.json`: Add Tailwind CSS dependencies (`tailwindcss`, `postcss`, `autoprefixer`) and grid utilities.
  - `src/components/Dashboard.tsx`: Refactored and decomposed from a single ~800-line monolithic file into modular sub-components, horizontal category tabs, container engine, and declarative presets.
  - `src/components/containers/`: New modular component directory containing `ContainerEngine.tsx`, output primitives, input primitives, and preset definitions.
  - `src/types/presets.ts`: Typed schema contract for `PaginatedContainerPreset`, `InputPrimitive`, and `OutputPrimitive`.
- **Backend / Daemon (`CraftLab-ctl`)**:
  - No breaking changes to existing REST or WebSocket APIs; all existing endpoints (`/api/v1/lifecycle`, `/api/v1/metrics`, `/api/v1/doctor`, `/api/v1/update/releases`, `/api/v1/logs/ws`) continue to serve as data sources for container presets.
- **Future Reusability**:
  - Container primitives and schema definitions are crafted with agnostic styling tokens and props, enabling direct porting to `CraftLab-frontend`.
