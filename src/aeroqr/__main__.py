"""Allow ``python -m aeroqr`` to launch the application."""

from __future__ import annotations

from aeroqr.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
