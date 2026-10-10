import { PaginatedContainerPreset } from "../../../types/presets";

export const securityThreatRadarPreset: PaginatedContainerPreset = {
  id: "security-threat-radar",
  title: "Threat Radar & Posture",
  iconName: "shield-alert",
  category: "security",
  defaultSpan: { cols: 1, rows: 1, minCols: 1, maxCols: 2 },
  paginationMode: "none",
  outputs: [
    {
      type: "gauge",
      label: "Threat Index",
      percent: (data) => data.security?.posture?.threat_index ?? 0,
      displayValue: (data) => `${data.security?.posture?.threat_index ?? 0}%`,
      color: "yellow",
    },
    {
      type: "status_pill",
      label: "Posture:",
      status: (data) => {
        const cls = data.security?.posture?.classification;
        if (cls === "CRITICAL") return "error";
        if (cls === "HIGH" || cls === "ELEVATED") return "warning";
        if (cls === "LOCKDOWN") return "degraded";
        return "healthy";
      },
      text: (data) => data.security?.posture?.classification ?? "NORMAL",
    },
    {
      type: "metric_stat",
      label: "Failed Auths (15m)",
      value: (data) => data.security?.posture?.failed_auths_15m ?? 0,
      subValue: () => "Threshold: 5/min",
      color: "yellow",
    },
    {
      type: "metric_stat",
      label: "Quarantined Sources",
      value: (data) => data.security?.posture?.quarantined_ips_count ?? 0,
      subValue: () => "Active blocks",
      color: "red",
    },
  ],
  inputs: [
    {
      type: "toggle",
      id: "toggle-emergency-lockdown",
      label: "Emergency Lockdown Mode",
      actionId: "security.toggle_lockdown",
      checked: (data) => !!data.security?.posture?.lockdown_enabled,
      requiredRoles: ["admin"],
    },
    {
      type: "button",
      id: "btn-recalculate-posture",
      label: "Recalculate Posture",
      actionId: "security.refresh",
      variant: "outline",
    },
  ],
};
