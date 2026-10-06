# Proposal: Real Runtime Execution and Mock Elimination

## Why

The platform has relied on a Python-based mock agent (`backend/mock_agent.py`) and simulated storage (`backend/mock_server_storage/items.json`) to verify local developer workflows and frontend interactions. To ensure authentic end-to-end functionality, the development and testing environment must execute against a real Minecraft Paper 1.21 server runtime where items, virtual display props, resource packs, and revisions are authored, compiled, and persisted purely in runtime without artificial mocks or hardcoded fixture items.

## What Changes

- **Deprecation and Removal of Mock Agent**: Remove `backend/mock_agent.py` and `backend/mock_server_storage/`. Eliminate all mock execution modes.
- **Real Server Environment Integration (`MCP_PAPER_SERVER_DIR`)**: Configure `dev.ps1` to integrate with a real local Paper 1.21 server identified by the `MCP_PAPER_SERVER_DIR` environment variable (or command-line parameter).
- **Flexible Server Startup Mechanics**:
  - Support user-defined startup scripts via `MCP_PAPER_START_SCRIPT` (e.g. `run.bat`).
  - Support direct JAR execution via `MCP_PAPER_SERVER_JAR` or automatic detection of `paper*.jar` / `server*.jar`.
- **Preflight Plugin Deployment & Verification**:
  - Automatically compile `paper-agent-1.0.0-SNAPSHOT.jar` and deploy it to `$MCP_PAPER_SERVER_DIR/plugins/`.
  - Verify that required server runtime dependencies (such as `PacketEvents` 2.14+ for virtual display props) are present in the server's `plugins/` directory, logging an advisory warning if absent.
  - Ensure the agent's `config.yml` connects to the local WebSocket gateway (`ws://127.0.0.1:8000/ws/agent`).
- **Pristine State & Clean-Slate Option**:
  - Add `-CleanData` flag to `dev.ps1` to wipe legacy/residual test data from `backend/mcp.db` and compilation cache (`data/packs/dist/`, `data/packs/tmp/`), ensuring all items tested originate from live runtime creation.
- **Resource Pack Local HTTP Distribution Verification**:
  - Confirm the end-to-end pipeline where compiled resource packs are served via the FastAPI endpoint (`GET /api/v1/packs/{target_id}/download`) and applied in real-time to players joining the Paper server via `ResourcePackJoinListener`.

## Capabilities

### New Capabilities
None. (This change adapts developer tooling, test environments, and runtime orchestration).

### Modified Capabilities
None. (The functional requirements of existing capabilities such as `paper-agent-adapter`, `deployment-engine`, `target-management`, and `resource-pack-pipeline` remain unaltered and are now executed on native Paper runtimes rather than mock simulators. Hence, `skip_specs: true` is configured).

## Impact

- **Developer Workflow**: `dev.ps1` launches the live Paper 1.21 server in an interactive terminal alongside FastAPI and Vite, instead of running `mock_agent.py`.
- **Repository Cleanliness**: Removal of `mock_agent.py` and dummy JSON storage folders.
- **Database**: Fresh SQLite state with zero pre-seeded mock items.
