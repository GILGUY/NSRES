"""NSRES: Narrative State Reconciliation Engine (reference implementation of NSRES-SPEC v0.1.1)."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("nsres")
except PackageNotFoundError:  # pragma: no cover - only when running from an uninstalled tree
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
