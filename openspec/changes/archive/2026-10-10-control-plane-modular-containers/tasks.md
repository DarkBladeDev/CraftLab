# Tasks

## 1. Setup & Styling Foundation

- [x] 1.1 Configure Tailwind CSS in `CraftLab-ctl/web` (`package.json`, `postcss.config.js`, `tailwind.config.js`, `src/index.css`) and verify build succeeds with `npm run build`
- [x] 1.2 Author typed preset schema contracts in `CraftLab-ctl/web/src/types/presets.ts` (`PaginatedContainerPreset`, `InputPrimitive`, `OutputPrimitive`, `LayoutConfig`) and verify TypeScript compilation with `npx tsc --noEmit`

## 2. Primitives & RBAC Controls

- [x] 2.1 Implement output display primitives in `src/components/primitives/outputs/` (`MetricStat`, `Gauge`, `KeyValueGrid`, `StatusPill`, `LogTerminalView`) styled with Tailwind CSS and verify visual rendering
- [x] 2.2 Implement input control primitives in `src/components/primitives/inputs/` (`ActionButton`, `ToggleSwitch`, `TextInput`, `NumberStepper`, `Select`) with role-based access control (`requiredRoles`, `allowBreakGlass`) and verify that unauthorized controls render disabled with role notices

## 3. Container Engine & Component Presets

- [x] 3.1 Implement `<ContainerEngine />` in `src/components/containers/ContainerEngine.tsx` supporting `subviews`, `records`, and `none` pagination modes with interactive page indicators and action dispatchers, verifying pagination state navigation
- [x] 3.2 Implement declarative supervisor presets in `src/components/containers/presets/` (`overview-telemetry`, `lifecycle-supervisor`, `doctor-diagnostics`, `releases-manager`, `live-log-stream`) and verify schema compliance

## 4. Categorized Pages & Draggable Grid

- [x] 4.1 Implement `<CategoryTabBar />` with horizontal navigation tabs (`System & Telemetry`, `Lifecycle & Supervisor`, `Releases & Updates`, `Doctor & Diagnostics`, `Audit & Logs`) and verify active category switching
- [x] 4.2 Implement `<DraggableGrid />` featuring drag-and-drop panel reordering, responsive column/row span resizing, `localStorage` persistence (`craftlab_ctl_layout_v1`), and a "Reset Layout" button, verifying that custom positions restore upon page reload

## 5. Dashboard Integration & Verification

- [x] 5.1 Refactor `Dashboard.tsx` to mount `CategoryTabBar`, `DraggableGrid`, and `ContainerEngine` with centralized polling and WebSocket context, verifying that supervisor lifecycle commands, doctor checks, releases, and log streaming operate seamlessly
- [x] 5.2 Build the web assets (`npm run build`) in `CraftLab-ctl/web` and execute the Python control test suite (`pytest tests/`) to verify end-to-end supervisor static serving and API compatibility
