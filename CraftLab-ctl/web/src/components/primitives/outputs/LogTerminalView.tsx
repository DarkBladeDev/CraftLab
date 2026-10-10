import React, { useRef, useEffect, useState } from "react";
import { LogStreamOutput } from "../../../types/presets";

interface LogTerminalViewProps {
  output: LogStreamOutput;
  logs?: string[];
  onClear?: () => void;
}

export const LogTerminalView: React.FC<LogTerminalViewProps> = ({
  output,
  logs = [],
  onClear,
}) => {
  const [autoScroll, setAutoScroll] = useState(output.autoscrollDefault ?? true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, autoScroll]);

  return (
    <div className="flex flex-col h-full bg-slate-950/80 border border-slate-800 rounded-xl overflow-hidden font-mono text-xs">
      {/* Terminal Toolbar */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-slate-900 border-b border-slate-800 text-slate-400">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80" />
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
          <span className="text-[11px] text-slate-400 font-sans ml-1 font-medium">
            Terminal Stream ({logs.length} lines)
          </span>
        </div>
        <div className="flex items-center gap-2 text-[11px] font-sans">
          <button
            onClick={() => setAutoScroll((prev) => !prev)}
            className={`px-2 py-0.5 rounded transition-colors ${
              autoScroll
                ? "bg-blue-600/30 text-blue-400 border border-blue-500/30 font-medium"
                : "bg-slate-800 text-slate-400 hover:text-slate-200"
            }`}
          >
            Autoscroll: {autoScroll ? "ON" : "OFF"}
          </button>
          {onClear && (
            <button
              onClick={onClear}
              className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Terminal Content */}
      <div
        ref={scrollRef}
        className="flex-1 p-3 overflow-y-auto space-y-1 text-slate-300 max-h-96 min-h-[160px]"
      >
        {logs.length === 0 ? (
          <div className="text-slate-600 italic py-4 text-center font-sans">
            No log entries yet. Waiting for supervisor messages...
          </div>
        ) : (
          logs.map((line, idx) => (
            <div key={idx} className="leading-relaxed hover:bg-slate-900/60 px-1 rounded break-all">
              {line}
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};
