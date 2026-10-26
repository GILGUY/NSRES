"""WP-000 unit smoke tests: the package imports and reports the installed version."""

from importlib.metadata import version

import pytest

import nsres
from nsres.cli.main import main


def test_version_matches_installed_metadata() -> None:
    assert nsres.__version__ == version("nsres")


def test_cli_version_flag_prints_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"nsres {nsres.__version__}"


def test_cli_without_arguments_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "usage: nsres" in capsys.readouterr().out
