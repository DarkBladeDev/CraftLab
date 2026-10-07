import React, { useState, useEffect, useRef } from "react";
import {
  api,
  UserContext,
  ServiceStatus,
  SystemMetrics,
  DoctorResult,
  ReleasesInfo,
  UpdateCheckResult,
} from "../api";

interface DashboardProps {
  user: UserContext;
  onLogout: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ user, onLogout }) => {
  const [status, setStatus] = useState<ServiceStatus | null>(null);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [doctor, setDoctor] = useState<DoctorResult | null>(null);
  const [releasesInfo, setReleasesInfo] = useState<ReleasesInfo | null>(null);
  const [updateCheck, setUpdateCheck] = useState<UpdateCheckResult | null>(null);
  const [targetVersion, setTargetVersion] = useState<string>("");
  const [selectedRollback, setSelectedRollback] = useState<string>("");
  const [logs, setLogs] = useState<string[]>([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [message, setMessage] = useState<{ text: string; type: "ok" | "err" } | null>(null);

  const logsEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const isAdminOrOperator = user.is_break_glass || user.roles.includes("admin") || user.roles.includes("operator");

  // Fetch status, metrics & releases
  const refreshData = async () => {
    try {
      const [s, m, r] = await Promise.all([
        api.getStatus(),
        api.getMetrics(),
        api.getReleases().catch(() => null),
      ]);
      setStatus(s);
      setMetrics(m);
      if (r) setReleasesInfo(r);
    } catch (err: any) {
      console.error("Failed to refresh status/metrics:", err);
    }
  };

  useEffect(() => {
    refreshData();
    const interval = setInterval(refreshData, 3000);
    return () => clearInterval(interval);
  }, []);

  // WebSocket for real-time logs
  useEffect(() => {
    const ws = api.createLogWebSocket();
    wsRef.current = ws;

    ws.onmessage = (event) => {
      setLogs((prev) => [...prev.slice(-999), event.data]);
    };

    ws.onerror = (err) => {
      console.warn("WebSocket error:", err);
    };

    return () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, autoScroll]);

  const handleAction = async (action: string) => {
    setActionLoading(action);
    setMessage(null);
    try {
      const res = await api.executeLifecycle(action);
      setMessage({ text: res.message || `Action ${action} succeeded`, type: "ok" });
      await refreshData();
    } catch (err: any) {
      setMessage({ text: err.message || `Action ${action} failed`, type: "err" });
    } finally {
      setActionLoading(null);
    }
  };

  const handleRunDoctor = async () => {
    setActionLoading("doctor");
    setMessage(null);
    try {
      const doc = await api.getDoctor();
      setDoctor(doc);
      setMessage({ text: `Doctor completed: ${doc.overall}`, type: doc.overall === "FAIL" ? "err" : "ok" });
    } catch (err: any) {
      setMessage({ text: err.message || "Failed to run doctor", type: "err" });
    } finally {
      setActionLoading(null);
    }
  };

  const handleCheckUpdates = async () => {
    setActionLoading("check_updates");
    setMessage(null);
    try {
      const res = await api.checkUpdates();
      setUpdateCheck(res);
      setMessage({
        text: res.update_available
          ? `New version ${res.latest_version} is available!`
          : `CraftLab is up to date (${res.current_version})`,
        type: "ok",
      });
    } catch (err: any) {
      setMessage({ text: err.message || "Failed to check for updates", type: "err" });
    } finally {
      setActionLoading(null);
    }
  };

  const handlePrepareUpdate = async (ver: string) => {
    if (!ver) return;
    setActionLoading("prepare_update");
    setMessage(null);
    try {
      const res = await api.prepareUpdate(ver);
      if (res.success) {
        setMessage({ text: res.message || `Release ${ver} prepared successfully!`, type: "ok" });
        await refreshData();
      } else {
        setMessage({ text: res.error || `Failed to prepare release ${ver}`, type: "err" });
      }
    } catch (err: any) {
      setMessage({ text: err.message || `Failed to prepare release ${ver}`, type: "err" });
    } finally {
      setActionLoading(null);
    }
  };

  const handleApplyUpdate = async (ver: string) => {
    if (!ver) return;
    if (!window.confirm(`Applying release ${ver} will restart the backend service. Proceed?`)) {
      return;
    }
    setActionLoading("apply_update");
    setMessage(null);
    try {
      const res = await api.applyUpdate(ver);
      if (res.success) {
        setMessage({ text: res.message || `Release ${ver} applied successfully!`, type: "ok" });
        await refreshData();
      } else {
        setMessage({ text: res.error || `Failed to apply release ${ver}`, type: "err" });
      }
    } catch (err: any) {
      setMessage({ text: err.message || `Failed to apply release ${ver}`, type: "err" });
    } finally {
      setActionLoading(null);
    }
  };

  const handleRollback = async (ver?: string) => {
    const targetDesc = ver || "previous release";
    if (!window.confirm(`Roll back to ${targetDesc}? This will restart the backend service.`)) {
      return;
    }
    setActionLoading("rollback");
    setMessage(null);
    try {
      const res = await api.rollbackUpdate(ver);
      if (res.success) {
        setMessage({ text: res.message || `Successfully rolled back to ${targetDesc}!`, type: "ok" });
        await refreshData();
      } else {
        setMessage({ text: res.error || "Rollback failed", type: "err" });
      }
    } catch (err: any) {
      setMessage({ text: err.message || "Rollback failed", type: "err" });
    } finally {
      setActionLoading(null);
    }
  };

  const handleToggleMaintenance = async () => {
    if (!releasesInfo) return;
    const nextState = !releasesInfo.maintenance.enabled;
    setActionLoading("maintenance");
    setMessage(null);
    try {
      const res = await api.setMaintenance(nextState, nextState ? "Manual maintenance from web panel" : "");
      setMessage({ text: res.message || `Maintenance mode ${nextState ? "enabled" : "disabled"}`, type: "ok" });
      await refreshData();
    } catch (err: any) {
      setMessage({ text: err.message || "Failed to toggle maintenance mode", type: "err" });
    } finally {
      setActionLoading(null);
    }
  };


  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#0b0f19", color: "#f8fafc", padding: "1.5rem" }}>
      {/* Header */}
      <header style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        borderBottom: "1px solid #1e293b",
        paddingBottom: "1rem",
        marginBottom: "1.5rem"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <div style={{
            backgroundColor: "#2563eb",
            borderRadius: "8px",
            padding: "0.4rem 0.6rem",
            fontWeight: "bold",
            fontSize: "1rem"
          }}>
            CL
          </div>
          <div>
            <h1 style={{ fontSize: "1.25rem", margin: 0, fontWeight: "700" }}>CraftLab Control Plane</h1>
            <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>Autonomous Supervisor & Diagnostics</span>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: "0.875rem", fontWeight: "600" }}>{user.username}</div>
            <div style={{ fontSize: "0.75rem", color: "#38bdf8" }}>
              {user.roles.join(", ")} {user.is_break_glass && "(Break-Glass)"}
            </div>
          </div>
          <button
            onClick={onLogout}
            style={{
              backgroundColor: "#1e293b",
              border: "1px solid #334155",
              color: "#cbd5e1",
              padding: "0.4rem 0.8rem",
              borderRadius: "6px",
              cursor: "pointer",
              fontSize: "0.875rem"
            }}
          >
            Sign Out
          </button>
        </div>
      </header>

      {/* Alert Banner */}
      {message && (
        <div style={{
          backgroundColor: message.type === "ok" ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)",
          border: `1px solid ${message.type === "ok" ? "#10b981" : "#ef4444"}`,
          color: message.type === "ok" ? "#a7f3d0" : "#fca5a5",
          padding: "0.75rem 1rem",
          borderRadius: "8px",
          marginBottom: "1.5rem",
          fontSize: "0.875rem"
        }}>
          {message.text}
        </div>
      )}

      {/* Grid Layout */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1.5rem" }}>
        {/* Service Lifecycle Card */}
        <div style={{
          backgroundColor: "#131b2e",
          border: "1px solid #1e293b",
          borderRadius: "10px",
          padding: "1.25rem"
        }}>
          <h2 style={{ fontSize: "1rem", fontWeight: "600", margin: "0 0 1rem 0", color: "#cbd5e1" }}>
            Application Lifecycle
          </h2>

          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
            <span style={{ fontSize: "0.875rem", color: "#94a3b8" }}>Managed Status:</span>
            <span style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.375rem",
              fontSize: "0.875rem",
              fontWeight: "600",
              color: status?.is_running ? "#4ade80" : "#f87171"
            }}>
              ● {status?.is_running ? "RUNNING" : "STOPPED"}
            </span>
          </div>

          <div style={{ fontSize: "0.8125rem", color: "#94a3b8", marginBottom: "1.25rem", lineHeight: "1.6" }}>
            <div>PID: {status?.pid || "—"}</div>
            <div>Uptime: {status?.uptime_seconds ? `${Math.round(status.uptime_seconds)}s` : "—"}</div>
            <div>Memory RSS: {status?.memory_mb ? `${status.memory_mb} MB` : "—"}</div>
          </div>

          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <button
              disabled={!isAdminOrOperator || actionLoading !== null || status?.is_running}
              onClick={() => handleAction("start")}
              style={{
                flex: "1",
                padding: "0.5rem",
                backgroundColor: status?.is_running ? "#1e293b" : "#16a34a",
                border: "none",
                borderRadius: "6px",
                color: "white",
                fontWeight: "600",
                fontSize: "0.8125rem",
                cursor: status?.is_running ? "not-allowed" : "pointer"
              }}
            >
              Start
            </button>
            <button
              disabled={!isAdminOrOperator || actionLoading !== null || !status?.is_running}
              onClick={() => handleAction("restart")}
              style={{
                flex: "1",
                padding: "0.5rem",
                backgroundColor: !status?.is_running ? "#1e293b" : "#2563eb",
                border: "none",
                borderRadius: "6px",
                color: "white",
                fontWeight: "600",
                fontSize: "0.8125rem",
                cursor: !status?.is_running ? "not-allowed" : "pointer"
              }}
            >
              Restart
            </button>
            <button
              disabled={!isAdminOrOperator || actionLoading !== null || !status?.is_running}
              onClick={() => handleAction("stop")}
              style={{
                flex: "1",
                padding: "0.5rem",
                backgroundColor: !status?.is_running ? "#1e293b" : "#dc2626",
                border: "none",
                borderRadius: "6px",
                color: "white",
                fontWeight: "600",
                fontSize: "0.8125rem",
                cursor: !status?.is_running ? "not-allowed" : "pointer"
              }}
            >
              Stop
            </button>
          </div>
        </div>

        {/* Telemetry Metrics Card */}
        <div style={{
          backgroundColor: "#131b2e",
          border: "1px solid #1e293b",
          borderRadius: "10px",
          padding: "1.25rem"
        }}>
          <h2 style={{ fontSize: "1rem", fontWeight: "600", margin: "0 0 1rem 0", color: "#cbd5e1" }}>
            System Telemetry (psutil)
          </h2>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <div style={{ backgroundColor: "#0f172a", padding: "0.75rem", borderRadius: "8px" }}>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>Host CPU</div>
              <div style={{ fontSize: "1.25rem", fontWeight: "700", color: "#38bdf8" }}>
                {metrics?.host.cpu_percent !== undefined ? `${metrics.host.cpu_percent}%` : "—"}
              </div>
            </div>

            <div style={{ backgroundColor: "#0f172a", padding: "0.75rem", borderRadius: "8px" }}>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>Host RAM</div>
              <div style={{ fontSize: "1.25rem", fontWeight: "700", color: "#818cf8" }}>
                {metrics?.host.memory.percent !== undefined ? `${metrics.host.memory.percent}%` : "—"}
              </div>
              <div style={{ fontSize: "0.6875rem", color: "#64748b" }}>
                {metrics?.host.memory.used_mb} MB / {metrics?.host.memory.total_mb} MB
              </div>
            </div>

            <div style={{ backgroundColor: "#0f172a", padding: "0.75rem", borderRadius: "8px" }}>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>Disk Usage</div>
              <div style={{ fontSize: "1.25rem", fontWeight: "700", color: "#facc15" }}>
                {metrics?.host.disk.percent !== undefined ? `${metrics.host.disk.percent}%` : "—"}
              </div>
              <div style={{ fontSize: "0.6875rem", color: "#64748b" }}>
                {metrics?.host.disk.free_gb} GB free
              </div>
            </div>

            <div style={{ backgroundColor: "#0f172a", padding: "0.75rem", borderRadius: "8px" }}>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>Process Threads</div>
              <div style={{ fontSize: "1.25rem", fontWeight: "700", color: "#4ade80" }}>
                {metrics?.process.threads !== undefined ? metrics.process.threads : "—"}
              </div>
            </div>
          </div>
        </div>

        {/* Doctor Diagnostics Card */}
        <div style={{
          backgroundColor: "#131b2e",
          border: "1px solid #1e293b",
          borderRadius: "10px",
          padding: "1.25rem"
        }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
            <h2 style={{ fontSize: "1rem", fontWeight: "600", margin: 0, color: "#cbd5e1" }}>
              Environmental Doctor
            </h2>
            <button
              onClick={handleRunDoctor}
              disabled={actionLoading !== null}
              style={{
                backgroundColor: "#334155",
                border: "none",
                borderRadius: "6px",
                color: "#f8fafc",
                padding: "0.3rem 0.6rem",
                fontSize: "0.75rem",
                cursor: "pointer"
              }}
            >
              {actionLoading === "doctor" ? "Testing..." : "Run Checks"}
            </button>
          </div>

          {doctor ? (
            <div>
              <div style={{ fontSize: "0.8125rem", marginBottom: "0.5rem", fontWeight: "600" }}>
                Overall: <span style={{ color: doctor.overall === "PASS" ? "#4ade80" : doctor.overall === "WARN" ? "#facc15" : "#f87171" }}>{doctor.overall}</span>
              </div>
              <div style={{ maxHeight: "150px", overflowY: "auto", fontSize: "0.75rem" }}>
                {doctor.checks.map((chk, i) => (
                  <div key={i} style={{ padding: "0.25rem 0", borderBottom: "1px solid #1e293b", display: "flex", gap: "0.5rem" }}>
                    <span style={{ fontWeight: "bold", color: chk.status === "PASS" ? "#4ade80" : chk.status === "WARN" ? "#facc15" : "#f87171" }}>
                      [{chk.status}]
                    </span>
                    <span style={{ color: "#cbd5e1" }}>{chk.check_id}: {chk.message}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div style={{ fontSize: "0.8125rem", color: "#64748b" }}>
              Click "Run Checks" to execute environment and database health checks.
            </div>
          )}
        </div>

        {/* Releases & Application Updates Card */}
        <div style={{
          backgroundColor: "#131b2e",
          border: "1px solid #1e293b",
          borderRadius: "10px",
          padding: "1.25rem"
        }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
            <h2 style={{ fontSize: "1rem", fontWeight: "600", margin: 0, color: "#cbd5e1" }}>
              Releases & Updates
            </h2>
            <button
              onClick={handleCheckUpdates}
              disabled={actionLoading !== null}
              style={{
                backgroundColor: "#2563eb",
                border: "none",
                borderRadius: "6px",
                color: "white",
                padding: "0.3rem 0.6rem",
                fontSize: "0.75rem",
                fontWeight: "600",
                cursor: "pointer"
              }}
            >
              {actionLoading === "check_updates" ? "Checking..." : "Check Updates"}
            </button>
          </div>

          {/* Active pointer & Maintenance status */}
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", marginBottom: "1rem", fontSize: "0.8125rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ color: "#94a3b8" }}>Active Release:</span>
              <span style={{
                backgroundColor: releasesInfo?.active_release ? "#1e3a5f" : "#1e293b",
                color: releasesInfo?.active_release ? "#38bdf8" : "#94a3b8",
                padding: "0.2rem 0.5rem",
                borderRadius: "4px",
                fontWeight: "bold"
              }}>
                {releasesInfo?.active_release || "dev (workspace)"}
              </span>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ color: "#94a3b8" }}>Maintenance Mode:</span>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <span style={{
                  color: releasesInfo?.maintenance?.enabled ? "#f87171" : "#4ade80",
                  fontWeight: "600"
                }}>
                  ● {releasesInfo?.maintenance?.enabled ? "ACTIVE" : "OFF"}
                </span>
                {isAdminOrOperator && (
                  <button
                    onClick={handleToggleMaintenance}
                    disabled={actionLoading !== null}
                    style={{
                      backgroundColor: "#334155",
                      border: "none",
                      borderRadius: "4px",
                      color: "#cbd5e1",
                      fontSize: "0.6875rem",
                      padding: "0.15rem 0.4rem",
                      cursor: "pointer"
                    }}
                  >
                    {releasesInfo?.maintenance?.enabled ? "Disable" : "Enable"}
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* GitHub Update Check Result */}
          {updateCheck && (
            <div style={{
              backgroundColor: updateCheck.update_available ? "rgba(37, 99, 235, 0.15)" : "#0f172a",
              border: `1px solid ${updateCheck.update_available ? "#3b82f6" : "#1e293b"}`,
              borderRadius: "6px",
              padding: "0.6rem 0.75rem",
              marginBottom: "1rem",
              fontSize: "0.75rem"
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.25rem" }}>
                <span style={{ color: "#94a3b8" }}>Latest on GitHub:</span>
                <span style={{ fontWeight: "bold", color: "#38bdf8" }}>{updateCheck.latest_version || "None"}</span>
              </div>
              {updateCheck.update_available ? (
                <div style={{ marginTop: "0.5rem", display: "flex", gap: "0.5rem" }}>
                  <button
                    disabled={!isAdminOrOperator || actionLoading !== null}
                    onClick={() => handlePrepareUpdate(updateCheck.latest_version!)}
                    style={{
                      flex: 1,
                      backgroundColor: "#334155",
                      border: "none",
                      borderRadius: "4px",
                      color: "white",
                      padding: "0.35rem",
                      fontSize: "0.75rem",
                      cursor: "pointer"
                    }}
                  >
                    {actionLoading === "prepare_update" ? "Staging..." : "1. Prepare"}
                  </button>
                  <button
                    disabled={!isAdminOrOperator || actionLoading !== null}
                    onClick={() => handleApplyUpdate(updateCheck.latest_version!)}
                    style={{
                      flex: 1,
                      backgroundColor: "#16a34a",
                      border: "none",
                      borderRadius: "4px",
                      color: "white",
                      fontWeight: "600",
                      padding: "0.35rem",
                      fontSize: "0.75rem",
                      cursor: "pointer"
                    }}
                  >
                    {actionLoading === "apply_update" ? "Applying..." : "2. Apply Update"}
                  </button>
                </div>
              ) : (
                <div style={{ color: "#4ade80", fontSize: "0.6875rem", marginTop: "0.25rem" }}>
                  System is running the latest available version.
                </div>
              )}
            </div>
          )}

          {/* Installed Releases List */}
          <div style={{ marginBottom: "1rem" }}>
            <span style={{ fontSize: "0.75rem", color: "#94a3b8", display: "block", marginBottom: "0.35rem" }}>
              Installed Releases ({releasesInfo?.installed_releases?.length || 0}):
            </span>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem" }}>
              {releasesInfo?.installed_releases && releasesInfo.installed_releases.length > 0 ? (
                releasesInfo.installed_releases.map((rel) => {
                  const isActive = rel === releasesInfo.active_release || `v${rel}` === releasesInfo.active_release || rel === `v${releasesInfo.active_release}`;
                  return (
                    <span
                      key={rel}
                      style={{
                        fontSize: "0.6875rem",
                        padding: "0.2rem 0.4rem",
                        borderRadius: "4px",
                        backgroundColor: isActive ? "#166534" : "#1e293b",
                        color: isActive ? "#bbf7d0" : "#94a3b8",
                        fontWeight: isActive ? "bold" : "normal"
                      }}
                    >
                      {rel} {isActive && "★"}
                    </span>
                  );
                })
              ) : (
                <span style={{ fontSize: "0.6875rem", color: "#64748b", fontStyle: "italic" }}>
                  No standalone releases installed yet.
                </span>
              )}
            </div>
          </div>

          {/* Manual Version Actions */}
          {isAdminOrOperator && (
            <div style={{ borderTop: "1px solid #1e293b", paddingTop: "0.75rem", fontSize: "0.75rem" }}>
              <div style={{ display: "flex", gap: "0.4rem", marginBottom: "0.5rem" }}>
                <input
                  type="text"
                  placeholder="Target version (e.g. 0.2.0)"
                  value={targetVersion}
                  onChange={(e) => setTargetVersion(e.target.value)}
                  style={{
                    flex: 1,
                    backgroundColor: "#0f172a",
                    border: "1px solid #334155",
                    borderRadius: "4px",
                    color: "white",
                    padding: "0.3rem 0.5rem",
                    fontSize: "0.75rem"
                  }}
                />
                <button
                  disabled={!targetVersion || actionLoading !== null}
                  onClick={() => handlePrepareUpdate(targetVersion)}
                  style={{
                    backgroundColor: "#334155",
                    border: "none",
                    borderRadius: "4px",
                    color: "white",
                    padding: "0.3rem 0.5rem",
                    cursor: targetVersion ? "pointer" : "not-allowed"
                  }}
                >
                  Prepare
                </button>
                <button
                  disabled={!targetVersion || actionLoading !== null}
                  onClick={() => handleApplyUpdate(targetVersion)}
                  style={{
                    backgroundColor: "#2563eb",
                    border: "none",
                    borderRadius: "4px",
                    color: "white",
                    fontWeight: "600",
                    padding: "0.3rem 0.5rem",
                    cursor: targetVersion ? "pointer" : "not-allowed"
                  }}
                >
                  Apply
                </button>
              </div>

              {/* Rollback Control */}
              {releasesInfo && releasesInfo.installed_releases && releasesInfo.installed_releases.length > 1 && (
                <div style={{ display: "flex", gap: "0.4rem", alignItems: "center", marginTop: "0.5rem" }}>
                  <select
                    value={selectedRollback}
                    onChange={(e) => setSelectedRollback(e.target.value)}
                    style={{
                      flex: 1,
                      backgroundColor: "#0f172a",
                      border: "1px solid #334155",
                      borderRadius: "4px",
                      color: "white",
                      padding: "0.3rem 0.5rem",
                      fontSize: "0.75rem"
                    }}
                  >
                    <option value="">Select prior release to rollback...</option>
                    {releasesInfo.installed_releases
                      .filter((r) => r !== releasesInfo.active_release && `v${r}` !== releasesInfo.active_release)
                      .map((r) => (
                        <option key={r} value={r}>{r}</option>
                      ))}
                  </select>
                  <button
                    disabled={actionLoading !== null}
                    onClick={() => handleRollback(selectedRollback || undefined)}
                    style={{
                      backgroundColor: "#dc2626",
                      border: "none",
                      borderRadius: "4px",
                      color: "white",
                      fontWeight: "600",
                      padding: "0.3rem 0.6rem",
                      cursor: "pointer"
                    }}
                  >
                    Rollback
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Real-time Console Log Streamer */}
      <div style={{
        marginTop: "1.5rem",
        backgroundColor: "#080c14",
        border: "1px solid #1e293b",
        borderRadius: "10px",
        overflow: "hidden"
      }}>
        <div style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.75rem 1rem",
          backgroundColor: "#101626",
          borderBottom: "1px solid #1e293b"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span style={{ fontSize: "0.875rem", fontWeight: "600", color: "#cbd5e1" }}>Live Log Stream</span>
            <span style={{ fontSize: "0.75rem", color: "#64748b" }}>({logs.length} lines)</span>
          </div>

          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button
              onClick={() => setAutoScroll(!autoScroll)}
              style={{
                backgroundColor: autoScroll ? "#2563eb" : "#334155",
                color: "white",
                border: "none",
                borderRadius: "4px",
                fontSize: "0.75rem",
                padding: "0.25rem 0.5rem",
                cursor: "pointer"
              }}
            >
              Autoscroll: {autoScroll ? "ON" : "OFF"}
            </button>
            <button
              onClick={() => setLogs([])}
              style={{
                backgroundColor: "#334155",
                color: "#cbd5e1",
                border: "none",
                borderRadius: "4px",
                fontSize: "0.75rem",
                padding: "0.25rem 0.5rem",
                cursor: "pointer"
              }}
            >
              Clear
            </button>
          </div>
        </div>

        <div style={{
          padding: "1rem",
          height: "300px",
          overflowY: "auto",
          fontFamily: "monospace",
          fontSize: "0.8125rem",
          lineHeight: "1.5",
          color: "#94a3b8"
        }}>
          {logs.length === 0 ? (
            <div style={{ color: "#475569", fontStyle: "italic" }}>No log output received yet...</div>
          ) : (
            logs.map((line, idx) => (
              <div key={idx} style={{ whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
                {line}
              </div>
            ))
          )}
          <div ref={logsEndRef} />
        </div>
      </div>
    </div>
  );
};
