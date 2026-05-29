from app.tools import registry
from app.tools.filesystem import write_file
import pytest


def test_filesystem_write_and_read(tmp_path):
    p = tmp_path / "subdir"
    p.mkdir()
    fp = p / "note.txt"
    # use dry_run True to avoid writing
    res = write_file(str(fp.relative_to(tmp_path)), "hello", dry_run=True)
    assert "DRY-RUN" in res


def test_shell_tool_requires_approval_for_dangerous_command():
    with pytest.raises(PermissionError):
        registry.run("run_shell", "rm -rf /", dry_run=True)


def test_shell_tool_allows_safe_command():
    code, output = registry.run("run_shell", "echo hello", dry_run=True)
    assert code == 0
    assert "DRY-RUN" in output


def test_shell_tool_can_run_with_approval():
    code, output = registry.run("run_shell", "rm -rf /", approval=True, dry_run=True)
    assert code == 0
    assert "DRY-RUN" in output

