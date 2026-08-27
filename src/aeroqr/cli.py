"""Command line entry point for AeroQR."""

from __future__ import annotations

import argparse
from typing import Sequence

from aeroqr import __version__, config
from aeroqr.app import run


def build_parser() -> argparse.ArgumentParser:
    """Build the ``aeroqr`` command line interface."""
    parser = argparse.ArgumentParser(
        prog="aeroqr",
        description=(
            "AeroQR — real-time QR detection, seed matching and orientation "
            "tracking for drone applications (ISRO IROUC 2026)."
        ),
        epilog=(
            "In the video window: Q quits, L loads a new seed, R resets the "
            "matcher, D toggles drone control."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"AeroQR {__version__}"
    )
    parser.add_argument(
        "-c", "--camera", type=int, default=None,
        help="camera index to open (default: interactive prompt)",
    )
    parser.add_argument(
        "-s", "--seed", type=str, default=None,
        help="path to the seed QR image (default: file dialog)",
    )
    parser.add_argument(
        "-d", "--drone", action="store_const", const=True, default=None,
        help="enable drone control (default: interactive prompt)",
    )
    parser.add_argument(
        "--drone-ip", type=str, default=None,
        help=f"drone command IP address (default: {config.DEFAULT_DRONE_IP})",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point. Returns an exit code."""
    args = build_parser().parse_args(argv)
    return run(
        camera_index=args.camera,
        seed_path=args.seed,
        connect_drone=args.drone,
        drone_ip=args.drone_ip,
    )


if __name__ == "__main__":
    raise SystemExit(main())
