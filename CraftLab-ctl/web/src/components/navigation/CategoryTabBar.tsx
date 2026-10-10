import React from "react";
import { CategoryDefinition } from "../../types/presets";

interface CategoryTabBarProps {
  categories: CategoryDefinition[];
  activeCategoryId: string;
  onSelectCategory: (categoryId: string) => void;
  categoryCounts?: Record<string, number>;
  onResetLayout?: () => void;
}

export const CategoryTabBar: React.FC<CategoryTabBarProps> = ({
  categories,
  activeCategoryId,
  onSelectCategory,
  categoryCounts,
  onResetLayout,
}) => {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800 mb-6">
      {/* Horizontal Category Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto py-1 max-w-full no-scrollbar">
        {categories.map((cat) => {
          const isActive = cat.id === activeCategoryId;
          const count = categoryCounts ? categoryCounts[cat.id] : undefined;

          return (
            <button
              key={cat.id}
              type="button"
              onClick={() => onSelectCategory(cat.id)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 cursor-pointer whitespace-nowrap select-none ${
                isActive
                  ? "bg-blue-600 text-white shadow-md shadow-blue-500/20"
                  : "bg-slate-900/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-slate-800/80"
              }`}
            >
              <span>{cat.label}</span>
              {count !== undefined && (
                <span
                  className={`text-[10px] font-mono px-1.5 py-0.2 rounded-full ${
                    isActive
                      ? "bg-blue-700/60 text-blue-100"
                      : "bg-slate-800 text-slate-400"
                  }`}
                >
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Action Utility (Reset Layout) */}
      {onResetLayout && (
        <button
          type="button"
          onClick={onResetLayout}
          className="text-xs text-slate-400 hover:text-slate-200 bg-slate-900/60 hover:bg-slate-800 border border-slate-800 px-3 py-1.5 rounded-xl transition-colors flex items-center gap-1.5 cursor-pointer ml-auto"
          title="Restaurar el orden y tamaño de paneles por defecto en esta categoría"
        >
          <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.047a1 1 0 011.885-.666A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566z"
              clipRule="evenodd"
            />
          </svg>
          <span>Reset Layout</span>
        </button>
      )}
    </div>
  );
};
