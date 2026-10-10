import React from "react";
import { KeyValueOutput } from "../../../types/presets";

const dotColors = {
  green: "bg-emerald-400",
  red: "bg-rose-500",
  yellow: "bg-amber-400",
  cyan: "bg-cyan-400",
  slate: "bg-slate-400",
};

interface KeyValueGridProps {
  items: KeyValueOutput[];
  data?: any;
}

export const KeyValueGrid: React.FC<KeyValueGridProps> = ({ items, data }) => {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3 divide-y divide-slate-800/80 text-xs">
      {items.map((item, idx) => {
        const val = typeof item.value === "function" ? item.value(data) : item.value;
        return (
          <div key={idx} className="flex items-center justify-between py-2 first:pt-0 last:pb-0">
            <span className="text-slate-400">{item.label}</span>
            <div className="flex items-center gap-1.5">
              {item.statusDot && (
                <span className={`w-2 h-2 rounded-full ${dotColors[item.statusDot] || "bg-slate-400"}`} />
              )}
              <span className={`text-slate-200 font-medium ${item.mono ? "font-mono" : ""}`}>
                {val}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
