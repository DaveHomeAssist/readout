"""Checks for roadmap gate documentation artifacts."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_threat_model_covers_required_sections():
    text = (ROOT / "THREAT_MODEL.md").read_text(encoding="utf-8")
    for heading in [
        "## Assets",
        "## Actors",
        "## Trust Boundaries",
        "## Explicit Assumptions",
        "## Architect Sign-off",
    ]:
        assert heading in text
    assert "Origin guard rejects untrusted browser origins" in text
    assert "same-user no-Origin callers" in text


def test_release_checklist_has_security_test_and_packaging_gates():
    text = (ROOT / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    assert "## 2. Security Gate" in text
    assert "origin/main" in text
    assert r".\tools\release_preflight.ps1" in text
    assert r".\tools\release_preflight.ps1 -RunSourceSmoke" in text
    assert r".\tools\architect_signoff_check.ps1" in text
    assert r".\tools\packaging_validation_check.ps1" in text
    assert r".\tools\manual_smoke_check.ps1" in text
    assert r".\tools\roadmap_audit.ps1" in text
    assert r".\tools\secret_scan.ps1" in text
    assert r".\tools\extension_static_smoke.ps1" in text
    assert r".\tools\tk_desktop_static_smoke.ps1" in text
    assert "python -m pytest" in text
    assert "tests/test_live_http_smoke.py" in text
    assert "tests/test_server_cors.py" in text
    assert r".\tools\cors_origin_matrix.ps1" in text
    assert r".\tools\server_smoke.ps1" in text
    assert r".\tools\control_workflow_smoke.ps1" in text
    assert r".\tools\windows_packaging_prereqs.ps1" in text
    assert "./tools/mac_package_smoke.sh" in text
    assert r".\tools\windows_package_smoke.ps1" in text
    assert "package-smoke workflow" in text
    assert "Confirm `/config` responses redact" in text
    assert "## 4. macOS Build Gate" in text
    assert "## 5. Windows Build Gate" in text
    assert "Record build path" in text
    assert "ARCHITECT_SIGNOFF.md" in text
    assert "PACKAGING_VALIDATION.md" in text
    assert "MANUAL_SMOKE_VALIDATION.md" in text
    assert "UPSTREAM_RECONCILIATION.md" in text


def test_roadmap_status_tracks_every_workstream_item():
    text = (ROOT / "ROADMAP_STATUS.md").read_text(encoding="utf-8")
    for item_id in [
        "P0-A1",
        "P0-A2",
        "P0-A3",
        "P0-A4",
        "P1-A1",
        "P1-A2",
        "P1-A3",
        "P1-A4",
        "P1-A5",
        "P2-A1",
        "P2-A2",
        "P2-A3",
        "P2-A4",
        "P3-A1",
        "P3-A2",
        "P3-A3",
        "P3-A4",
    ]:
        assert f"| {item_id} |" in text

    assert "Current Blocking Conditions" in text
    assert "tools/roadmap_audit.ps1" in text
    assert "Architect sign-off" in text
    assert "Current Integration Risk" in text
    assert "origin/main" in text
    assert (
        "Hosted macOS package build, non-audio smoke, and clean-quit evidence exists"
        in text
    )
    assert "Hosted Windows package build and headless non-audio smoke evidence exists" in text


def test_readme_links_release_readiness_artifacts():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "engines/" in text
    assert "Voice and engine catalogue" in text
    assert "FEATURE-SPEC.md" in text
    assert "THREAT_MODEL.md" in text
    assert "ARCHITECT_SIGNOFF.md" in text
    assert "PACKAGING_VALIDATION.md" in text
    assert "MANUAL_SMOKE_VALIDATION.md" in text
    assert "NEXT_EXECUTOR_PROMPT.md" in text
    assert "RELEASE_CHECKLIST.md" in text
    assert "ROADMAP_STATUS.md" in text
    assert "UPSTREAM_RECONCILIATION.md" in text
    assert r".\tools\release_preflight.ps1" in text
    assert r".\tools\release_preflight.ps1 -RunSourceSmoke" in text
    assert r".\tools\architect_signoff_check.ps1" in text
    assert r".\tools\packaging_validation_check.ps1" in text
    assert r".\tools\manual_smoke_check.ps1" in text
    assert r".\tools\roadmap_audit.ps1" in text
    assert r".\tools\secret_scan.ps1" in text
    assert r".\tools\extension_static_smoke.ps1" in text
    assert r".\tools\tk_desktop_static_smoke.ps1" in text
    assert r".\tools\cors_origin_matrix.ps1" in text
    assert r".\tools\server_smoke.ps1" in text
    assert r".\tools\control_workflow_smoke.ps1" in text
    assert r".\tools\windows_packaging_prereqs.ps1" in text
    assert "./tools/mac_package_smoke.sh" in text
    assert r".\tools\windows_package_smoke.ps1" in text
    assert ".github/workflows/package-smoke.yml" in text


def test_next_executor_prompt_tracks_remaining_release_gates():
    text = (ROOT / "NEXT_EXECUTOR_PROMPT.md").read_text(encoding="utf-8")
    for required in [
        "roadmap-integration",
        "28062313500",
        "28062313482",
        "architect_signoff_check.ps1",
        "packaging_validation_check.ps1",
        "manual_smoke_check.ps1",
        "Tk desktop static smoke",
        "Menu-bar/tray icon visible",
        "Windows: verify audible preview/speak/stop lifecycle",
        "Do not install Python or `espeak-ng`",
        "Report GREEN only after",
    ]:
        assert required in text


def test_architect_signoff_packet_covers_pending_owner_decisions():
    text = (ROOT / "ARCHITECT_SIGNOFF.md").read_text(encoding="utf-8")
    for item_id in ["P0-A4", "P1-A2", "P1-A4", "P1-A5", "P2-A1", "P2-A4", "P3-A4"]:
        assert f"| {item_id} |" in text

    for artifact in [
        "THREAT_MODEL.md",
        "DECISION_LOG.md",
        "RELEASE_CHECKLIST.md",
        "ROADMAP_STATUS.md",
        "tools/release_preflight.ps1",
        "tools/architect_signoff_check.ps1",
        "tools/server_smoke.ps1",
        "tools/cors_origin_matrix.ps1",
        "hosted package-smoke evidence",
        "28062313500",
        "P3-A1 still needs manual macOS",
        "P3-A2 still needs manual Windows",
    ]:
        assert artifact in text


def test_packaging_validation_worksheet_covers_target_build_gates():
    text = (ROOT / "PACKAGING_VALIDATION.md").read_text(encoding="utf-8")
    for required in [
        "P3-A1 - macOS App Validation",
        "P3-A2 - Windows App Validation",
        r".\tools\packaging_validation_check.ps1",
        "./build_mac.sh",
        "./tools/mac_package_smoke.sh --app dist/ReadOut.app",
        r".\build_windows.ps1",
        r".\tools\windows_package_smoke.ps1 -ExePath dist\ReadOut\ReadOut.exe",
        "Release Evidence Summary",
        "Known Acceptable Gaps",
        ".github/workflows/package-smoke.yml",
    ]:
        assert required in text


def test_package_smoke_workflow_builds_and_smokes_both_targets():
    text = (ROOT / ".github" / "workflows" / "package-smoke.yml").read_text(encoding="utf-8")

    for required in [
        "workflow_dispatch",
        "roadmap-integration",
        "ReadOut.spec",
        "windows-latest",
        "macos-latest",
        "actions/setup-python@v5",
        'python-version: "3.12"',
        "eSpeak-NG.eSpeak-NG",
        "Get-Command espeak-ng.exe",
        "WinGet\\Packages",
        "$LASTEXITCODE",
        "set -eo pipefail",
        "chmod +x build_mac.sh",
        "brew install espeak-ng",
        ".\\build_windows.ps1",
        ".\\tools\\windows_package_smoke.ps1",
        "-TimeoutSec 90",
        "./build_mac.sh",
        "./tools/mac_package_smoke.sh --app dist/ReadOut.app",
        "actions/upload-artifact@v4",
        "readout-windows-package-smoke",
        "readout-macos-package-smoke",
    ]:
        assert required in text


def test_manual_smoke_validation_worksheet_covers_interactive_gates():
    text = (ROOT / "MANUAL_SMOKE_VALIDATION.md").read_text(encoding="utf-8")
    for required in [
        "Source Control Panel Smoke",
        "Automated Non-Audio Support Evidence",
        r".\tools\control_workflow_smoke.ps1",
        r".\tools\tk_desktop_static_smoke.ps1",
        r".\tools\tk_desktop_runtime_smoke.ps1",
        "Tk Desktop Smoke",
        "Chrome Extension Smoke",
        r".\tools\manual_smoke_check.ps1",
        "`/control` Preview Voice plays audio",
        "Tk desktop opens",
        "Popup shows READY",
        "Context menu Read aloud works",
        "Manual Smoke Summary",
    ]:
        assert required in text


def test_upstream_reconciliation_doc_tracks_remote_delta():
    text = (ROOT / "UPSTREAM_RECONCILIATION.md").read_text(encoding="utf-8")
    for required in [
        "origin/main",
        "roadmap-integration",
        "ahead=0; behind=0",
        "Do not run a blind pull",
        "Exact browser origins",
        "Tk remains available",
        r".\tools\upstream_reconciliation.ps1",
        "Target packaging validation remains separate",
    ]:
        assert required in text


def test_feature_spec_documents_current_security_and_engine_shape():
    text = (ROOT / "FEATURE-SPEC.md").read_text(encoding="utf-8")
    for required in [
        "engines/",
        "GET /voices",
        "allowed_origins",
        "TrustedHostMiddleware",
        "Recent-read history is off by default",
        "Known Release Blockers",
    ]:
        assert required in text
