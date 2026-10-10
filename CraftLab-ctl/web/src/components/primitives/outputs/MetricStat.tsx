import React from "react";
import { MetricStatOutput, ColorTone } from "../../../types/presets";

const colorStyles: Record<ColorTone, { text: string; bg: string; bar: string }> = {
  blue: { text: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20", bar: "bg-blue-500" },
  green: { text: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20", bar: "bg-emerald-500" },
  cyan: { text: "text-cyan-400", bg: "bg-cyan-500/10 border-cyan-500/20", bar: "bg-cyan-500" },
  yellow: { text: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20", bar: "bg-amber-500" },
  red: { text: "text-rose-400", bg: "bg-rose-500/10 border-rose-500/20", bar: "bg-rose-500" },
  purple: { text: "text-purple-400", bg: "bg-purple-500/10 border-purple-500/20", bar: "bg-purple-500" },
  slate: { text: "text-slate-300", bg: "bg-slate-800/40 border-slate-700/50", bar: "bg-slate-400" },
};

interface MetricStatProps {
  output: MetricStatOutput;
  data?: any;
}

export const MetricStat: React.FC<MetricStatProps> = ({ output, data }) => {
  const resolvedValue = typeof output.value === "function" ? output.value(data) : output.value;
  const resolvedSubValue = typeof output.subValue === "function" ? output.subValue(data) : output.subValue;
  const color = output.color || "blue";
  const styles = colorStyles[color] || colorStyles.blue;
  const percent = typeof output.progressPercent === "function"
    ? output.progressPercent(data)
    : output.progressPercent;

  return (
    <div className={`p-3 rounded-xl border flex flex-col justify-between ${styles.bg}`}>
      <div className="flex items-center justify-between text-xs text-slate-400 font-medium mb-1">
        <span>{output.label}</span>
      </div>
      <div className={`text-2xl font-bold tracking-tight ${styles.text}`}>
        {resolvedValue}
      </div>
      {resolvedSubValue && (
        <div className="text-xs text-slate-400 mt-1 truncate">
          {resolvedSubValue}
        </div>
      )}
      {percent !== undefined && (
        <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2.5 overflow-hidden">
          <div
            className={`h-1.5 rounded-full transition-all duration-500 ${styles.bar}`}
            style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
          />
        </div>
      )}
    </div>
  );
};
