"""The network-import check in scripts/verify_package.py catches a planted import (plan A-13)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


def _load_verify_package() -> ModuleType:
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec = importlib.util.spec_from_file_location(
            "verify_package", SCRIPTS / "verify_package.py"
        )
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(SCRIPTS))


def test_planted_network_imports_are_found(tmp_path: Path) -> None:
    verify = _load_verify_package()
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "clean.py").write_text("import json\nfrom pathlib import Path\n", encoding="utf-8")
    (package / "planted.py").write_text(
        "import urllib.request\nfrom http import client\nfrom . import clean\n", encoding="utf-8"
    )
    hits = verify.find_network_imports(package)
    assert len(hits) == 2
    assert any(hit.endswith(": urllib.request") for hit in hits)
    assert any(hit.endswith(": http") for hit in hits)


def test_real_package_has_no_network_imports() -> None:
    verify = _load_verify_package()
    assert verify.find_network_imports(Path(verify.SRC_PACKAGE)) == []
