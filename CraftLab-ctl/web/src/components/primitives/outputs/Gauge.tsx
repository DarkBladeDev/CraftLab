import React from "react";
import { GaugeOutput, ColorTone } from "../../../types/presets";

const colorClasses: Record<ColorTone, { stroke: string; text: string }> = {
  blue: { stroke: "stroke-blue-500", text: "text-blue-400" },
  green: { stroke: "stroke-emerald-500", text: "text-emerald-400" },
  cyan: { stroke: "stroke-cyan-500", text: "text-cyan-400" },
  yellow: { stroke: "stroke-amber-500", text: "text-amber-400" },
  red: { stroke: "stroke-rose-500", text: "text-rose-400" },
  purple: { stroke: "stroke-purple-500", text: "text-purple-400" },
  slate: { stroke: "stroke-slate-400", text: "text-slate-300" },
};

interface GaugeProps {
  output: GaugeOutput;
  data?: any;
}

export const Gauge: React.FC<GaugeProps> = ({ output, data }) => {
  const percent = typeof output.percent === "function" ? output.percent(data) : output.percent;
  const clampedPercent = Math.min(100, Math.max(0, percent || 0));
  const displayVal = typeof output.displayValue === "function" ? output.displayValue(data) : (output.displayValue || `${clampedPercent}%`);
  const color = output.color || (clampedPercent > 85 ? "red" : clampedPercent > 70 ? "yellow" : "blue");
  const styles = colorClasses[color] || colorClasses.blue;

  return (
    <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between gap-3">
      <div>
        <div className="text-xs text-slate-400 font-medium">{output.label}</div>
        <div className={`text-xl font-bold ${styles.text} mt-0.5`}>
          {displayVal}
        </div>
      </div>
      <div className="w-14 h-14 relative flex items-center justify-center">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
          <circle
            cx="18"
            cy="18"
            r="15"
            fill="none"
            className="stroke-slate-800"
            strokeWidth="3.5"
          />
          <circle
            cx="18"
            cy="18"
            r="15"
            fill="none"
            className={`${styles.stroke} transition-all duration-700 ease-out`}
            strokeWidth="3.5"
            strokeDasharray="94.2"
            strokeDashoffset={94.2 - (94.2 * clampedPercent) / 100}
            strokeLinecap="round"
          />
        </svg>
        <span className="absolute text-[11px] font-bold text-slate-300">
          {Math.round(clampedPercent)}%
        </span>
      </div>
    </div>
  );
};
