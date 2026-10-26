"""The ``nsres`` command.

WP-000 ships only ``--version`` and help. Each later work package adds its subcommand
(spec §10.13; plan §6, CLI surface).
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from nsres import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nsres",
        description="Narrative State Reconciliation Engine (NSRES-SPEC v0.1.1).",
    )
    parser.add_argument("--version", action="version", version=f"nsres {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    parser.print_help()
    return 0
