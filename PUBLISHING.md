# Publishing Guide

## PyPI Release Steps

1. Update version in both files:
   - `pyproject.toml` `version = "X.Y.Z"`
   - `src/glean_mcp/__init__.py` `__version__ = "X.Y.Z"`
2. (Optional) Update README release notes.
3. Commit and tag:
   ```bash
   git add pyproject.toml src/glean_mcp/__init__.py README.md
   git commit -m "release: vX.Y.Z"
   git tag -a vX.Y.Z -m "vX.Y.Z"
   git push origin main --tags
   ```
4. Build artifacts:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install --upgrade pip build twine
   python -m build
   twine check dist/*
   ```
5. Test upload:
   ```bash
   twine upload --repository testpypi dist/*
   pip install --index-url https://test.pypi.org/simple --no-deps glean-mcp==X.Y.Z
   ```
6. Real upload:
   ```bash
   twine upload dist/*
   ```

## GitHub Actions Automated Release

If you bump versions and push a tag `vX.Y.Z`, the workflow `.github/workflows/release.yml` will:
1. Verify `pyproject.toml` and `__init__` versions match the tag
2. Install dev extras & run tests (non-blocking if they fail currently)
3. Build sdist and wheel
4. Publish to PyPI using `PYPI_API_TOKEN` secret (must be an API token, not password)
5. Upload artifacts

Manual publish remains possible; automation is the preferred path once token is configured.

## Coordinated Docker + PyPI Release
1. Publish Python package first.
2. Build & push Docker image tagged `vX.Y.Z`.
3. Update README Latest Release section and GitHub Release notes referencing both artifacts.

## Future Automation
Add a GitHub Actions workflow triggered on tag push (`v*`) to:
- Build & publish wheel/sdist
- Push Docker image

Ask to generate a sample workflow if desired.
