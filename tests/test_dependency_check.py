"""Tests for first-run dependency diagnostics."""
from __future__ import annotations

import dependency_check


def test_main_startup_dependency_check_prints_report(monkeypatch, capsys):
    import main

    issue = dependency_check.DependencyIssue(
        id="python-version",
        severity="error",
        message="Python 3.13 is not supported.",
        fix="Use Python 3.12.",
    )
    monkeypatch.setattr(main, "check_dependencies", lambda: [issue])

    issues = main._check_startup_dependencies()

    assert issues == [issue]
    captured = capsys.readouterr()
    assert "Python 3.13 is not supported." in captured.err
    assert "Use Python 3.12." in captured.err


def test_dependency_check_passes_when_runtime_is_supported():
    issues = dependency_check.check_dependencies(
        version_info=(3, 12, 0),
        find_spec=lambda name: object(),
        which=lambda name: "C:/tools/espeak-ng.exe",
    )
    assert issues == []


def test_dependency_check_reports_python_kokoro_and_espeak():
    issues = dependency_check.check_dependencies(
        version_info=(3, 13, 0),
        find_spec=lambda name: None,
        which=lambda name: None,
    )

    ids = {issue.id for issue in issues}
    assert ids == {"python-version", "kokoro-module", "espeak-ng"}
    assert any("Python 3.13 is not supported" in issue.message for issue in issues)
    assert any("requirements.txt" in issue.fix for issue in issues)
    assert any("brew install espeak-ng" in issue.fix for issue in issues)


def test_format_dependency_report_is_actionable():
    issues = [
        dependency_check.DependencyIssue(
            id="kokoro-module",
            severity="error",
            message="The Kokoro Python package is not installed.",
            fix="Run pip install.",
        )
    ]

    report = dependency_check.format_dependency_report(issues)

    assert "ReadOut dependency check found issues" in report
    assert "The Kokoro Python package is not installed." in report
    assert "Run pip install." in report
