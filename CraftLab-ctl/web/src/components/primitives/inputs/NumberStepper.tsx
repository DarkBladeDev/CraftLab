import React, { useState } from "react";
import { NumberStepperInput, ContainerActionDispatcher } from "../../../types/presets";
import { checkRoleAccess } from "./rbacHelper";

interface NumberStepperProps {
  input: NumberStepperInput;
  actions: ContainerActionDispatcher;
  data?: any;
}

export const NumberStepper: React.FC<NumberStepperProps> = ({ input, actions }) => {
  const [val, setVal] = useState<number>(input.initialValue ?? 0);
  const step = input.step ?? 1;
  const min = input.min ?? -Infinity;
  const max = input.max ?? Infinity;

  const { authorized, reason } = checkRoleAccess(
    actions.user,
    input.requiredRoles,
    input.allowBreakGlass ?? true
  );

  const isLoading = actions.isLoading(input.actionId);
  const isDisabled = !authorized || isLoading;

  const handleStep = (delta: number) => {
    if (isDisabled) return;
    const next = Math.max(min, Math.min(max, val + delta));
    setVal(next);
    actions.dispatch(input.actionId, next);
  };

  return (
    <div className="flex items-center justify-between text-xs py-1">
      <div className="flex items-center gap-1.5 text-slate-300">
        <span>{input.label}</span>
        {!authorized && <span className="text-[10px] text-amber-300 font-mono" title={reason}>🔒</span>}
      </div>
      <div className="flex items-center gap-1 bg-slate-900 border border-slate-700 rounded-lg p-0.5">
        <button
          type="button"
          onClick={() => handleStep(-step)}
          disabled={isDisabled || val <= min}
          className="w-6 h-6 flex items-center justify-center rounded text-slate-300 hover:bg-slate-800 disabled:opacity-40"
        >
          -
        </button>
        <span className="w-10 text-center font-mono font-medium text-slate-100">
          {val}
        </span>
        <button
          type="button"
          onClick={() => handleStep(step)}
          disabled={isDisabled || val >= max}
          className="w-6 h-6 flex items-center justify-center rounded text-slate-300 hover:bg-slate-800 disabled:opacity-40"
        >
          +
        </button>
      </div>
    </div>
  );
};
