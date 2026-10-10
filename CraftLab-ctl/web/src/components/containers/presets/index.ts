import { CategoryDefinition, PaginatedContainerPreset } from "../../../types/presets";
import { overviewTelemetryPreset } from "./overviewTelemetryPreset";
import { lifecycleSupervisorPreset } from "./lifecycleSupervisorPreset";
import { doctorDiagnosticsPreset } from "./doctorDiagnosticsPreset";
import { releasesManagerPreset } from "./releasesManagerPreset";
import { liveLogStreamPreset } from "./liveLogStreamPreset";
import { securityThreatRadarPreset } from "./securityThreatRadarPreset";
import { securityAnomalyMonitorPreset } from "./securityAnomalyMonitorPreset";
import { securityAuditExplorerPreset } from "./securityAuditExplorerPreset";

export {
  overviewTelemetryPreset,
  lifecycleSupervisorPreset,
  doctorDiagnosticsPreset,
  releasesManagerPreset,
  liveLogStreamPreset,
  securityThreatRadarPreset,
  securityAnomalyMonitorPreset,
  securityAuditExplorerPreset,
};

export const SUPERVISOR_CATEGORIES: CategoryDefinition[] = [
  { id: "all", label: "Overview", iconName: "layout-grid", description: "All core panels" },
  { id: "system", label: "System & Host", iconName: "cpu", description: "Host resource and hardware telemetry" },
  { id: "lifecycle", label: "Lifecycle & Ops", iconName: "activity", description: "Supervised process lifecycle and controls" },
  { id: "releases", label: "Releases & Updates", iconName: "package", description: "Versions, deployments, and rollbacks" },
  { id: "doctor", label: "Doctor & Health", iconName: "stethoscope", description: "Environment and database health diagnostics" },
  { id: "security", label: "Security & Audit", iconName: "shield-alert", description: "Threat radar, anomaly monitor, and forensic audit explorer" },
  { id: "logs", label: "Terminal & Logs", iconName: "terminal", description: "Real-time log stream" },
];

export const allSupervisorPresets: PaginatedContainerPreset[] = [
  overviewTelemetryPreset,
  lifecycleSupervisorPreset,
  doctorDiagnosticsPreset,
  releasesManagerPreset,
  securityThreatRadarPreset,
  securityAnomalyMonitorPreset,
  securityAuditExplorerPreset,
  liveLogStreamPreset,
];
