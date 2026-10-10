# Spec Delta

## ADDED Requirements

### Requirement: Categorized Pages Navigation in Web Administration Dashboard
The embedded single-page web administration dashboard SHALL provide a horizontal category tab navigation system that groups dashboard panels into distinct operational domains, preserving full viewport width for active domain panels.

#### Scenario: Switching operational categories
- **WHEN** an authenticated user selects a category tab (e.g., `System & Telemetry`, `Lifecycle & Supervisor`, `Releases & Updates`, or `Audit & Logs`)
- **THEN** the dashboard switches the active view and renders the registered data container panels assigned to that category without reloading the browser page

#### Scenario: Persistent category tab selection across refreshes
- **WHEN** a user switches to a category tab and reloads the browser
- **THEN** the dashboard restores the previously active category tab from the browser URL or session storage

### Requirement: Modular Paginated Data Container Engine
The web administration dashboard SHALL provide a modular data container engine capable of rendering panels defined as presets, supporting both sub-view switching and data collection pagination.

#### Scenario: Sub-views internal pagination mode
- **WHEN** a container preset configured with `paginationMode: "subviews"` is rendered
- **THEN** the container displays internal pagination controls (`◀` / `▶` and page indicators) that navigate across discrete sub-view pages (such as metric summary, granular telemetry, and action forms) within a constant panel footprint

#### Scenario: Records collection pagination mode
- **WHEN** a container preset configured with `paginationMode: "records"` is rendered with tabular or collection data
- **THEN** the container renders collection items divided by page size and displays page controls that navigate pages of items without changing the card structure

#### Scenario: Single non-paginated container mode
- **WHEN** a container preset configured with `paginationMode: "none"` is rendered
- **THEN** the container renders its contents directly without pagination navigation elements

### Requirement: Draggable and Resizable Dashboard Layout with Persistence
The web administration dashboard SHALL provide an interactive layout grid allowing operators to rearrange panel positions and resize column and row spans, persisting layout preferences locally.

#### Scenario: Reordering containers via drag and drop
- **WHEN** an operator drags a container by its handle and drops it in a new grid position
- **THEN** the dashboard reorders the panels in the grid and saves the new sequence to `localStorage`

#### Scenario: Resizing container dimensions
- **WHEN** an operator resizes a container using its resize handle
- **THEN** the dashboard updates the panel's column and row spans within configured min/max constraints and saves the updated geometry to `localStorage`

#### Scenario: Resetting layout to defaults
- **WHEN** an operator clicks the "Reset Layout" action for a category
- **THEN** the dashboard restores all container positions and sizes in that category to their preset default grid dimensions and clears customized overrides from `localStorage`

### Requirement: Declarative Container Preset Contract and Role-Based Input Control
The dashboard container engine SHALL evaluate typed declarative presets specifying output primitives, input action primitives, and role-based access restrictions.

#### Scenario: Rendering typed output primitives
- **WHEN** the container engine evaluates output declarations
- **THEN** it renders the declared primitives (`metric_stat`, `gauge`, `progress_bar`, `key_value`, `status_pill`, or `log_stream`) bound to live supervisor data

#### Scenario: Enforcing role-based access on input controls
- **WHEN** an input primitive specifies a required role (e.g. `admin` or `operator`) and the active session lacks that role or break-glass access
- **THEN** the container engine disables or hides the interactive input control and prevents action dispatch

#### Scenario: Executing authorized container action
- **WHEN** an authorized operator activates an input action control (e.g. lifecycle start, doctor probe, or release rollback)
- **THEN** the container engine dispatches the operation request to the supervisor API, shows real-time action feedback, and refreshes dependent container outputs
