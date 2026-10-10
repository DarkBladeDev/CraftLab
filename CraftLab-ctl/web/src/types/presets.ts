import React from "react";
import { UserContext } from "../api";

export type RoleName = "admin" | "operator" | "viewer" | string;

export interface CategoryDefinition {
  id: string;
  label: string;
  iconName?: string;
  description?: string;
}

export type ColorTone = "blue" | "green" | "cyan" | "yellow" | "red" | "purple" | "slate";

// ----------------- OUTPUT PRIMITIVES -----------------

export interface MetricStatOutput {
  type: "metric_stat";
  label: string;
  value: string | number | ((data: any) => string | number);
  subValue?: string | ((data: any) => string);
  color?: ColorTone;
  progressPercent?: number | ((data: any) => number);
}

export interface GaugeOutput {
  type: "gauge";
  label: string;
  percent: number | ((data: any) => number);
  displayValue?: string | ((data: any) => string);
  color?: ColorTone;
}

export interface KeyValueOutput {
  type: "key_value";
  label: string;
  value: string | number | ((data: any) => string | number);
  mono?: boolean;
  statusDot?: "green" | "red" | "yellow" | "cyan" | "slate";
}

export interface StatusPillOutput {
  type: "status_pill";
  label: string;
  status: "running" | "stopped" | "starting" | "degraded" | "healthy" | "warning" | "error" | ((data: any) => string);
  text?: string | ((data: any) => string);
}

export interface LogStreamOutput {
  type: "log_stream";
  maxLines?: number;
  autoscrollDefault?: boolean;
}

export type OutputPrimitive =
  | MetricStatOutput
  | GaugeOutput
  | KeyValueOutput
  | StatusPillOutput
  | LogStreamOutput;

// ----------------- INPUT PRIMITIVES (WITH RBAC) -----------------

export interface BaseInputPrimitive {
  id: string;
  label: string;
  requiredRoles?: RoleName[];
  allowBreakGlass?: boolean;
}

export interface ActionButtonInput extends BaseInputPrimitive {
  type: "button";
  variant?: "primary" | "secondary" | "danger" | "warning" | "outline";
  actionId: string;
  confirmMessage?: string;
  disabledIf?: (data: any) => boolean;
  loadingIfAction?: string;
}

export interface ToggleSwitchInput extends BaseInputPrimitive {
  type: "toggle";
  actionId: string;
  checked: boolean | ((data: any) => boolean);
  disabledIf?: (data: any) => boolean;
}

export interface TextInputInput extends BaseInputPrimitive {
  type: "text_input";
  placeholder?: string;
  actionId: string;
  buttonLabel?: string;
  initialValue?: string;
}

export interface NumberStepperInput extends BaseInputPrimitive {
  type: "number_stepper";
  min?: number;
  max?: number;
  step?: number;
  actionId: string;
  initialValue?: number;
}

export interface SelectDropdownInput extends BaseInputPrimitive {
  type: "select";
  actionId: string;
  buttonLabel?: string;
  options: { label: string; value: string }[] | ((data: any) => { label: string; value: string }[]);
}

export type InputPrimitive =
  | ActionButtonInput
  | ToggleSwitchInput
  | TextInputInput
  | NumberStepperInput
  | SelectDropdownInput;

// ----------------- ACTION DISPATCHER & CONTEXT -----------------

export interface ContainerActionDispatcher {
  dispatch: (actionId: string, payload?: any) => Promise<any> | void;
  user: UserContext;
  isLoading: (actionId?: string) => boolean;
  message?: { text: string; type: "ok" | "err" } | null;
}

// ----------------- PAGINATION MODES & PAGES -----------------

export interface ContainerSubViewPage {
  pageId: string;
  title: string;
  badge?: string | ((data: any) => string);
  badgeColor?: ColorTone | ((data: any) => ColorTone);
  description?: string;
  outputs?: OutputPrimitive[];
  inputs?: InputPrimitive[];
  renderCustom?: (data: any, actions: ContainerActionDispatcher) => React.ReactNode;
}

export interface ContainerCollectionConfig {
  pageSize: number;
  getItems: (data: any) => any[];
  renderItem: (item: any, index: number, actions: ContainerActionDispatcher) => React.ReactNode;
  emptyMessage?: string;
  footerInputs?: InputPrimitive[];
}

export interface ContainerGridSpan {
  cols: number; // 1 to 4 columns in grid
  rows: number; // 1 to 3 rows
  minCols?: number;
  maxCols?: number;
  minRows?: number;
  maxRows?: number;
}

export interface PaginatedContainerPreset {
  id: string;
  title: string;
  iconName?: string;
  category: string;
  defaultSpan: ContainerGridSpan;
  paginationMode: "subviews" | "records" | "none";
  pages?: ContainerSubViewPage[];
  collection?: ContainerCollectionConfig;
  outputs?: OutputPrimitive[];
  inputs?: InputPrimitive[];
  renderCustom?: (data: any, actions: ContainerActionDispatcher) => React.ReactNode;
}

// ----------------- LAYOUT PERSISTENCE CONTRACT -----------------

export interface ContainerLayoutItem {
  id: string;
  cols: number;
  rows: number;
  order: number;
}

export interface CategoryLayoutState {
  version: number;
  category: string;
  containers: ContainerLayoutItem[];
}
