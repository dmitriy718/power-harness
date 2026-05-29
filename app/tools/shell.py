import shlex
import subprocess
from typing import Tuple
from ..observability.logging import get_logger

logger = get_logger("tools.shell")

def run_shell(cmd: str, timeout: int = 30, dry_run: bool = True) -> Tuple[int, str]:
    logger.info("Shell command requested: %s", cmd)
    if dry_run:
        return 0, f"DRY-RUN: {cmd}"
    parts = shlex.split(cmd)
    try:
        out = subprocess.check_output(parts, stderr=subprocess.STDOUT, timeout=timeout, text=True)
        return 0, out
    except subprocess.CalledProcessError as e:
        return e.returncode, e.output
    except Exception as e:
        return 255, str(e)
