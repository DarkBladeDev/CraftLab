import React from "react";
import { ActionButtonInput, ContainerActionDispatcher } from "../../../types/presets";
import { checkRoleAccess } from "./rbacHelper";

const variantStyles = {
  primary: "bg-blue-600 hover:bg-blue-500 text-white shadow-sm",
  secondary: "bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700",
  danger: "bg-rose-600 hover:bg-rose-500 text-white shadow-sm",
  warning: "bg-amber-600 hover:bg-amber-500 text-white shadow-sm",
  outline: "bg-transparent hover:bg-slate-800 text-slate-300 border border-slate-700",
};

interface ActionButtonProps {
  input: ActionButtonInput;
  actions: ContainerActionDispatcher;
  data?: any;
}

export const ActionButton: React.FC<ActionButtonProps> = ({ input, actions, data }) => {
  const { authorized, reason } = checkRoleAccess(
    actions.user,
    input.requiredRoles,
    input.allowBreakGlass ?? true
  );

  const disabledByData = input.disabledIf ? input.disabledIf(data) : false;
  const isLoading = actions.isLoading(input.loadingIfAction || input.actionId);
  const isDisabled = !authorized || disabledByData || isLoading;

  const handleClick = async () => {
    if (isDisabled) return;
    if (input.confirmMessage && !window.confirm(input.confirmMessage)) {
      return;
    }
    await actions.dispatch(input.actionId);
  };

  const variantClass = variantStyles[input.variant || "secondary"];

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isDisabled}
      title={!authorized ? reason : undefined}
      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center justify-center gap-1.5 cursor-pointer ${variantClass} ${
        isDisabled ? "opacity-50 cursor-not-allowed filter grayscale-[30%]" : "active:scale-[0.98]"
      }`}
    >
      {isLoading ? (
        <>
          <span className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
          <span>Executing...</span>
        </>
      ) : (
        <span>{input.label}</span>
      )}
      {!authorized && (
        <span className="text-[10px] text-amber-300/80 font-mono ml-0.5">🔒</span>
      )}
    </button>
  );
};
