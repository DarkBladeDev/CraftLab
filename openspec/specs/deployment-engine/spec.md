# Deployment Engine

## Purpose
The Deployment Engine capability orchestrates synchronization, 3-way difference comparison, conflict detection, deployment planning, approvals, and controlled execution of content changes onto target servers.

## Requirements

### Requirement: Deterministic Deployment Planning
The system MUST generate deterministic, immutable deployment plans that pair a specific immutable project revision with an explicit target server.

#### Scenario: Generating a deployment plan
- **WHEN** an authorized user requests a plan for a project revision against a target
- **THEN** the platform generates an immutable plan enumerating the discrete operations (adds, updates, deletes) required to reconcile desired and target states

### Requirement: Explicit Conflict Detection
The synchronization engine MUST detect discrepancies between project revision, baseline, and observed target state, never silently overwriting conflicting changes.

#### Scenario: Detecting concurrent modifications
- **WHEN** a resource has been modified on the target independently of the project revision since the last baseline
- **THEN** the system marks the resource as in conflict and prevents automatic publication until explicitly resolved

### Requirement: Plan Approval Lifecycle
Deployment plans MUST be reviewed and approved by an authorized user before execution can proceed.

#### Scenario: Approval of deployment plan
- **WHEN** a user with Publisher permission reviews and approves an exact deployment plan hash
- **THEN** the plan transitions to approved state and becomes eligible for execution

#### Scenario: Plan invalidation on target state change
- **WHEN** a target reports state drift or reconnects with different capabilities after a plan is approved
- **THEN** the plan is invalidated and must be regenerated and re-approved

### Requirement: Step-by-Step Execution and Partial State Tracking
The engine MUST coordinate step-by-step operation execution and honestly report partial completion without claiming non-existent atomic rollbacks.

#### Scenario: Successful full execution
- **WHEN** all operations in an approved plan are executed by the agent and return success
- **THEN** the deployment status is marked as applied and the new target baseline is updated

#### Scenario: Partial deployment failure
- **WHEN** an operation fails mid-execution
- **THEN** execution halts, the deployment records exact per-operation outcomes, marks the status as partially applied, and provides diagnostic logs for recovery

### Requirement: Item Deployment Plan Execution
The deployment engine SHALL generate deterministic plans containing `create_or_update_item` operations for item definitions and track live execution progress through agent confirmation.

#### Scenario: Item deployment execution flow
- **WHEN** an approved item deployment plan is executed against an online target
- **THEN** the engine sends the operation via the agent gateway, awaits the correlated operation result, and transitions deployment status to `applied` upon success

#### Scenario: Execution failure handling
- **WHEN** the agent returns an execution error or the target disconnects during operation execution
- **THEN** the deployment status transitions to `failed` and captures the error details in the execution log
