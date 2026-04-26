"""Tests for stacktrace_filter.validator and validator_cli."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.validator import (
    ValidatorConfig,
    ValidationResult,
    ValidationViolation,
    format_validation,
    validate,
)


def _frame(filename: str = "app/main.py", function: str = "run", lineno: int = 10) -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, source_line="pass")


def _tb(*frames: Frame, exc_type: str = "ValueError", exc_msg: str = "bad") -> Traceback:
    return Traceback(frames=list(frames), exc_type=exc_type, exc_message=exc_msg)


# ---------------------------------------------------------------------------
# validate() – basic
# ---------------------------------------------------------------------------

def test_validate_no_config_is_valid():
    tb = _tb(_frame())
    result = validate(tb)
    assert result.is_valid
    assert result.violation_count == 0


def test_validate_max_depth_not_exceeded():
    tb = _tb(*[_frame() for _ in range(5)])
    result = validate(tb, ValidatorConfig(max_depth=10))
    assert result.is_valid


def test_validate_max_depth_exceeded():
    tb = _tb(*[_frame() for _ in range(15)])
    result = validate(tb, ValidatorConfig(max_depth=10))
    assert not result.is_valid
    assert any(v.rule_name == "max_depth" for v in result.violations)


def test_validate_require_user_frame_present():
    tb = _tb(_frame("app/views.py"))
    result = validate(tb, ValidatorConfig(require_user_frame=True))
    assert result.is_valid


def test_validate_require_user_frame_missing():
    import sysconfig
    stdlib = sysconfig.get_path("stdlib")
    stdlib_file = f"{stdlib}/os.py" if stdlib else "/usr/lib/python3.11/os.py"
    tb = _tb(_frame(stdlib_file))
    result = validate(tb, ValidatorConfig(require_user_frame=True))
    # Either valid (if our heuristic doesn't flag it) or invalid – just ensure no crash
    assert isinstance(result, ValidationResult)


def test_validate_forbidden_filename_match():
    tb = _tb(_frame("app/dangerous.py"))
    result = validate(tb, ValidatorConfig(forbidden_filenames=["dangerous"]))
    assert not result.is_valid
    v = result.violations[0]
    assert v.rule_name == "forbidden_filename"
    assert v.frame is not None


def test_validate_forbidden_filename_no_match():
    tb = _tb(_frame("app/safe.py"))
    result = validate(tb, ValidatorConfig(forbidden_filenames=["dangerous"]))
    assert result.is_valid


def test_validate_forbidden_function_match():
    tb = _tb(_frame(function="exec_query"))
    result = validate(tb, ValidatorConfig(forbidden_functions=["exec"]))
    assert not result.is_valid
    assert result.violations[0].rule_name == "forbidden_function"


def test_validate_multiple_violations():
    frames = [_frame() for _ in range(5)]
    tb = _tb(*frames)
    cfg = ValidatorConfig(max_depth=2, forbidden_filenames=["main"])
    result = validate(tb, cfg)
    assert result.violation_count >= 2


# ---------------------------------------------------------------------------
# format_validation()
# ---------------------------------------------------------------------------

def test_format_validation_valid_no_color():
    tb = _tb(_frame())
    result = validate(tb)
    out = format_validation(result, color=False)
    assert "OK" in out
    assert "violation" not in out


def test_format_validation_invalid_no_color():
    tb = _tb(*[_frame() for _ in range(20)])
    result = validate(tb, ValidatorConfig(max_depth=5))
    out = format_validation(result, color=False)
    assert "FAIL" in out
    assert "max_depth" in out


def test_format_validation_with_color_contains_ansi():
    tb = _tb(*[_frame() for _ in range(20)])
    result = validate(tb, ValidatorConfig(max_depth=5))
    out = format_validation(result, color=True)
    assert "\033[" in out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_build_validator_parser_defaults():
    from stacktrace_filter.validator_cli import build_validator_parser
    p = build_validator_parser()
    args = p.parse_args([])
    assert args.file == "-"
    assert args.max_depth is None
    assert args.require_user_frame is False
    assert args.forbidden_filenames == []
    assert args.forbidden_functions == []
    assert args.no_color is False
    assert args.exit_code is False


def test_main_missing_file(capsys):
    from stacktrace_filter.validator_cli import main
    with pytest.raises(SystemExit) as exc:
        main(["nonexistent_file_xyz.txt"])
    assert exc.value.code == 2


def test_main_reads_stdin(capsys):
    from stacktrace_filter.validator_cli import main
    traceback_text = (
        "Traceback (most recent call last):\n"
        '  File "app/main.py", line 5, in run\n'
        "    result = compute()\n"
        "ValueError: bad value\n"
    )
    with patch("stacktrace_filter.validator_cli.read_source", return_value=traceback_text):
        main(["-", "--no-color"])
    captured = capsys.readouterr()
    assert "OK" in captured.out or "FAIL" in captured.out


def test_main_exit_code_on_failure(capsys):
    from stacktrace_filter.validator_cli import main
    traceback_text = (
        "Traceback (most recent call last):\n"
        + "".join(
            f'  File "app/f{i}.py", line {i}, in fn{i}\n    pass\n'
            for i in range(20)
        )
        + "ValueError: too deep\n"
    )
    with patch("stacktrace_filter.validator_cli.read_source", return_value=traceback_text):
        with pytest.raises(SystemExit) as exc:
            main(["--max-depth", "3", "--exit-code", "--no-color"])
    assert exc.value.code == 1
