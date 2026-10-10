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
      setMessage({ text: res.message || `Acción ${action} ejecutada con éxito`, type: "ok" });
      await refreshData();
    } catch (err: any) {
      setMessage({ text: err.message || `Error al ejecutar acción ${action}`, type: "err" });
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
        text: `Doctor completado: ${doc.overall}`,
        type: doc.overall === "FAIL" ? "err" : "ok",
      });
    } catch (err: any) {
      setMessage({ text: err.message || "Error al ejecutar el doctor", type: "err" });
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
          ? `Nueva versión ${res.latest_version} disponible!`
          : `CraftLab está actualizado (${res.current_version})`,
        type: "ok",
      });
    } catch (err: any) {
      setMessage({ text: err.message || "Error al consultar actualizaciones", type: "err" });
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
        setMessage({ text: res.message || `Release ${ver} preparada correctamente`, type: "ok" });
        await refreshData();
      } else {
        setMessage({ text: res.error || `Error al preparar release ${ver}`, type: "err" });
      }
    } catch (err: any) {
      setMessage({ text: err.message || `Error al preparar release ${ver}`, type: "err" });
    } finally {
      setActionLoading(null);
    }
  };

  const handleApplyUpdate = async (ver: string) => {
    if (!ver) return;
    if (!window.confirm(`Aplicar la release ${ver} reiniciará el servicio backend de CraftLab. ¿Continuar?`)) {
      return;
    }
    setActionLoading("apply_version");
    setMessage(null);
    try {
      // First ensure prepared then apply
      await api.prepareUpdate(ver);
      const res = await api.applyUpdate(ver);
      if (res.success) {
        setMessage({ text: res.message || `Release ${ver} aplicada exitosamente!`, type: "ok" });
        await refreshData();
      } else {
        setMessage({ text: res.error || `Error al aplicar release ${ver}`, type: "err" });
      }
    } catch (err: any) {
      setMessage({ text: err.message || `Error al aplicar release ${ver}`, type: "err" });
    } finally {
      setActionLoading(null);
    }
  };

  const handleRollback = async (ver?: string) => {
    const targetDesc = ver || "versión anterior";
    if (!window.confirm(`¿Revertir a ${targetDesc}? Esto reiniciará el servicio supervisado.`)) {
      return;
    }
    setActionLoading("rollback_release");
    setMessage(null);
    try {
      const res = await api.rollbackUpdate(ver);
      if (res.success) {
        setMessage({ text: res.message || `Reversión a ${targetDesc} completada!`, type: "ok" });
        await refreshData();
      } else {
        setMessage({ text: res.error || "Fallo en el rollback", type: "err" });
      }
    } catch (err: any) {
      setMessage({ text: err.message || "Fallo al ejecutar rollback", type: "err" });
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
        nextState ? "Mantenimiento activado desde panel modular" : ""
      );
      setMessage({
        text: res.message || `Modo mantenimiento ${nextState ? "activado" : "desactivado"}`,
        type: "ok",
      });
      await refreshData();
    } catch (err: any) {
      setMessage({ text: err.message || "Error al alternar modo mantenimiento", type: "err" });
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
        default:
          console.warn("Acción no reconocida:", actionId, payload);
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
      text: `Diseño de la categoría restaurado a los valores por defecto`,
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
