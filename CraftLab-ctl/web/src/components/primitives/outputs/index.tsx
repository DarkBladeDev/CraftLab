import React from "react";
import { OutputPrimitive } from "../../../types/presets";
import { MetricStat } from "./MetricStat";
import { Gauge } from "./Gauge";
import { KeyValueGrid } from "./KeyValueGrid";
import { StatusPill } from "./StatusPill";
import { LogTerminalView } from "./LogTerminalView";

export { MetricStat, Gauge, KeyValueGrid, StatusPill, LogTerminalView };

interface OutputRendererProps {
  output: OutputPrimitive;
  data?: any;
  logs?: string[];
  onClearLogs?: () => void;
}

export const OutputRenderer: React.FC<OutputRendererProps> = ({
  output,
  data,
  logs,
  onClearLogs,
}) => {
  switch (output.type) {
    case "metric_stat":
      return <MetricStat output={output} data={data} />;
    case "gauge":
      return <Gauge output={output} data={data} />;
    case "key_value":
      return <KeyValueGrid items={[output]} data={data} />;
    case "status_pill":
      return <StatusPill output={output} data={data} />;
    case "log_stream":
      return <LogTerminalView output={output} logs={logs} onClear={onClearLogs} />;
    default:
      return null;
  }
};
