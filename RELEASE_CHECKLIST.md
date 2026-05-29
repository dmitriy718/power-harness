Release checklist for Nova Agent Runtime

This checklist helps coordinate releases and ensures builds, tests, and artifacts are produced consistently.

1. Prepare
   - Update `CHANGELOG.md` with user-facing changes and migration notes.
   - Bump project version in `pyproject.toml` (or other release manifest).

2. Local verification
   - Run full test suite and linters locally:

```powershell
.venv\Scripts\python -m pip install -r requirements.txt -r requirements-dev.txt
.venv\Scripts\ruff check .
.venv\Scripts\python -m mypy app
.venv\Scripts\pytest -q
```

3. Build artifacts
   - (Optional) Build a wheel and sdist:

```powershell
python -m pip install build
python -m build
```

4. Tag and push
   - Create an annotated git tag (use semantic version):

```powershell
git add -A
git commit -m "Release vX.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin main --tags
```

5. GitHub Release
   - Draft a GitHub release from the tag, attach build artifacts if needed, and paste the changelog entry.

6. Publish packages (if applicable)
   - Upload to PyPI (ensure credentials are configured):

```powershell
python -m pip install --upgrade twine
python -m twine upload dist/*
```

7. Docker image (optional)
   - Build and push Docker image with appropriate tags.

8. Post-release
   - Update `CHANGELOG.md` release header to include link to GitHub Release.
   - Create a PR for any post-release housekeeping (update docs, bump branch version, etc.).

9. Verify CI status
   - Confirm the `.github/workflows/ci.yml` build completed successfully on the release commit/tag.

Notes
- If your repository is private or uses a different branch, adapt the commands accordingly.
- For reproducible releases, run CI and verify the artifacts produced by the workflow before publishing.
