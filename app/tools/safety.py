import re
from typing import Any, Dict, List

from ..config import settings
from ..observability.logging import get_logger
from ..security.command_guard import is_command_safe

logger = get_logger("tools.safety")

SENSITIVE_PATTERNS = [
    re.compile(r"Bearer\s+[A-Za-z0-9\-\._~\+/=]+", re.IGNORECASE),
    re.compile(r"apikey=([A-Za-z0-9\-\._~\+/=]+)", re.IGNORECASE),
    re.compile(r"api_key=([A-Za-z0-9\-\._~\+/=]+)", re.IGNORECASE),
]

SAFE_TOOL_APPROVAL = {
    "run_shell": lambda args, kwargs: not is_command_safe(str(kwargs.get("cmd", args[0] if args else ""))),
    "write_file": lambda args, kwargs: True,
}


def requires_approval(tool_name: str, args: List[Any], kwargs: Dict[str, Any]) -> bool:
    if settings.allow_destructive:
        return False
    validator = SAFE_TOOL_APPROVAL.get(tool_name)
    if validator:
        return validator(args, kwargs)
    return False


def redact_output(output: Any) -> Any:
    if isinstance(output, str):
        redacted = output
        for pattern in SENSITIVE_PATTERNS:
            redacted = pattern.sub("[REDACTED]", redacted)
        return redacted
    if isinstance(output, tuple):
        return tuple(redact_output(item) for item in output)
    if isinstance(output, list):
        return [redact_output(item) for item in output]
    if isinstance(output, dict):
        return {key: redact_output(value) for key, value in output.items()}
    return output
