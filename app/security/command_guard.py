from typing import List, Optional

DANGEROUS_KEYWORDS = ["rm", "shutdown", "reboot", "del ", "format "]

def is_command_safe(cmd: str, allowed_paths: Optional[List[str]] = None) -> bool:
    lc = cmd.lower()
    for k in DANGEROUS_KEYWORDS:
        if k in lc:
            return False
    return True
