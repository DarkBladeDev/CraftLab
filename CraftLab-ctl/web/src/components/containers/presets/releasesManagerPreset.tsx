import React from "react";
import { PaginatedContainerPreset } from "../../../types/presets";

export const releasesManagerPreset: PaginatedContainerPreset = {
  id: "releases-manager",
  title: "Releases & Updates",
  category: "releases",
  defaultSpan: { cols: 2, rows: 1, minCols: 1, maxCols: 4 },
  paginationMode: "records",
  collection: {
    pageSize: 3,
    emptyMessage: "No installed releases recorded.",
    getItems: (data) => data.releasesInfo?.installed_releases || [],
    renderItem: (version: string, index: number, actions) => {
      return (
        <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
          <div className="flex items-center gap-2">
            <span className="font-mono font-bold text-slate-100">{version}</span>
            <span className="text-[10px] text-slate-500 font-sans">#release {index + 1}</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => actions.dispatch("rollback_release", version)}
              disabled={actions.isLoading("rollback_release") || !actions.user.roles.includes("admin")}
              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300 hover:text-white transition-colors cursor-pointer text-[11px]"
              title={
                !actions.user.roles.includes("admin")
                  ? "Requires admin role for rollback"
                  : "Roll back to this version"
              }
            >
              Rollback
            </button>
          </div>
        </div>
      );
    },
    footerInputs: [
      {
        type: "button",
        id: "btn-check-updates",
        label: "Check Updates",
        actionId: "check_updates",
        variant: "secondary",
      },
      {
        type: "toggle",
        id: "toggle-maintenance",
        label: "Maintenance Mode",
        actionId: "toggle_maintenance",
        checked: (data) => data.releasesInfo?.maintenance?.enabled ?? false,
        requiredRoles: ["admin", "operator"],
      },
      {
        type: "text_input",
        id: "input-target-version",
        label: "Target Version:",
        placeholder: "e.g. 0.6.1",
        buttonLabel: "Prepare & Apply",
        actionId: "apply_version",
        requiredRoles: ["admin"],
      },
    ],
  },
};
