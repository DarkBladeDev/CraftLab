import React, { useState } from "react";
import { SelectDropdownInput, ContainerActionDispatcher } from "../../../types/presets";
import { checkRoleAccess } from "./rbacHelper";

interface SelectDropdownProps {
  input: SelectDropdownInput;
  actions: ContainerActionDispatcher;
  data?: any;
}

export const SelectDropdown: React.FC<SelectDropdownProps> = ({ input, actions, data }) => {
  const options = typeof input.options === "function" ? input.options(data) : input.options;
  const [selected, setSelected] = useState<string>(options[0]?.value || "");

  const { authorized, reason } = checkRoleAccess(
    actions.user,
    input.requiredRoles,
    input.allowBreakGlass ?? true
  );

  const isLoading = actions.isLoading(input.actionId);
  const isDisabled = !authorized || isLoading || options.length === 0;

  const handleExecute = () => {
    if (isDisabled || !selected) return;
    actions.dispatch(input.actionId, selected);
  };

  return (
    <div className="flex flex-col gap-1.5 text-xs">
      <div className="flex items-center justify-between text-slate-400">
        <span>{input.label}</span>
        {!authorized && (
          <span className="text-[10px] text-amber-300 font-mono" title={reason}>
            🔒 Restricted
          </span>
        )}
      </div>
      <div className="flex gap-2">
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          disabled={isDisabled}
          className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 text-xs focus:outline-none focus:border-blue-500 disabled:opacity-50"
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={handleExecute}
          disabled={isDisabled || !selected}
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium px-3 py-1.5 rounded-lg text-xs transition-colors cursor-pointer disabled:cursor-not-allowed"
        >
          {input.buttonLabel || "Execute"}
        </button>
      </div>
    </div>
  );
};
