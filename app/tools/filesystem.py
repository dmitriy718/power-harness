from pathlib import Path
from typing import List

ALLOWED_ROOT = Path.cwd()

def list_files(path: str, ext: str = "*") -> List[str]:
    p = (ALLOWED_ROOT / path).resolve()
    if not str(p).startswith(str(ALLOWED_ROOT)):
        raise PermissionError("path outside allowed root")
    return [str(x) for x in p.rglob(f"*.{ext}")]

def read_file(path: str) -> str:
    p = (ALLOWED_ROOT / path).resolve()
    if not str(p).startswith(str(ALLOWED_ROOT)):
        raise PermissionError("path outside allowed root")
    return p.read_text(encoding="utf-8")

def write_file(path: str, content: str, dry_run: bool = True) -> str:
    p = (ALLOWED_ROOT / path).resolve()
    if not str(p).startswith(str(ALLOWED_ROOT)):
        raise PermissionError("path outside allowed root")
    if dry_run:
        return f"DRY-RUN: would write {p}"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return str(p)
