import React, { useState } from "react";
import {
  PaginatedContainerPreset,
  ContainerActionDispatcher,
  ColorTone,
} from "../../types/presets";
import { OutputRenderer } from "../primitives/outputs";
import { InputRenderer } from "../primitives/inputs";

const badgeColorStyles: Record<ColorTone, string> = {
  blue: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  green: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  cyan: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  yellow: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  red: "bg-rose-500/20 text-rose-400 border-rose-500/30",
  purple: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  slate: "bg-slate-700/50 text-slate-300 border-slate-600/40",
};

interface ContainerEngineProps {
  preset: PaginatedContainerPreset;
  data: any;
  actions: ContainerActionDispatcher;
  logs?: string[];
  onClearLogs?: () => void;
  cols?: number;
  rows?: number;
  isDraggable?: boolean;
  onResizeSpan?: (deltaCols: number) => void;
  className?: string;
  dragHandleProps?: React.HTMLAttributes<HTMLDivElement>;
}

export const ContainerEngine: React.FC<ContainerEngineProps> = ({
  preset,
  data,
  actions,
  logs = [],
  onClearLogs,
  cols = preset.defaultSpan.cols,
  onResizeSpan,
  className = "",
  dragHandleProps,
}) => {
  // Sub-view pagination index (1-indexed)
  const [subViewIndex, setSubViewIndex] = useState(1);
  // Records collection pagination index (1-indexed)
  const [recordPageIndex, setRecordPageIndex] = useState(1);

  const pages = preset.pages || [];
  const totalSubViews = pages.length;
  const currentSubView = pages[subViewIndex - 1];

  // Records collection items
  const collection = preset.collection;
  const allItems = collection ? collection.getItems(data) || [] : [];
  const pageSize = collection?.pageSize || 3;
  const totalRecordPages = Math.max(1, Math.ceil(allItems.length / pageSize));
  const currentRecords = collection
    ? allItems.slice((recordPageIndex - 1) * pageSize, recordPageIndex * pageSize)
    : [];

  const handlePrevSubView = () => {
    setSubViewIndex((prev) => (prev > 1 ? prev - 1 : totalSubViews));
  };

  const handleNextSubView = () => {
    setSubViewIndex((prev) => (prev < totalSubViews ? prev + 1 : 1));
  };

  const handlePrevRecords = () => {
    setRecordPageIndex((prev) => (prev > 1 ? prev - 1 : totalRecordPages));
  };

  const handleNextRecords = () => {
    setRecordPageIndex((prev) => (prev < totalRecordPages ? prev + 1 : 1));
  };

  // Determine span class
  const colSpanClass =
    cols === 4
      ? "col-span-1 md:col-span-2 lg:col-span-4"
      : cols === 3
      ? "col-span-1 md:col-span-2 lg:col-span-3"
      : cols === 2
      ? "col-span-1 md:col-span-2"
      : "col-span-1";

  return (
    <div
      className={`bg-slate-900/90 border border-slate-800 rounded-2xl p-4 shadow-xl flex flex-col justify-between transition-all duration-200 hover:border-slate-700/80 ${colSpanClass} ${className}`}
    >
      {/* Container Header */}
      <div>
        <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 mb-3 gap-2">
          {/* Title & Drag Handle */}
          <div className="flex items-center gap-2 min-w-0">
            {dragHandleProps && (
              <div
                {...dragHandleProps}
                className="cursor-grab active:cursor-grabbing text-slate-500 hover:text-slate-300 p-0.5 rounded transition-colors select-none"
                title="Arrastrar para reorganizar"
              >
                <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M7 4a2 2 0 11-4 0 2 2 0 014 0zm0 6a2 2 0 11-4 0 2 2 0 014 0zm0 6a2 2 0 11-4 0 2 2 0 014 0zm8-12a2 2 0 11-4 0 2 2 0 014 0zm0 6a2 2 0 11-4 0 2 2 0 014 0zm0 6a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
            )}
            <h3 className="font-semibold text-xs tracking-wider uppercase text-slate-200 truncate">
              {preset.title}
            </h3>
          </div>

          {/* Right Header Controls (Pagination & Resize) */}
          <div className="flex items-center gap-2">
            {/* Sub-view Pagination Controller */}
            {preset.paginationMode === "subviews" && totalSubViews > 1 && (
              <div className="flex items-center gap-1 bg-slate-950/70 px-2 py-0.5 rounded-lg border border-slate-800 text-xs">
                <button
                  type="button"
                  onClick={handlePrevSubView}
                  className="hover:text-blue-400 text-slate-400 font-bold px-1 cursor-pointer transition-colors"
                  title="Página anterior"
                >
                  ◀
                </button>
                <span className="font-mono text-blue-400 font-semibold px-1 text-[11px]">
                  {subViewIndex} / {totalSubViews}
                </span>
                <button
                  type="button"
                  onClick={handleNextSubView}
                  className="hover:text-blue-400 text-slate-400 font-bold px-1 cursor-pointer transition-colors"
                  title="Página siguiente"
                >
                  ▶
                </button>
              </div>
            )}

            {/* Records Pagination Controller */}
            {preset.paginationMode === "records" && (
              <div className="flex items-center gap-1 bg-slate-950/70 px-2 py-0.5 rounded-lg border border-slate-800 text-xs">
                <button
                  type="button"
                  onClick={handlePrevRecords}
                  disabled={totalRecordPages <= 1}
                  className="hover:text-emerald-400 text-slate-400 font-bold px-1 cursor-pointer disabled:opacity-40 transition-colors"
                  title="Página anterior de registros"
                >
                  ◀
                </button>
                <span className="font-mono text-emerald-400 font-semibold px-1 text-[11px]">
                  {recordPageIndex} / {totalRecordPages}
                </span>
                <button
                  type="button"
                  onClick={handleNextRecords}
                  disabled={totalRecordPages <= 1}
                  className="hover:text-emerald-400 text-slate-400 font-bold px-1 cursor-pointer disabled:opacity-40 transition-colors"
                  title="Página siguiente de registros"
                >
                  ▶
                </button>
              </div>
            )}

            {/* Column Span Resize Control (+ / -) */}
            {onResizeSpan && (
              <div className="flex items-center bg-slate-950/60 rounded-lg border border-slate-800 text-[10px]">
                <button
                  type="button"
                  onClick={() => onResizeSpan(-1)}
                  disabled={cols <= (preset.defaultSpan.minCols || 1)}
                  className="px-1.5 py-0.5 text-slate-400 hover:text-white disabled:opacity-30 cursor-pointer"
                  title="Reducir ancho"
                >
                  -
                </button>
                <span className="text-slate-400 font-mono px-0.5">{cols}c</span>
                <button
                  type="button"
                  onClick={() => onResizeSpan(1)}
                  disabled={cols >= (preset.defaultSpan.maxCols || 4)}
                  className="px-1.5 py-0.5 text-slate-400 hover:text-white disabled:opacity-30 cursor-pointer"
                  title="Ampliar ancho"
                >
                  +
                </button>
              </div>
            )}
          </div>
        </div>

        {/* ================= BODY CONTENT ================= */}
        {/* MODE: SUBVIEWS */}
        {preset.paginationMode === "subviews" && currentSubView && (
          <div className="space-y-3">
            {/* Sub-view Sub-header with Title / Badge */}
            <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
              <span className="truncate">{currentSubView.title}</span>
              {currentSubView.badge && (
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                    badgeColorStyles[
                      typeof currentSubView.badgeColor === "function"
                        ? currentSubView.badgeColor(data)
                        : currentSubView.badgeColor || "blue"
                    ]
                  }`}
                >
                  {typeof currentSubView.badge === "function"
                    ? currentSubView.badge(data)
                    : currentSubView.badge}
                </span>
              )}
            </div>

            {currentSubView.description && (
              <p className="text-xs text-slate-400">{currentSubView.description}</p>
            )}

            {/* Custom Renderer if provided */}
            {currentSubView.renderCustom &&
              currentSubView.renderCustom(data, actions)}

            {/* Outputs */}
            {currentSubView.outputs && currentSubView.outputs.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {currentSubView.outputs.map((out, idx) => (
                  <OutputRenderer
                    key={idx}
                    output={out}
                    data={data}
                    logs={logs}
                    onClearLogs={onClearLogs}
                  />
                ))}
              </div>
            )}

            {/* Inputs */}
            {currentSubView.inputs && currentSubView.inputs.length > 0 && (
              <div className="pt-2 border-t border-slate-800/60 flex flex-wrap gap-2 items-center">
                {currentSubView.inputs.map((inp, idx) => (
                  <InputRenderer key={idx} input={inp} actions={actions} data={data} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* MODE: RECORDS */}
        {preset.paginationMode === "records" && collection && (
          <div className="space-y-3">
            <div className="space-y-2">
              {currentRecords.length === 0 ? (
                <div className="text-slate-500 italic text-xs py-4 text-center">
                  {collection.emptyMessage || "No hay registros disponibles."}
                </div>
              ) : (
                currentRecords.map((item, idx) => (
                  <div key={idx}>
                    {collection.renderItem(item, (recordPageIndex - 1) * pageSize + idx, actions)}
                  </div>
                ))
              )}
            </div>

            {collection.footerInputs && collection.footerInputs.length > 0 && (
              <div className="pt-3 border-t border-slate-800/80 flex flex-wrap gap-2 items-center justify-between">
                {collection.footerInputs.map((inp, idx) => (
                  <InputRenderer key={idx} input={inp} actions={actions} data={data} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* MODE: NONE */}
        {preset.paginationMode === "none" && (
          <div className="space-y-3">
            {preset.renderCustom && preset.renderCustom(data, actions)}

            {preset.outputs && preset.outputs.length > 0 && (
              <div className="space-y-2">
                {preset.outputs.map((out, idx) => (
                  <OutputRenderer
                    key={idx}
                    output={out}
                    data={data}
                    logs={logs}
                    onClearLogs={onClearLogs}
                  />
                ))}
              </div>
            )}

            {preset.inputs && preset.inputs.length > 0 && (
              <div className="pt-2 border-t border-slate-800/60 flex flex-wrap gap-2 items-center">
                {preset.inputs.map((inp, idx) => (
                  <InputRenderer key={idx} input={inp} actions={actions} data={data} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Action feedback message banner if active */}
      {actions.message && (
        <div
          className={`mt-3 text-xs px-2.5 py-1.5 rounded-lg border font-medium flex items-center justify-between ${
            actions.message.type === "ok"
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
              : "bg-rose-500/10 border-rose-500/30 text-rose-400"
          }`}
        >
          <span>{actions.message.text}</span>
        </div>
      )}
    </div>
  );
};
