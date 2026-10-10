import React, { useState, useEffect } from "react";
import {
  PaginatedContainerPreset,
  ContainerActionDispatcher,
  ContainerLayoutItem,
} from "../../types/presets";
import { ContainerEngine } from "./ContainerEngine";

const STORAGE_PREFIX = "craftlab_ctl_layout_v1:";

interface DraggableGridProps {
  category: string;
  presets: PaginatedContainerPreset[];
  data: any;
  actions: ContainerActionDispatcher;
  logs?: string[];
  onClearLogs?: () => void;
  resetTrigger?: number;
}

export const DraggableGrid: React.FC<DraggableGridProps> = ({
  category,
  presets,
  data,
  actions,
  logs = [],
  onClearLogs,
  resetTrigger = 0,
}) => {
  const storageKey = `${STORAGE_PREFIX}${category}`;

  // Initialize layout items from storage or defaults
  const getInitialLayout = (): ContainerLayoutItem[] => {
    try {
      const stored = localStorage.getItem(storageKey);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) {
          // Merge with any newly added presets that might not be in saved layout
          const storedIds = new Set(parsed.map((p) => p.id));
          const missing = presets
            .filter((p) => !storedIds.has(p.id))
            .map((p, idx) => ({
              id: p.id,
              cols: p.defaultSpan.cols,
              rows: p.defaultSpan.rows,
              order: parsed.length + idx,
            }));
          return [...parsed, ...missing].sort((a, b) => a.order - b.order);
        }
      }
    } catch (e) {
      console.warn("Failed to read layout from localStorage:", e);
    }

    return presets.map((p, idx) => ({
      id: p.id,
      cols: p.defaultSpan.cols,
      rows: p.defaultSpan.rows,
      order: idx,
    }));
  };

  const [layoutItems, setLayoutItems] = useState<ContainerLayoutItem[]>(getInitialLayout);
  const [draggedId, setDraggedId] = useState<string | null>(null);
  const [dragOverId, setDragOverId] = useState<string | null>(null);

  // Re-sync layout when category or resetTrigger changes
  useEffect(() => {
    setLayoutItems(getInitialLayout());
  }, [category, resetTrigger]);

  const saveLayout = (items: ContainerLayoutItem[]) => {
    setLayoutItems(items);
    try {
      localStorage.setItem(storageKey, JSON.stringify(items));
    } catch (e) {
      console.warn("Failed to save layout to localStorage:", e);
    }
  };

  // Reorder via drag & drop
  const handleDragStart = (id: string, e: React.DragEvent) => {
    setDraggedId(id);
    e.dataTransfer.effectAllowed = "move";
  };

  const handleDragOver = (id: string, e: React.DragEvent) => {
    e.preventDefault();
    if (dragOverId !== id) {
      setDragOverId(id);
    }
  };

  const handleDrop = (targetId: string, e: React.DragEvent) => {
    e.preventDefault();
    if (!draggedId || draggedId === targetId) {
      setDraggedId(null);
      setDragOverId(null);
      return;
    }

    const currentOrder = [...layoutItems].sort((a, b) => a.order - b.order);
    const sourceIdx = currentOrder.findIndex((it) => it.id === draggedId);
    const targetIdx = currentOrder.findIndex((it) => it.id === targetId);

    if (sourceIdx !== -1 && targetIdx !== -1) {
      const [moved] = currentOrder.splice(sourceIdx, 1);
      currentOrder.splice(targetIdx, 0, moved);
      const reindexed = currentOrder.map((it, idx) => ({ ...it, order: idx }));
      saveLayout(reindexed);
    }

    setDraggedId(null);
    setDragOverId(null);
  };

  const handleDragEnd = () => {
    setDraggedId(null);
    setDragOverId(null);
  };

  // Resize column span
  const handleResize = (id: string, deltaCols: number) => {
    const preset = presets.find((p) => p.id === id);
    if (!preset) return;

    const minCols = preset.defaultSpan.minCols || 1;
    const maxCols = preset.defaultSpan.maxCols || 4;

    const updated = layoutItems.map((item) => {
      if (item.id === id) {
        const nextCols = Math.max(minCols, Math.min(maxCols, item.cols + deltaCols));
        return { ...item, cols: nextCols };
      }
      return item;
    });

    saveLayout(updated);
  };

  // Map ordered presets
  const orderedPresetsWithLayout = layoutItems
    .map((item) => {
      const preset = presets.find((p) => p.id === item.id);
      return preset ? { preset, layout: item } : null;
    })
    .filter(Boolean) as { preset: PaginatedContainerPreset; layout: ContainerLayoutItem }[];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 items-start">
      {orderedPresetsWithLayout.map(({ preset, layout }) => {
        const isTarget = dragOverId === preset.id && draggedId !== preset.id;
        const isBeingDragged = draggedId === preset.id;

        return (
          <div
            key={preset.id}
            onDragOver={(e) => handleDragOver(preset.id, e)}
            onDrop={(e) => handleDrop(preset.id, e)}
            className={`transition-all duration-150 ${
              isBeingDragged ? "opacity-40 scale-[0.99]" : ""
            } ${isTarget ? "ring-2 ring-blue-500 rounded-2xl" : ""} ${
              layout.cols === 4
                ? "col-span-1 md:col-span-2 lg:col-span-4"
                : layout.cols === 3
                ? "col-span-1 md:col-span-2 lg:col-span-3"
                : layout.cols === 2
                ? "col-span-1 md:col-span-2"
                : "col-span-1"
            }`}
          >
            <ContainerEngine
              preset={preset}
              data={data}
              actions={actions}
              logs={logs}
              onClearLogs={onClearLogs}
              cols={layout.cols}
              rows={layout.rows}
              onResizeSpan={(delta) => handleResize(preset.id, delta)}
              dragHandleProps={{
                draggable: true,
                onDragStart: (e) => handleDragStart(preset.id, e),
                onDragEnd: handleDragEnd,
              }}
            />
          </div>
        );
      })}
    </div>
  );
};
