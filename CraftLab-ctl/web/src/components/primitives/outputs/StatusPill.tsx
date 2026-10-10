import React from "react";
import { StatusPillOutput } from "../../../types/presets";

interface StatusPillProps {
  output: StatusPillOutput;
  data?: any;
}

export const StatusPill: React.FC<StatusPillProps> = ({ output, data }) => {
  const statusRaw = typeof output.status === "function" ? output.status(data) : output.status;
  const status = (statusRaw || "").toLowerCase();
  const text = typeof output.text === "function" ? output.text(data) : (output.text || status.toUpperCase());

  let bg = "bg-slate-800 text-slate-300 border-slate-700";
  let dot = "bg-slate-400";
  let pulse = false;

  if (status === "running" || status === "healthy" || status === "ok" || status === "passed") {
    bg = "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
    dot = "bg-emerald-400";
    pulse = true;
  } else if (status === "stopped" || status === "error" || status === "failed") {
    bg = "bg-rose-500/10 text-rose-400 border-rose-500/30";
    dot = "bg-rose-400";
  } else if (status === "starting" || status === "warning" || status === "degraded") {
    bg = "bg-amber-500/10 text-amber-400 border-amber-500/30";
    dot = "bg-amber-400";
    pulse = true;
  }

  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-slate-400 font-medium">{output.label}</span>
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${bg}`}>
        <span className={`w-1.5 h-1.5 rounded-full ${dot} ${pulse ? "animate-pulse" : ""}`} />
        <span>{text}</span>
      </span>
    </div>
  );
};
