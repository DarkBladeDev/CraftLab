import inspect
from typing import Callable, Any, Dict, Optional, Type
from craftlab_ctl.core.models import DangerLevel


def _map_py_type_to_schema(annotation: Any) -> str:
    if annotation in (str, Optional[str]):
        return "string"
    elif annotation in (int, Optional[int]):
        return "integer"
    elif annotation in (bool, Optional[bool]):
        return "boolean"
    elif annotation in (float, Optional[float]):
        return "float"
    return "string"


def introspect_command_parameters(func: Callable) -> Dict[str, Any]:
    sig = inspect.signature(func)
    parameters = {}
    for param_name, param in sig.parameters.items():
        if param_name in ("self", "ctx"):
            continue

        param_type = _map_py_type_to_schema(param.annotation)
        is_required = param.default is inspect.Parameter.empty
        default_val = None if is_required else param.default

        parameters[param_name] = {
            "type": param_type,
            "required": is_required,
            "default": default_val,
        }
    return parameters


def command(
    mutates: bool = False,
    danger: DangerLevel = DangerLevel.SAFE,
    runs_in: str = "daemon",
    name: Optional[str] = None,
):
    def decorator(func: Callable):
        func.__is_craftctl_command__ = True
        func.__command_mutates__ = mutates
        func.__command_danger__ = danger
        func.__command_runs_in__ = runs_in
        func.__command_name__ = name or func.__name__
        func.__command_parameters__ = introspect_command_parameters(func)
        func.__command_doc__ = (func.__doc__ or "").strip()
        return func

    return decorator


def hook(event_name: str, priority: int = 100):
    def decorator(func: Callable):
        func.__is_craftctl_hook__ = True
        func.__hook_event__ = event_name
        func.__hook_priority__ = priority
        return func

    return decorator


def check(check_id: str):
    def decorator(func: Callable):
        func.__is_craftctl_check__ = True
        func.__check_id__ = check_id
        return func

    return decorator
