import { CategoryDefinition, PaginatedContainerPreset } from "../../../types/presets";
import { overviewTelemetryPreset } from "./overviewTelemetryPreset";
import { lifecycleSupervisorPreset } from "./lifecycleSupervisorPreset";
import { doctorDiagnosticsPreset } from "./doctorDiagnosticsPreset";
import { releasesManagerPreset } from "./releasesManagerPreset";
import { liveLogStreamPreset } from "./liveLogStreamPreset";

export {
  overviewTelemetryPreset,
  lifecycleSupervisorPreset,
  doctorDiagnosticsPreset,
  releasesManagerPreset,
  liveLogStreamPreset,
};

export const SUPERVISOR_CATEGORIES: CategoryDefinition[] = [
  { id: "all", label: "Overview", iconName: "layout-grid", description: "All core panels" },
  { id: "system", label: "System & Host", iconName: "cpu", description: "Host resource and hardware telemetry" },
  { id: "lifecycle", label: "Lifecycle & Ops", iconName: "activity", description: "Supervised process lifecycle and controls" },
  { id: "releases", label: "Releases & Updates", iconName: "package", description: "Versions, deployments, and rollbacks" },
  { id: "doctor", label: "Doctor & Health", iconName: "stethoscope", description: "Environment and database health diagnostics" },
  { id: "logs", label: "Terminal & Logs", iconName: "terminal", description: "Real-time log stream" },
];

export const allSupervisorPresets: PaginatedContainerPreset[] = [
  overviewTelemetryPreset,
  lifecycleSupervisorPreset,
  doctorDiagnosticsPreset,
  releasesManagerPreset,
  liveLogStreamPreset,
];
