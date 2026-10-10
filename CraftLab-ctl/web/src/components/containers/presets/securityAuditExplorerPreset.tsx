import React from "react";
import { PaginatedContainerPreset } from "../../../types/presets";

export const securityAuditExplorerPreset: PaginatedContainerPreset = {
  id: "security-audit-explorer",
  title: "Forensic Audit Explorer",
  iconName: "database",
  category: "security",
  defaultSpan: { cols: 3, rows: 2, minCols: 2, maxCols: 4 },
  paginationMode: "records",
  collection: {
    pageSize: 4,
    emptyMessage: "No security audit events recorded in SQLite storage.",
    getItems: (data) => data.security?.events || [],
    renderItem: (evt: any, index: number) => {
      const severityColor =
        evt.severity === "critical"
          ? "bg-rose-500/20 text-rose-400 border-rose-500/40"
          : evt.severity === "high"
          ? "bg-amber-500/20 text-amber-400 border-amber-500/40"
          : evt.severity === "medium"
          ? "bg-blue-500/20 text-blue-400 border-blue-500/40"
          : "bg-slate-700/40 text-slate-400 border-slate-600/30";

      const outcomeColor =
        evt.outcome === "success"
          ? "text-emerald-400"
          : evt.outcome === "denied"
          ? "text-amber-400"
          : "text-rose-400";

      const timeFormatted = evt.occurred_at
        ? new Date(evt.occurred_at).toLocaleTimeString()
        : "--:--:--";

      return (
        <div
          key={evt.event_id || index}
          className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-xs flex flex-col gap-1.5"
        >
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="font-mono text-slate-400 text-[11px]">{timeFormatted}</span>
              <span
                className={`text-[9px] font-mono uppercase px-1.5 py-0.5 rounded border ${severityColor}`}
              >
                {evt.severity}
              </span>
              <span className="font-mono font-semibold text-slate-200">
                {evt.event_type}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-[10px] font-mono uppercase font-bold ${outcomeColor}`}>
                {evt.outcome}
              </span>
              <span className="text-[10px] text-slate-500 font-sans">
                #{evt.component || "system"}
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400 pt-1 border-t border-slate-900">
            <div>
              <span className="text-slate-500">Actor:</span>{" "}
              <span className="font-mono text-slate-300">
                {evt.actor_id || evt.actor_type || "anonymous"}
              </span>
              {evt.source_ip && (
                <>
                  <span className="text-slate-600 mx-1.5">•</span>
                  <span className="text-slate-500">Source:</span>{" "}
                  <span className="font-mono text-slate-300">{evt.source_ip}</span>
                </>
              )}
            </div>

            {evt.reason_code && (
              <div className="text-[10px] font-mono text-rose-300">
                Reason: {evt.reason_code}
              </div>
            )}
            {evt.route && (
              <div className="text-[10px] font-mono text-slate-500">
                Route: {evt.route}
              </div>
            )}
          </div>
        </div>
      );
    },
    footerInputs: [
      {
        type: "button",
        id: "btn-refresh-audit",
        label: "Refresh Audit Feed",
        actionId: "security.refresh",
        variant: "secondary",
      },
      {
        type: "button",
        id: "btn-purge-retention",
        label: "Purge Retained Logs (>30 Days)",
        actionId: "security.purge_logs",
        variant: "warning",
        confirmMessage:
          "Permanently delete security audit events older than 30 days from SQLite storage?",
        requiredRoles: ["admin"],
      },
    ],
  },
};
