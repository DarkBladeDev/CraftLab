import React, { useState } from "react";
import { TextInputInput, ContainerActionDispatcher } from "../../../types/presets";
import { checkRoleAccess } from "./rbacHelper";

interface TextInputProps {
  input: TextInputInput;
  actions: ContainerActionDispatcher;
  data?: any;
}

export const TextInput: React.FC<TextInputProps> = ({ input, actions }) => {
  const [val, setVal] = useState(input.initialValue || "");
  const { authorized, reason } = checkRoleAccess(
    actions.user,
    input.requiredRoles,
    input.allowBreakGlass ?? true
  );

  const isLoading = actions.isLoading(input.actionId);
  const isDisabled = !authorized || isLoading;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isDisabled || !val.trim()) return;
    actions.dispatch(input.actionId, val.trim());
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-1.5 text-xs">
      <div className="flex items-center justify-between text-slate-400">
        <span>{input.label}</span>
        {!authorized && (
          <span className="text-[10px] text-amber-300 font-mono" title={reason}>
            🔒 Restringido
          </span>
        )}
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          value={val}
          onChange={(e) => setVal(e.target.value)}
          placeholder={input.placeholder}
          disabled={isDisabled}
          className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 placeholder-slate-500 text-xs focus:outline-none focus:border-blue-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isDisabled || !val.trim()}
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium px-3 py-1.5 rounded-lg text-xs transition-colors cursor-pointer disabled:cursor-not-allowed"
        >
          {input.buttonLabel || "Enviar"}
        </button>
      </div>
    </form>
  );
};
