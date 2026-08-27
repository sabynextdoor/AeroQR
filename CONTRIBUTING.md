# Contributing to AeroQR

First off — thank you for taking the time to contribute! AeroQR is a research
challenge project, and every contribution helps push it closer to production
quality.

## Table of contents

- [Code of conduct](#code-of-conduct)
- [Getting started](#getting-started)
- [Development environment](#development-environment)
- [Project layout](#project-layout)
- [Coding standards](#coding-standards)
- [Testing](#testing)
- [Opening a pull request](#opening-a-pull-request)

## Code of conduct

This project and everyone participating in it is governed by the
[Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to
uphold this code.

## Getting started

1. Fork the repository on GitHub.
2. Clone your fork locally:

   ```bash
   git clone https://github.com/<your-username>/AeroQR.git
   cd AeroQR
   ```

3. Add the upstream remote for reference:

   ```bash
   git remote add upstream https://github.com/sabynextdoor/AeroQR.git
   ```

## Development environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -e ".[dev]"
pre-commit install
```

## Project layout

```
src/aeroqr/    # the package (one module per responsibility)
tests/         # pytest tests (mirror the package layout)
docs/          # extended documentation
.github/       # CI/CD and issue templates
```

## Coding standards

- Target Python **3.8+** with `from __future__ import annotations`.
- Follow **PEP 8**; AeroQR uses **ruff** as its single source of truth
  (see `pyproject.toml`). Run `ruff check .` and `ruff format --check .`.
- Keep modules focused: no 800-line files, one class/concern per module.
- Keep the detection pipeline deterministic — never depend on wall-clock
  ordering between `WebcamStream`, `QRWorker` and the main loop.
- Do not add new runtime dependencies without a strong reason; add them to
  `pyproject.toml` `dependencies`, not just `requirements.txt`.

## Testing

Run the full suite locally:

```bash
pytest
```

Add tests for every new behaviour. Tests that need a real camera are
out of scope for CI — isolate pure logic (matching, geometry, controller
decisions) in testable units instead.

## Opening a pull request

1. Create a feature branch from `main`:

   ```bash
   git checkout -b feature/amazing-feature
   ```

2. Make your changes and add tests.
3. Run checks locally so CI stays green:

   ```bash
   ruff check .
   pytest
   ```

4. Commit with a clear message and push:

   ```bash
   git push origin feature/amazing-feature
   ```

5. Open a pull request against `main` and fill in the template.

Thank you for helping make AeroQR better!