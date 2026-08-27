# Changelog

All notable changes to **AeroQR** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Audio feedback for rotation instructions.
- Distance estimation from QR size.
- Multiple QR tracking in a single frame.
- Recording mode for detection sessions.
- PyQt dashboard with live graphs.
- REST API mode.

## [1.0.0] - 2026-08-27

### Added
- Initial public release of the complete detection stack:
  - Real-time QR detection at 60+ FPS using a dedicated detector thread.
  - Multi-scale detection (6 scales) across 4 pre-processing strategies
    (grayscale, CLAHE, sharpen, Otsu).
  - Seed-image matching with exact and similarity-based payload comparison.
  - Automatic orientation calibration from 5 median-stabilised samples.
  - Orientation analysis with 10° tolerance and terminal + overlay feedback.
  - Kalman-style corner smoothing for stable tracking.
  - UDP drone control with throttled commands and prioritised navigation.
  - Camera auto-discovery with fallback to index 0.
- Professional project structure (`src/`) with a public Python API.
- `aeroqr` console command and `python -m aeroqr` entry points.
- Unit test suite (pytest) covering matching, geometry and drone control.
- CI/CD: lint, multi-platform multi-version tests, package build, GitHub
  Release and PyPI publishing workflows.
- Documentation: README, architecture, API reference, contributing guide,
  security policy and code of conduct.

### Security
- Documented the thin-trust model of the UDP drone command channel.

## Migration notes

The previously flat `Drone_QR_angular_BY_SABY.py` script has been replaced by
the installable `aeroqr` package. Run the app with:

```bash
python -m aeroqr
```

or, after installation:

```bash
aeroqr
```