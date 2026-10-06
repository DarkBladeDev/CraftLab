# Tasks

## 1. Mock Decommissioning & Repository Cleanup

- [x] 1.1 Remove `backend/mock_agent.py` and `backend/mock_server_storage/` and verify files no longer exist in repository.
- [x] 1.2 Clean residual test records (mock catalog items, placeholder items, test targets) from `backend/mcp.db` and empty cached build folders in `data/packs/dist/` and `data/packs/tmp/`.

## 2. Dev Runner Adaptation (`dev.ps1`)

- [x] 2.1 Add parameters and environment variable resolution for `MCP_PAPER_SERVER_DIR`, `MCP_PAPER_START_SCRIPT`, `MCP_PAPER_SERVER_JAR`, and `-CleanData` in `dev.ps1`.
- [x] 2.2 Implement pre-flight deployment routine in `dev.ps1`: build `paper-agent` JAR with Gradle, copy to `$MCP_PAPER_SERVER_DIR\plugins\`, check for PacketEvents (`*packetevents*.jar`), and verify target config.
- [x] 2.3 Implement multi-tier Paper server startup in `dev.ps1` (execute custom start script, explicit JAR, or auto-detect `paper*.jar`/`server*.jar`) in an interactive PowerShell console with process title `MCP - Paper 1.21 Server`.
- [x] 2.4 Implement `-CleanData` flag handling in `dev.ps1` to reset SQLite database and pack cache for pristine testing.

## 3. Integration & Runtime Verification

- [x] 3.1 Run backend pytest suite to verify all API, database, compiler, and revision tests pass without mock agent dependencies.
- [x] 3.2 Run `paper-agent` Gradle tests to ensure plugin compile and adapter tests pass.
- [x] 3.3 Perform dev runner verification to confirm correct resolution of Paper server parameters and pre-flight dependency warnings.
