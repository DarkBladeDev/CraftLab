import React from "react";
import { PaginatedContainerPreset } from "../../../types/presets";

export const securityAnomalyMonitorPreset: PaginatedContainerPreset = {
  id: "security-anomaly-monitor",
  title: "Anomaly Monitor & Mitigations",
  iconName: "alert-triangle",
  category: "security",
  defaultSpan: { cols: 2, rows: 1, minCols: 2, maxCols: 4 },
  paginationMode: "subviews",
  pages: [
    {
      pageId: "live-anomalies",
      title: "Detected Anomalies",
      badge: (data) =>
        data.security?.anomalies?.length > 0
          ? `${data.security.anomalies.length} ALERTS`
          : "CLEAR",
      badgeColor: (data) =>
        data.security?.anomalies?.length > 0 ? "red" : "green",
      description:
        "Heuristic triggers detected in the current 15-minute sliding evaluation window.",
      renderCustom: (data, actions) => {
        const anomalies = data.security?.anomalies || [];
        if (anomalies.length === 0) {
          return (
            <div className="flex flex-col items-center justify-center py-6 text-center text-slate-500 text-xs">
              <span className="text-emerald-400 font-semibold mb-1">
                ✓ No active anomalies detected
              </span>
              <span>All authentication and API streams are operating within normal thresholds.</span>
            </div>
          );
        }

        return (
          <div className="space-y-2 max-h-56 overflow-y-auto pr-1 text-xs">
            {anomalies.map((a: any) => {
              const severityColor =
                a.severity === "critical"
                  ? "bg-rose-500/20 text-rose-400 border-rose-500/40"
                  : a.severity === "high"
                  ? "bg-amber-500/20 text-amber-400 border-amber-500/40"
                  : "bg-blue-500/20 text-blue-400 border-blue-500/40";

              return (
                <div
                  key={a.alert_id}
                  className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 flex flex-col gap-2"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="font-semibold text-slate-200">{a.title}</div>
                      <div className="text-[11px] text-slate-400 mt-0.5">{a.description}</div>
                      {(a.source_ip || a.target_actor) && (
                        <div className="text-[10px] text-slate-500 font-mono mt-1">
                          {a.source_ip && <span>Source IP: {a.source_ip} </span>}
                          {a.target_actor && <span>Target Actor: {a.target_actor}</span>}
                        </div>
                      )}
                    </div>
                    <span
                      className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded border ${severityColor}`}
                    >
                      {a.severity}
                    </span>
                  </div>

                  {/* Incident Mitigation Action Buttons */}
                  <div className="flex items-center gap-2 pt-1 border-t border-slate-900">
                    {a.source_ip && (
                      <button
                        type="button"
                        onClick={() =>
                          actions.dispatch("security.quarantine_ip", {
                            ip: a.source_ip,
                            duration_minutes: 60,
                            reason: a.title,
                          })
                        }
                        className="px-2 py-1 text-[10px] rounded bg-rose-600/20 hover:bg-rose-600/40 text-rose-300 border border-rose-500/30 cursor-pointer font-medium"
                      >
                        Quarantine IP
                      </button>
                    )}
                    {a.target_actor && (
                      <button
                        type="button"
                        onClick={() =>
                          actions.dispatch("security.revoke_user_sessions", a.target_actor)
                        }
                        className="px-2 py-1 text-[10px] rounded bg-amber-600/20 hover:bg-amber-600/40 text-amber-300 border border-amber-500/30 cursor-pointer font-medium"
                      >
                        Revoke User Sessions
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() =>
                        actions.dispatch("security.dismiss_anomaly", a.alert_id)
                      }
                      className="px-2 py-1 text-[10px] rounded bg-slate-800 hover:bg-slate-700 text-slate-400 cursor-pointer ml-auto"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        );
      },
    },
    {
      pageId: "active-quarantines",
      title: "Active Quarantines & Containment",
      badge: (data) =>
        data.security?.quarantines?.length > 0
          ? `${data.security.quarantines.length} BLOCKED`
          : "0 BLOCKED",
      badgeColor: "red",
      description:
        "Inspect quarantined sources and execute emergency containment actions.",
      renderCustom: (data, actions) => {
        const quarantines = data.security?.quarantines || [];
        return (
          <div className="space-y-2 mb-2">
            {quarantines.length === 0 ? (
              <div className="text-slate-500 italic text-xs py-2 text-center">
                No IP addresses are currently quarantined.
              </div>
            ) : (
              <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1 text-xs">
                {quarantines.map((q: any) => (
                  <div
                    key={q.ip}
                    className="flex items-center justify-between p-2 rounded-lg bg-slate-950/60 border border-slate-800"
                  >
                    <div>
                      <div className="font-mono text-rose-300 font-semibold">{q.ip}</div>
                      <div className="text-[10px] text-slate-500">
                        Expires: {q.expires_at ? new Date(q.expires_at).toLocaleTimeString() : "--"} ({q.reason})
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => actions.dispatch("security.unquarantine_ip", q.ip)}
                      className="px-2 py-0.5 text-[10px] rounded bg-slate-800 hover:bg-slate-700 text-slate-300 cursor-pointer"
                    >
                      Unblock
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      },
      inputs: [
        {
          type: "text_input",
          id: "input-manual-quarantine",
          label: "Manual IP Quarantine",
          placeholder: "e.g. 192.168.1.50",
          buttonLabel: "Quarantine",
          actionId: "security.manual_quarantine",
          requiredRoles: ["admin"],
        },
        {
          type: "button",
          id: "btn-revoke-all-sessions",
          label: "Revoke All Active Sessions",
          actionId: "security.revoke_sessions",
          variant: "danger",
          confirmMessage:
            "This will instantly disconnect ALL active users across the platform. Continue?",
          requiredRoles: ["admin"],
        },
      ],
    },
  ],
};
