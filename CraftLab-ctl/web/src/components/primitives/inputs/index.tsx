import React from "react";
import { InputPrimitive, ContainerActionDispatcher } from "../../../types/presets";
import { ActionButton } from "./ActionButton";
import { ToggleSwitch } from "./ToggleSwitch";
import { TextInput } from "./TextInput";
import { NumberStepper } from "./NumberStepper";
import { SelectDropdown } from "./SelectDropdown";

export { ActionButton, ToggleSwitch, TextInput, NumberStepper, SelectDropdown };

interface InputRendererProps {
  input: InputPrimitive;
  actions: ContainerActionDispatcher;
  data?: any;
}

export const InputRenderer: React.FC<InputRendererProps> = ({ input, actions, data }) => {
  switch (input.type) {
    case "button":
      return <ActionButton input={input} actions={actions} data={data} />;
    case "toggle":
      return <ToggleSwitch input={input} actions={actions} data={data} />;
    case "text_input":
      return <TextInput input={input} actions={actions} data={data} />;
    case "number_stepper":
      return <NumberStepper input={input} actions={actions} data={data} />;
    case "select":
      return <SelectDropdown input={input} actions={actions} data={data} />;
    default:
      return null;
  }
};
