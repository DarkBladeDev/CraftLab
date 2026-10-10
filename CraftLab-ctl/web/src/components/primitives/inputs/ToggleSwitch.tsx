import React from "react";
import { ToggleSwitchInput, ContainerActionDispatcher } from "../../../types/presets";
import { checkRoleAccess } from "./rbacHelper";

interface ToggleSwitchProps {
  input: ToggleSwitchInput;
  actions: ContainerActionDispatcher;
  data?: any;
}

export const ToggleSwitch: React.FC<ToggleSwitchProps> = ({ input, actions, data }) => {
  const { authorized, reason } = checkRoleAccess(
    actions.user,
    input.requiredRoles,
    input.allowBreakGlass ?? true
  );

  const isChecked = typeof input.checked === "function" ? input.checked(data) : input.checked;
  const disabledByData = input.disabledIf ? input.disabledIf(data) : false;
  const isLoading = actions.isLoading(input.actionId);
  const isDisabled = !authorized || disabledByData || isLoading;

  const handleToggle = () => {
    if (isDisabled) return;
    actions.dispatch(input.actionId, !isChecked);
  };

  return (
    <div
      className={`flex items-center justify-between text-xs py-1 ${
        isDisabled ? "opacity-60" : ""
      }`}
      title={!authorized ? reason : undefined}
    >
      <div className="flex items-center gap-1.5">
        <span className="text-slate-300 font-medium">{input.label}</span>
        {!authorized && <span className="text-[10px] text-amber-300/80 font-mono">🔒</span>}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={isChecked}
        disabled={isDisabled}
        onClick={handleToggle}
        className={`w-10 h-5 flex items-center rounded-full p-0.5 transition-colors cursor-pointer ${
          isChecked ? "bg-emerald-500" : "bg-slate-700"
        } ${isDisabled ? "cursor-not-allowed" : ""}`}
      >
        <div
          className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
            isChecked ? "translate-x-5" : "translate-x-0"
          }`}
        />
      </button>
    </div>
  );
};
