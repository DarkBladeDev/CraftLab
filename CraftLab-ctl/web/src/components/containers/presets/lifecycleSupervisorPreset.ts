import { PaginatedContainerPreset } from "../../../types/presets";

export const lifecycleSupervisorPreset: PaginatedContainerPreset = {
  id: "lifecycle-supervisor",
  title: "Application Lifecycle",
  category: "lifecycle",
  defaultSpan: { cols: 1, rows: 1, minCols: 1, maxCols: 2 },
  paginationMode: "subviews",
  pages: [
    {
      pageId: "status-controls",
      title: "State & Direct Operations",
      badge: (data) => (data.status?.status ? data.status.status.toUpperCase() : "UNKNOWN"),
      badgeColor: "green",
      outputs: [
        {
          type: "status_pill",
          label: "Managed Status:",
          status: (data) => data.status?.status ?? "unknown",
          text: (data) => (data.status?.status ? data.status.status.toUpperCase() : "UNKNOWN"),
        },
        {
          type: "key_value",
          label: "PID",
          value: (data) => (data.status?.pid ? `${data.status.pid}` : "--"),
          mono: true,
        },
        {
          type: "key_value",
          label: "Uptime",
          value: (data) => (data.status?.uptime_seconds ? `${data.status.uptime_seconds}s` : "--"),
          mono: true,
        },
        {
          type: "key_value",
          label: "Memory RSS",
          value: (data) => (data.status?.memory_rss_mb ? `${data.status.memory_rss_mb} MB` : "--"),
          mono: true,
        },
      ],
      inputs: [
        {
          type: "button",
          id: "btn-start",
          label: "Start",
          actionId: "start",
          variant: "primary",
          requiredRoles: ["admin", "operator"],
          disabledIf: (data) => data.status?.status === "running",
        },
        {
          type: "button",
          id: "btn-restart",
          label: "Restart",
          actionId: "restart",
          variant: "warning",
          requiredRoles: ["admin", "operator"],
        },
        {
          type: "button",
          id: "btn-stop",
          label: "Stop",
          actionId: "stop",
          variant: "danger",
          requiredRoles: ["admin", "operator"],
          disabledIf: (data) => data.status?.status === "stopped",
          confirmMessage: "¿Estás seguro de detener el proceso supervisado de CraftLab?",
        },
      ],
    },
    {
      pageId: "advanced-ops",
      title: "Supervisor Diagnostics Trigger",
      badge: "Diagnostics",
      badgeColor: "blue",
      description: "Ejecutar pruebas diagnósticas rápidas o recargar parámetros.",
      inputs: [
        {
          type: "button",
          id: "btn-run-doctor",
          label: "Run Doctor Health Checks",
          actionId: "doctor",
          variant: "primary",
        },
      ],
    },
  ],
};
