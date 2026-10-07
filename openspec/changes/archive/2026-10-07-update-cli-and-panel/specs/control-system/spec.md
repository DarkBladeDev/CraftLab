# Spec Delta: Control System Update CLI and Dashboard Integration

## ADDED Requirements

### Requirement: Application Update and Release Lifecycle CLI Commands
The `craftctl` CLI tool SHALL expose dedicated subcommands and commands for application update lifecycle management, including checking GitHub releases, preparing and provisioning release environments, applying updates atomically, rolling back to previous versions, listing installed releases, and inspecting or toggling maintenance mode.

#### Scenario: Checking for updates via CLI
- **WHEN** `craftctl update check` is invoked
- **THEN** the CLI queries GitHub releases, compares the latest tag against current version, and prints release availability and release notes

#### Scenario: Staging a release via CLI
- **WHEN** `craftctl update prepare <version>` is invoked
- **THEN** the CLI downloads the release archive and checksum, verifies cryptographic integrity, extracts files into `releases/v<version>`, provisions the release virtual environment from cached wheels, and reports staged status

#### Scenario: Applying a release atomically via CLI
- **WHEN** `craftctl update apply <version>` is invoked for a staged release
- **THEN** the CLI commands `craftctld` to activate maintenance mode, stop the running application, switch the active release pointer, launch the updated application, poll readiness, and deactivate maintenance mode upon success

#### Scenario: Shorthand update execution via CLI
- **WHEN** `craftctl update <version>` is invoked
- **THEN** the CLI executes the prepare phase followed immediately by the apply phase in sequence with operator confirmation

#### Scenario: Rolling back release via CLI
- **WHEN** `craftctl rollback` is invoked with an optional target version
- **THEN** the CLI switches the active pointer to the specified or most recent prior release, restarts the service, and verifies operational readiness

#### Scenario: Listing installed releases via CLI
- **WHEN** `craftctl releases` is invoked
- **THEN** the CLI outputs all installed release directories, highlights the currently active release pointer, and displays maintenance mode status

#### Scenario: Managing maintenance mode via CLI
- **WHEN** `craftctl maintenance enable --message "<reason>"` or `craftctl maintenance disable` is invoked
- **THEN** the CLI toggles maintenance mode and records the status and reason

### Requirement: Remote Update and Release Management Endpoints
The `craftctld` HTTP gateway SHALL expose authenticated REST endpoints under `/api/v1/update/` for querying releases, preparing release artifacts, applying updates with automated rollback, executing rollbacks, and managing maintenance mode with RBAC role authorization and operation locking.

#### Scenario: Querying update status and releases via HTTP
- **WHEN** an authenticated user sends `GET /api/v1/update/releases` or `GET /api/v1/update/check`
- **THEN** the server returns the installed releases, active release pointer, maintenance state, and GitHub release metadata

#### Scenario: Preparing a release via HTTP
- **WHEN** an authenticated administrator sends `POST /api/v1/update/prepare` with a target version
- **THEN** the server acquires the mutation lock, executes release extraction and venv provisioning, logs the audit event, and returns operation results

#### Scenario: Applying an update with automated rollback via HTTP
- **WHEN** an authenticated administrator sends `POST /api/v1/update/apply` with a target version
- **THEN** the server executes the atomic switch, enters maintenance mode, starts the new version, verifies `/ready`, automatically reverts to the previous version if startup fails, and logs the outcome to the audit log

#### Scenario: Toggling maintenance mode via HTTP
- **WHEN** an authenticated operator sends `POST /api/v1/update/maintenance` with desired state and message
- **THEN** the server sets maintenance mode and returns the updated state

### Requirement: Interactive Release and Update Dashboard Management
The embedded single-page web administration dashboard SHALL provide interactive controls for inspecting release status, checking for GitHub releases, staging release packages, applying atomic updates with real-time feedback, rolling back to installed releases, and toggling maintenance mode.

#### Scenario: Inspecting releases and maintenance state in dashboard
- **WHEN** an administrator or operator accesses the administration dashboard
- **THEN** the dashboard renders an Updates card displaying current active release, installed versions, maintenance status badge, and update availability

#### Scenario: Triggering an update from dashboard
- **WHEN** an authorized user triggers update preparation and apply from the dashboard
- **THEN** the dashboard initiates the operations, shows live progress feedback, and updates status upon completion

#### Scenario: Reverting to a prior release from dashboard
- **WHEN** an authorized user selects a previously installed release and clicks Rollback
- **THEN** the dashboard issues the rollback request, displays progress, and refreshes service telemetry upon completion
