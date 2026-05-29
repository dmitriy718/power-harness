from typing import Callable, Dict, Any
from ..observability.logging import get_logger
from .safety import requires_approval, redact_output

logger = get_logger("tools.registry")

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Callable[..., Any]] = {}

    def register(self, name: str, fn: Callable[..., Any]):
        logger.debug("Registering tool %s", name)
        self.tools[name] = fn

    def run(self, name: str, *args, **kwargs):
        if name not in self.tools:
            raise KeyError(f"Tool {name} not found")
        approval = bool(kwargs.pop("approval", False) or kwargs.pop("_approval", False))
        if requires_approval(name, list(args), kwargs) and not approval:
            logger.warning("Tool %s requires approval", name)
            raise PermissionError(f"Tool {name} requires approval before execution")
        logger.info("Running tool %s", name)
        result = self.tools[name](*args, **kwargs)
        return redact_output(result)

registry = ToolRegistry()
