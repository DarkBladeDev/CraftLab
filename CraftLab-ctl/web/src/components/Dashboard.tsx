import React, { useState, useEffect, useRef } from "react";
import { api, UserContext, ServiceStatus, SystemMetrics, DoctorResult } from "../api";

interface DashboardProps {
  user: UserContext;
  onLogout: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ user, onLogout }) => {
  const [status, setStatus] = useState<ServiceStatus | null>(null);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [doctor, setDoctor] = useState<DoctorResult | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [message, setMessage] = useState<{ text: string; type: "ok" | "err" } | null>(null);

  const logsEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const isAdminOrOperator = user.is_break_glass || user.roles.includes("admin") || user.roles.includes("operator");

  // Fetch status & metrics
  const refreshData = async () => {
    try {
      const [s, m] = await Promise.all([api.getStatus(), api.getMetrics()]);
      setStatus(s);
      setMetrics(m);
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
