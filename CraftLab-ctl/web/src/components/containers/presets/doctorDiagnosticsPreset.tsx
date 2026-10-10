import React from "react";
import { PaginatedContainerPreset } from "../../../types/presets";

export const doctorDiagnosticsPreset: PaginatedContainerPreset = {
  id: "doctor-diagnostics",
  title: "Environmental Doctor",
  category: "doctor",
  defaultSpan: { cols: 1, rows: 1, minCols: 1, maxCols: 2 },
  paginationMode: "subviews",
  pages: [
    {
      pageId: "doctor-summary",
      title: "Health Diagnostic Overview",
      badge: (data) =>
        data.doctor
          ? data.doctor.healthy
            ? "ALL PASSED"
            : "ISSUES FOUND"
          : "NOT RUN",
      badgeColor: (data: any): "green" | "red" | "slate" =>
        data.doctor ? (data.doctor.healthy ? "green" : "red") : "slate",
      description:
        'Click "Run Checks" to execute environment, database, and permission checks.',
      outputs: [
        {
          type: "status_pill",
          label: "Doctor Status:",
          status: (data) =>
            data.doctor
              ? data.doctor.healthy
                ? "healthy"
                : "warning"
              : "degraded",
          text: (data) =>
            data.doctor
              ? data.doctor.healthy
                ? "HEALTHY"
                : "WARNING"
              : "PENDING",
        },
      ],
      inputs: [
        {
          type: "button",
          id: "btn-doctor-run",
          label: "Run Checks",
          actionId: "doctor",
          variant: "primary",
        },
      ],
    },
    {
      pageId: "doctor-checks-list",
      title: "Individual Probes Detail",
      badge: (data) =>
        data.doctor?.checks ? `${data.doctor.checks.length} checks` : "0 checks",
      badgeColor: "blue",
      renderCustom: (data) => {
        if (!data.doctor?.checks || data.doctor.checks.length === 0) {
          return (
            <div className="text-slate-500 italic text-xs py-3 text-center">
              No diagnostic checks have been executed yet.
            </div>
          );
        }
        return (
          <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1 text-xs">
            {data.doctor.checks.map((chk: any, idx: number) => (
              <div
                key={idx}
                className="flex items-start justify-between p-2 rounded-lg bg-slate-950/60 border border-slate-800/80 gap-2"
              >
                <div>
                  <div className="font-medium text-slate-200">{chk.name}</div>
                  {chk.message && (
                    <div className="text-[11px] text-slate-400 mt-0.5">{chk.message}</div>
                  )}
                </div>
                <span
                  className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded ${
                    chk.status === "passed" || chk.status === "ok"
                      ? "bg-emerald-500/20 text-emerald-400"
                      : chk.status === "warning" || chk.status === "warn"
                      ? "bg-amber-500/20 text-amber-400"
                      : "bg-rose-500/20 text-rose-400"
                  }`}
                >
                  {chk.status}
                </span>
              </div>
            ))}
          </div>
        );
      },
    },
  ],
};
