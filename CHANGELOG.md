# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2025-08-14
### Added
- Automated Docker image build & push to GHCR on tagged release (`v*`) with version and `latest` tags.

### Changed
- Aligned semantic versioning between Python package and Docker image (jump from 1.7.1 package draft to 2.0.0 for unified baseline).
- Bumped `mcp` dependency floor to `>=1.10.0,<2.0.0` (security fixes) in earlier 0.x release now formalized as part of 2.0.0 stable line.

### Notes
- No breaking API changes relative to 1.7.1 code; major version chosen to synchronize ecosystems and reserve 1.x gap.
- Future releases: tag with `vX.Y.Z` to publish both PyPI artifact and Docker images `ghcr.io/<repo>:X.Y.Z` + `latest`.

## [1.7.1]
- Internal alignment step (not published to PyPI) prior to unified 2.0.0 release.

## [0.1.3]
- Security dependency bump and minor packaging fixes.

