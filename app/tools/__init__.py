from .registry import registry
from .filesystem import list_files, read_file, write_file
from .memory_tools import save_memory, search_memory, list_memory
from .shell import run_shell
from .safety import requires_approval, redact_output

registry.register("list_files", list_files)
registry.register("read_file", read_file)
registry.register("write_file", write_file)
registry.register("save_memory", save_memory)
registry.register("search_memory", search_memory)
registry.register("list_memory", list_memory)
registry.register("run_shell", run_shell)

__all__ = [
    "registry",
    "list_files",
    "read_file",
    "write_file",
    "save_memory",
    "search_memory",
    "list_memory",
    "run_shell",
    "requires_approval",
    "redact_output",
]
