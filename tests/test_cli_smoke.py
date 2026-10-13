"""Smoke tests for SecondBrain CLI."""

from __future__ import annotations

import pytest

from secondbrain import __version__
from secondbrain.cli import SUBCOMMANDS, main


def test_cli_version(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that sb --version outputs the version string."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert __version__ in output


def test_cli_help_lists_commands(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that sb --help lists all six subcommands."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    expected_commands = ("capture", "find", "open", "verify", "backup", "restore")
    for cmd in expected_commands:
        assert cmd in captured.out


def test_cli_backup_missing_config_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that sb backup without configured backup root exits with code 2."""
    with pytest.raises(SystemExit) as exc_info:
        main(["backup"])
    assert exc_info.value.code == 2


def test_cli_restore_missing_args_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that sb restore without args exits with code 2."""
    with pytest.raises(SystemExit) as exc_info:
        main(["restore"])
    assert exc_info.value.code == 2


def test_cli_capture_no_target_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that invoking sb capture without a target exits with code 2."""
    with pytest.raises(SystemExit) as exc_info:
        main(["capture"])
    assert exc_info.value.code == 2


def test_cli_parse_failure_honours_json(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that argparse failures honour --json and include results in error envelope."""
    import json

    with pytest.raises(SystemExit) as exc_info:
        main(["--json", "capture"])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "error"
    assert data["results"] == []
    assert len(data["errors"]) >= 1


def test_cli_no_args_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that invoking sb without subcommands prints help and exits with code 2."""
    with pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code == 2


def test_python_m_secondbrain_execution() -> None:
    """Regression test: executing python -m secondbrain must invoke CLI via __main__.py."""
    import subprocess
    import sys

    res = subprocess.run(
        [sys.executable, "-m", "secondbrain", "--version"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert __version__ in res.stdout


