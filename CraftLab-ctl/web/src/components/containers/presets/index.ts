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
  { id: "all", label: "Overview", iconName: "layout-grid", description: "Todos los paneles clave" },
  { id: "system", label: "System & Host", iconName: "cpu", description: "Métricas de recursos y hardware" },
  { id: "lifecycle", label: "Lifecycle & Ops", iconName: "activity", description: "Control del proceso supervisado" },
  { id: "releases", label: "Releases & Updates", iconName: "package", description: "Versiones, despliegues y rollbacks" },
  { id: "doctor", label: "Doctor & Health", iconName: "stethoscope", description: "Diagnósticos de entorno y base de datos" },
  { id: "logs", label: "Terminal & Logs", iconName: "terminal", description: "Stream de logs en tiempo real" },
];

export const allSupervisorPresets: PaginatedContainerPreset[] = [
  overviewTelemetryPreset,
  lifecycleSupervisorPreset,
  doctorDiagnosticsPreset,
  releasesManagerPreset,
  liveLogStreamPreset,
];
