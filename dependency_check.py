"""First-run dependency checks for ReadOut.

The checks stay lightweight: no torch/kokoro imports, only module discovery and
PATH lookup. This lets startup explain missing prerequisites before model warmup
fails with a lower-level traceback.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib.util
import shutil
import sys
from typing import Callable, Iterable


SUPPORTED_PYTHON_MIN = (3, 10)
SUPPORTED_PYTHON_MAX_EXCLUSIVE = (3, 13)


@dataclass(frozen=True)
class DependencyIssue:
    id: str
    severity: str
    message: str
    fix: str

    def to_dict(self) -> dict:
        return asdict(self)


def _version_tuple(version_info) -> tuple[int, int]:
    return int(version_info[0]), int(version_info[1])


def _has_espeak_runtime(
    *,
    find_spec: Callable[[str], object | None],
    which: Callable[[str], str | None],
) -> bool:
    """Return true when Kokoro can reach eSpeak NG.

    Kokoro can use a system `espeak-ng` executable or the Python
    `espeakng_loader` package bundled into the PyInstaller app.
    """
    return which("espeak-ng") is not None or find_spec("espeakng_loader") is not None


def check_dependencies(
    *,
    version_info=None,
    find_spec: Callable[[str], object | None] | None = None,
    which: Callable[[str], str | None] | None = None,
) -> list[DependencyIssue]:
    """Return actionable dependency issues for the current runtime."""
    version_info = version_info or sys.version_info
    find_spec = find_spec or importlib.util.find_spec
    which = which or shutil.which

    issues: list[DependencyIssue] = []
    version = _version_tuple(version_info)

    if version < SUPPORTED_PYTHON_MIN or version >= SUPPORTED_PYTHON_MAX_EXCLUSIVE:
        issues.append(
            DependencyIssue(
                id="python-version",
                severity="error",
                message=(
                    f"Python {version[0]}.{version[1]} is not supported. "
                    "Kokoro requires Python 3.10-3.12."
                ),
                fix="Create a Python 3.10-3.12 virtualenv, then reinstall requirements.txt.",
            )
        )

    if find_spec("kokoro") is None:
        issues.append(
            DependencyIssue(
                id="kokoro-module",
                severity="error",
                message="The Kokoro Python package is not installed.",
                fix="Run `python -m pip install -r requirements.txt` inside the ReadOut virtualenv.",
            )
        )

    if not _has_espeak_runtime(find_spec=find_spec, which=which):
        issues.append(
            DependencyIssue(
                id="espeak-ng",
                severity="error",
                message="No eSpeak NG runtime was found for Kokoro.",
                fix=(
                    "Install requirements.txt so `espeakng_loader` is available, "
                    "or install system espeak-ng (`brew install espeak-ng` / Windows MSI)."
                ),
            )
        )

    return issues


def issues_to_dicts(issues: Iterable[DependencyIssue]) -> list[dict]:
    return [issue.to_dict() for issue in issues]


def format_dependency_report(issues: Iterable[DependencyIssue]) -> str:
    issues = list(issues)
    if not issues:
        return "ReadOut dependency check passed."

    lines = ["ReadOut dependency check found issues:"]
    for issue in issues:
        lines.append(f"- [{issue.severity}] {issue.message} Fix: {issue.fix}")
    return "\n".join(lines)
