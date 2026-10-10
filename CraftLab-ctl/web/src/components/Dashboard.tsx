import React, { useState, useEffect, useRef } from "react";
import {
  api,
  UserContext,
  ServiceStatus,
  SystemMetrics,
  DoctorResult,
  ReleasesInfo,
  UpdateCheckResult,
  SecurityPosture,
  SecurityAnomaly,
  SecurityQuarantineEntry,
  SecurityEventRecord,
} from "../api";
import { ContainerActionDispatcher } from "../types/presets";
import { CategoryTabBar } from "./navigation/CategoryTabBar";
import { DraggableGrid } from "./containers/DraggableGrid";
import {
  allSupervisorPresets,
  SUPERVISOR_CATEGORIES,
} from "./containers/presets";

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
  const [securityPosture, setSecurityPosture] = useState<SecurityPosture | null>(null);
  const [securityAnomalies, setSecurityAnomalies] = useState<SecurityAnomaly[]>([]);
  const [quarantines, setQuarantines] = useState<SecurityQuarantineEntry[]>([]);
  const [auditEvents, setAuditEvents] = useState<SecurityEventRecord[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [message, setMessage] = useState<{ text: string; type: "ok" | "err" } | null>(null);

  // Active Category State
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [resetTrigger, setResetTrigger] = useState<number>(0);

  const wsRef = useRef<WebSocket | null>(null);

  // Periodic Telemetry and Data Polling
  const refreshData = async () => {
    try {
      const [s, m, r, p, a, q, evts] = await Promise.all([
        api.getStatus(),
        api.getMetrics(),
        api.getReleases().catch(() => null),
        api.getSecurityPosture().catch(() => null),
        api.getSecurityAnomalies().catch(() => []),
        api.getSecurityQuarantines().catch(() => []),
        api.getSecurityEvents({ limit: 50 }).catch(() => ({ events: [] })),
      ]);
      setStatus(s);
      setMetrics(m);
      if (r) setReleasesInfo(r);
      if (p) setSecurityPosture(p);
      setSecurityAnomalies(a || []);
      setQuarantines(q || []);
      if (evts?.events) setAuditEvents(evts.events);
    } catch (err: any) {
      console.error("Failed to refresh status/metrics/security:", err);
    }
  };

  useEffect(() => {
    refreshData();
    const interval = setInterval(refreshData, 3000);
    return () => clearInterval(interval);
  }, []);

  // WebSocket for Real-time Log Streaming
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

  // Supervisor Action Handlers
  const handleLifecycleAction = async (action: string) => {
    setActionLoading(action);
    setMessage(null);
    try {
      const res = await api.executeLifecycle(action);
      setMessage({ text: res.message || `Action ${action} executed successfully`, type: "ok" });
      await refreshData();
    } catch (err: any) {
      setMessage({ text: err.message || `Failed to execute action ${action}`, type: "err" });
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
      setMessage({
        text: `Doctor completed: ${doc.overall}`,
        type: doc.overall === "FAIL" ? "err" : "ok",
      });
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
          ? `New version ${res.latest_version} available!`
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
    setActionLoading("apply_version");
    setMessage(null);
    try {
      const res = await api.prepareUpdate(ver);
      if (res.success) {
        setMessage({ text: res.message || `Release ${ver} prepared successfully`, type: "ok" });
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
    if (!window.confirm(`Applying release ${ver} will restart the CraftLab backend service. Proceed?`)) {
      return;
    }
    setActionLoading("apply_version");
    setMessage(null);
    try {
      // First ensure prepared then apply
      await api.prepareUpdate(ver);
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
    const targetDesc = ver || "previous version";
    if (!window.confirm(`Roll back to ${targetDesc}? This will restart the supervised service.`)) {
      return;
    }
    setActionLoading("rollback_release");
    setMessage(null);
    try {
      const res = await api.rollbackUpdate(ver);
      if (res.success) {
        setMessage({ text: res.message || `Rollback to ${targetDesc} completed!`, type: "ok" });
        await refreshData();
      } else {
        setMessage({ text: res.error || "Rollback failed", type: "err" });
      }
    } catch (err: any) {
      setMessage({ text: err.message || "Failed to execute rollback", type: "err" });
    } finally {
      setActionLoading(null);
    }
  };

  const handleToggleMaintenance = async () => {
    if (!releasesInfo) return;
    const nextState = !releasesInfo.maintenance.enabled;
    setActionLoading("toggle_maintenance");
    setMessage(null);
    try {
      const res = await api.setMaintenance(
        nextState,
        nextState ? "Maintenance enabled from modular panel" : ""
      );
      setMessage({
        text: res.message || `Maintenance mode ${nextState ? "enabled" : "disabled"}`,
        type: "ok",
      });
      await refreshData();
    } catch (err: any) {
      setMessage({ text: err.message || "Failed to toggle maintenance mode", type: "err" });
    } finally {
      setActionLoading(null);
    }
  };

  // Centralized Action Dispatcher
  const actionDispatcher: ContainerActionDispatcher = {
    user,
    isLoading: (id) => (id ? actionLoading === id : !!actionLoading),
    message,
    dispatch: async (actionId, payload) => {
      switch (actionId) {
        case "start":
        case "restart":
        case "stop":
          return handleLifecycleAction(actionId);
        case "doctor":
          return handleRunDoctor();
        case "check_updates":
          return handleCheckUpdates();
        case "prepare_release":
          return handlePrepareUpdate(payload);
        case "apply_version":
          return handleApplyUpdate(payload);
        case "rollback_release":
          return handleRollback(payload);
        case "toggle_maintenance":
          return handleToggleMaintenance();
        case "security.refresh":
          await refreshData();
          setMessage({ text: "Security telemetry and posture refreshed", type: "ok" });
          return;
        case "security.quarantine_ip":
        case "security.manual_quarantine": {
          const ip = typeof payload === "string" ? payload : payload?.ip;
          if (!ip) return;
          setActionLoading("quarantine");
          try {
            const res = await api.quarantineIp(ip, payload?.duration_minutes || 60, payload?.reason || "Quarantined by operator");
            setMessage({ text: res.message || `IP ${ip} quarantined`, type: "ok" });
            await refreshData();
          } catch (err: any) {
            setMessage({ text: err.message || "Failed to quarantine IP", type: "err" });
          } finally {
            setActionLoading(null);
          }
          return;
        }
        case "security.unquarantine_ip": {
          const ip = typeof payload === "string" ? payload : payload?.ip;
          if (!ip) return;
          setActionLoading("unquarantine");
          try {
            const res = await api.unquarantineIp(ip);
            setMessage({ text: res.message || `IP ${ip} unquarantined`, type: "ok" });
            await refreshData();
          } catch (err: any) {
            setMessage({ text: err.message || "Failed to unquarantine IP", type: "err" });
          } finally {
            setActionLoading(null);
          }
          return;
        }
        case "security.revoke_sessions": {
          setActionLoading("revoke_sessions");
          try {
            const res = await api.revokeSessions();
            setMessage({ text: res.message || "Active sessions revoked", type: "ok" });
            await refreshData();
          } catch (err: any) {
            setMessage({ text: err.message || "Failed to revoke sessions", type: "err" });
          } finally {
            setActionLoading(null);
          }
          return;
        }
        case "security.revoke_user_sessions": {
          const username = typeof payload === "string" ? payload : payload?.username;
          if (!username) return;
          setActionLoading("revoke_user_sessions");
          try {
            const res = await api.revokeSessions(username);
            setMessage({ text: res.message || `Revoked sessions for user ${username}`, type: "ok" });
            await refreshData();
          } catch (err: any) {
            setMessage({ text: err.message || "Failed to revoke user sessions", type: "err" });
          } finally {
            setActionLoading(null);
          }
          return;
        }
        case "security.toggle_lockdown": {
          setActionLoading("toggle_lockdown");
          const next = !securityPosture?.lockdown_enabled;
          try {
            const res = await api.toggleLockdown(next, next ? "Emergency lockdown enabled" : "");
            setMessage({ text: res.message || `Emergency lockdown ${next ? "enabled" : "disabled"}`, type: "ok" });
            await refreshData();
          } catch (err: any) {
            setMessage({ text: err.message || "Failed to toggle lockdown", type: "err" });
          } finally {
            setActionLoading(null);
          }
          return;
        }
        case "security.dismiss_anomaly": {
          const alertId = typeof payload === "string" ? payload : payload?.alert_id;
          if (!alertId) return;
          try {
            await api.dismissSecurityAnomaly(alertId);
            setMessage({ text: `Alert ${alertId} dismissed`, type: "ok" });
            await refreshData();
          } catch (err: any) {
            setMessage({ text: err.message || "Failed to dismiss alert", type: "err" });
          }
          return;
        }
        case "security.purge_logs": {
          setActionLoading("purge_logs");
          try {
            const res = await api.purgeSecurityLogs(payload || 30);
            setMessage({ text: res.message || "Security audit logs purged", type: "ok" });
            await refreshData();
          } catch (err: any) {
            setMessage({ text: err.message || "Failed to purge audit logs", type: "err" });
          } finally {
            setActionLoading(null);
          }
          return;
        }
        default:
          console.warn("Unrecognized action:", actionId, payload);
      }
    },
  };

  // Aggregated Context Data for Container Presets
  const containerContextData = {
    status,
    metrics,
    doctor,
    releasesInfo,
    updateCheck,
    security: {
      posture: securityPosture,
      anomalies: securityAnomalies,
      quarantines: quarantines,
      events: auditEvents,
    },
  };

  // Filter Presets by Active Category
  const activePresets =
    activeCategory === "all"
      ? allSupervisorPresets
      : allSupervisorPresets.filter((p) => p.category === activeCategory);

  // Category counts
  const categoryCounts: Record<string, number> = {
    all: allSupervisorPresets.length,
    system: allSupervisorPresets.filter((p) => p.category === "system").length,
    lifecycle: allSupervisorPresets.filter((p) => p.category === "lifecycle").length,
    releases: allSupervisorPresets.filter((p) => p.category === "releases").length,
    doctor: allSupervisorPresets.filter((p) => p.category === "doctor").length,
    logs: allSupervisorPresets.filter((p) => p.category === "logs").length,
  };

  const handleResetLayout = () => {
    const key = `craftlab_ctl_layout_v1:${activeCategory}`;
    try {
      localStorage.removeItem(key);
    } catch (e) {
      console.warn("Failed to clear layout from localStorage:", e);
    }
    setResetTrigger((prev) => prev + 1);
    setMessage({
      text: `Category layout restored to default dimensions`,
      type: "ok",
    });
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 p-4 md:p-6">
      {/* Top Header */}
      <header className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800 mb-6">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 rounded-xl px-3 py-1.5 font-bold text-base text-white shadow-md shadow-blue-500/20">
            CL
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white m-0">
              CraftLab Control Plane
            </h1>
            <span className="text-xs text-slate-400 font-medium">
              Autonomous Supervisor & Diagnostics
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-xs font-semibold text-slate-200">{user.username}</div>
            <div className="text-[11px] text-cyan-400 font-mono">
              {user.roles.join(", ")} {user.is_break_glass && "(Break-Glass)"}
            </div>
          </div>
          <button
            type="button"
            onClick={onLogout}
            className="bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 hover:text-white px-3 py-1.5 rounded-xl text-xs font-medium transition-colors cursor-pointer"
          >
            Sign Out
          </button>
        </div>
      </header>

      {/* Global Status Message Toast if present */}
      {message && (
        <div
          className={`mb-6 p-3 rounded-xl border text-xs font-medium flex items-center justify-between shadow-lg ${
            message.type === "ok"
              ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-300"
              : "bg-rose-950/40 border-rose-500/40 text-rose-300"
          }`}
        >
          <div className="flex items-center gap-2">
            <span>{message.type === "ok" ? "✔" : "✖"}</span>
            <span>{message.text}</span>
          </div>
          <button
            type="button"
            onClick={() => setMessage(null)}
            className="text-slate-400 hover:text-slate-200 text-xs px-2 cursor-pointer font-bold"
          >
            ✕
          </button>
        </div>
      )}

      {/* Horizontal Categorized Navigation Tabs */}
      <CategoryTabBar
        categories={SUPERVISOR_CATEGORIES}
        activeCategoryId={activeCategory}
        onSelectCategory={setActiveCategory}
        categoryCounts={categoryCounts}
        onResetLayout={handleResetLayout}
      />

      {/* Modular Draggable & Resizable Grid of Paginated Data Containers */}
      <main>
        <DraggableGrid
          category={activeCategory}
          presets={activePresets}
          data={containerContextData}
          actions={actionDispatcher}
          logs={logs}
          onClearLogs={() => setLogs([])}
          resetTrigger={resetTrigger}
        />
      </main>
    </div>
  );
};
