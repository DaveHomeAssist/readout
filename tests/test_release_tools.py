"""Checks for release helper scripts."""
from __future__ import annotations

import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _powershell_exe() -> str:
    exe = (
        shutil.which("pwsh.exe")
        or shutil.which("pwsh")
        or shutil.which("powershell.exe")
        or shutil.which("powershell")
    )
    if not exe:
        pytest.skip("PowerShell is not available")
    return exe


def _run_ps_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    exe = _powershell_exe()
    command = [exe, "-NoProfile"]
    if Path(exe).name.lower().startswith("powershell"):
        command += ["-ExecutionPolicy", "Bypass"]
    command += ["-File", str(ROOT / "tools" / script), *args]
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)


def _combined_output(result: subprocess.CompletedProcess[str]) -> str:
    return f"{result.stdout}\n{result.stderr}"


@pytest.fixture
def workspace_tmp_dir():
    path = ROOT / ".tmp-release-gate-tests"
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir()
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_server_smoke_script_is_non_audio_and_non_mutating_by_default():
    text = (ROOT / "tools" / "server_smoke.ps1").read_text(encoding="utf-8")

    assert "GET /status" in text
    assert "GET /voices" in text
    assert "GET /history" in text
    assert "GET /control" in text
    assert "primary macOS control surface" in text
    assert "Speak + Save WAV" in text
    assert "POST /preview" in text
    assert '$preview.status -eq "playing"' in text
    assert "POST /speak" in text
    assert '$speak.status -eq "playing"' in text
    assert "POST /stop after speak" in text
    assert "AudioTimeoutSec" in text
    assert "if ($IncludeAudio)" in text
    assert "PATCH" not in text
    assert "DELETE" not in text
    assert "exit 1" in text


def test_control_workflow_smoke_is_stateful_but_restores_local_files():
    text = (ROOT / "tools" / "control_workflow_smoke.ps1").read_text(encoding="utf-8")

    for required in [
        "/status",
        "/control",
        "/config",
        "/history",
        "/stop",
        "history_enabled",
        "history_limit",
        "ReadAllBytes",
        "WriteAllBytes",
        "Restore-File",
        "Restore local config/history",
        "Refusing stateful smoke against non-loopback host",
        "Remove-Item",
        "exit 1",
    ]:
        assert required in text


def test_control_browser_runtime_smoke_renders_control_status_without_audio():
    text = (ROOT / "tools" / "control_browser_runtime_smoke.ps1").read_text(encoding="utf-8")

    for required in [
        "Start-Process",
        "-WindowStyle Hidden",
        "uvicorn",
        "server:app",
        "Chrome or Edge was not found",
        "--headless=new",
        "--virtual-time-budget=5000",
        "--dump-dom",
        "/control",
        "/status",
        "Refusing browser runtime smoke against non-loopback host",
        "A server is already responding",
        "statusLabel",
        "feedback",
        "/control status display updates",
        "Remove-Item",
        "exit 1",
    ]:
        assert required in text


def test_control_browser_action_smoke_clicks_playback_actions_with_restore():
    text = (ROOT / "tools" / "control_browser_action_smoke.ps1").read_text(encoding="utf-8")

    for required in [
        "Start-Process",
        "-WindowStyle Hidden",
        "uvicorn",
        "server:app",
        "Chrome or Edge was not found",
        "--headless=new",
        "--remote-debugging-port",
        "ClientWebSocket",
        "Runtime.evaluate",
        "/control",
        "/status",
        "/config",
        "previewBtn",
        "speakBtn",
        "saveBtn",
        "stopBtn",
        "Preview playing.",
        "Playing",
        "/control Preview Voice action",
        "/control Speak action",
        "Saved to ",
        "Saved WAV file exists",
        "Playback stopped.",
        "ReadAllBytes",
        "WriteAllBytes",
        "Restore local config/history",
        "Remove-Item",
        "exit 1",
    ]:
        assert required in text


def test_extension_static_smoke_covers_manifest_and_endpoint_contracts():
    text = (ROOT / "tools" / "extension_static_smoke.ps1").read_text(encoding="utf-8")

    for required in [
        "manifest_version",
        "contextMenus",
        "activeTab",
        "scripting",
        "Least privilege: no storage permission",
        "http://localhost:7778/*",
        "background.js",
        "popup.html",
        "btn-preview",
        "Read Selection",
        "`${READOUT_URL}/status`",
        "`${READOUT_URL}/voices`",
        "`${READOUT_URL}/preview`",
        "`${READOUT_URL}/speak`",
        "`${READOUT_URL}/stop`",
        "`${READOUT_URL}/config`",
        "readout-speak-save",
        "readout-toast",
        "exit 1",
    ]:
        assert required in text


def test_extension_runtime_smoke_loads_popup_and_restores_local_files():
    text = (ROOT / "tools" / "extension_runtime_smoke.ps1").read_text(encoding="utf-8")

    for required in [
        "Start-Process",
        "-WindowStyle Hidden",
        "uvicorn",
        "server:app",
        "Chrome or Edge was not found",
        "--remote-debugging-port",
        "Extensions.loadUnpacked",
        "Extensions.triggerAction",
        "Load unpacked extension",
        "Popup OFFLINE state",
        "Popup READY state",
        "Popup Preview action",
        "Context menu Read aloud action",
        "Popup Stop action",
        "stopPlayback",
        "handleContextMenuClick",
        "Get-ServiceWorkerWebSocketUrl",
        "service_worker",
        "Extension origin allowlisted",
        "ReadAllBytes",
        "WriteAllBytes",
        "Restore local config/history",
        "A server is already responding",
        "exit 1",
    ]:
        assert required in text


def test_tk_desktop_static_smoke_covers_desktop_controls_and_endpoint_contracts():
    text = (ROOT / "tools" / "tk_desktop_static_smoke.ps1").read_text(encoding="utf-8")

    for required in [
        "class ReadOutApp(tk.Tk):",
        "BASE_URL",
        '"kokoro":',
        '"openai":',
        '"elevenlabs":',
        '"browser":',
        "Unsupported browser engine absent",
        "Preview Voice",
        "Save WAV",
        "_patch(\"/config\", payload)",
        "payload = {\"engine\": key}",
        "payload[\"voice\"] = voice_id",
        "self._patch_config({\"voice\": voice_id})",
        "self._patch_config({\"speed\": v})",
        "_get(\"/voices\")",
        "_get(\"/status\")",
        "_post(\"/preview\"",
        "_post(\"/speak\"",
        "_post(\"/stop\", timeout=10)",
        "save true payload",
        "Auto-read control absent",
        "exit 1",
    ]:
        assert required in text


def test_tk_desktop_runtime_smoke_opens_tk_and_restores_local_files():
    text = (ROOT / "tools" / "tk_desktop_runtime_smoke.ps1").read_text(encoding="utf-8")

    for required in [
        "Start-Process",
        "-WindowStyle Hidden",
        "uvicorn",
        "server:app",
        "Tk desktop UI currently targets localhost:7778",
        "A server is already responding",
        "ReadAllBytes",
        "WriteAllBytes",
        "Restore-File",
        "Restore local config/history",
        "ReadOutApp._poll_status = lambda self: None",
        "winfo_ismapped",
        "_select_engine(\"openai\")",
        "_select_voice(\"nova\")",
        "_on_speed_change",
        "Desktop engine persists",
        "Desktop voice persists",
        "Desktop speed persists",
        "pending_callbacks",
        "Desktop Preview Voice action",
        "Desktop Speak action",
        "Desktop Save WAV action",
        "Desktop Stop action",
        "exit 1",
    ]:
        assert required in text


def test_cors_matrix_script_covers_required_phase0_cases():
    text = (ROOT / "tools" / "cors_origin_matrix.ps1").read_text(encoding="utf-8")

    assert "curl.exe" in text
    assert "no-origin status" in text
    assert "allowed local status" in text
    assert "allowed local config preflight" in text
    assert "blocked evil status" in text
    assert "blocked evil stop" in text
    assert "AllowedExtensionOrigin" in text
    assert "Access-Control-Allow-Origin" in text
    assert "exit 1" in text


def test_release_preflight_summarizes_artifacts_prereqs_and_optional_checks():
    text = (ROOT / "tools" / "release_preflight.ps1").read_text(encoding="utf-8")

    for required in [
        "THREAT_MODEL.md",
        "FEATURE-SPEC.md",
        "UPSTREAM_RECONCILIATION.md",
        "ARCHITECT_SIGNOFF.md",
        "PACKAGING_VALIDATION.md",
        "MANUAL_SMOKE_VALIDATION.md",
        "NEXT_EXECUTOR_PROMPT.md",
        "RELEASE_CHECKLIST.md",
        "ROADMAP_STATUS.md",
        "MILESTONE_LOG.md",
        "ReadOut.spec",
        "build_windows.ps1",
        "build_mac.sh",
        "tools\\secret_scan.ps1",
        "tools\\architect_signoff_check.ps1",
        "tools\\packaging_validation_check.ps1",
        "tools\\manual_smoke_check.ps1",
        "tools\\roadmap_audit.ps1",
        "tools\\upstream_reconciliation.ps1",
        "tools\\mac_package_smoke.sh",
        "tools\\cors_origin_matrix.ps1",
        "tools\\server_smoke.ps1",
        "tools\\control_workflow_smoke.ps1",
        "tools\\control_browser_runtime_smoke.ps1",
        "tools\\control_browser_action_smoke.ps1",
        "tools\\extension_static_smoke.ps1",
        "tools\\extension_runtime_smoke.ps1",
        "tools\\tk_desktop_static_smoke.ps1",
        "tools\\tk_desktop_runtime_smoke.ps1",
        "tools\\windows_packaging_prereqs.ps1",
        "tools\\windows_package_smoke.ps1",
    ]:
        assert required in text

    assert "Python 3.10-3.12" in text
    assert "eSpeak NG runtime" in text
    assert "espeakng_loader" in text
    assert "Get-PackagingEvidence" in text
    assert "Hosted/target evidence recorded" in text
    assert "Git upstream currency" in text
    assert "safe.directory=$script:GitSafeDirectory" in text
    assert "rev-list" in text
    assert "--left-right" in text
    assert "--count" in text
    assert "Upstream reconciliation" in text
    assert "upstream_reconciliation.ps1 exit=$exitCode vs $UpstreamRef" in text
    assert "-Upstream $UpstreamRef -Quiet" in text
    assert "$trackingBranch" in text
    assert "Secret scan" in text
    assert "Extension static smoke" in text
    assert "Tk desktop static smoke" in text
    assert "Invoke-PreflightCommand" in text
    assert "extension_static_smoke.ps1 exit=$exitCode" in text
    assert "tk_desktop_static_smoke.ps1 exit=$exitCode" in text
    assert "-Quiet" in text
    assert "Architect sign-off" in text
    assert "architect_signoff_check.ps1" in text
    assert "Packaging validation evidence" in text
    assert "packaging_validation_check.ps1" in text
    assert "Manual smoke evidence" in text
    assert "manual_smoke_check.ps1" in text
    assert "RunPytest" in text
    assert "RunSourceSmoke" in text
    assert "Source live HTTP smoke" in text
    assert "tests/test_live_http_smoke.py" in text
    assert "RunLiveChecks" in text
    assert "server_smoke.ps1" in text
    assert "cors_origin_matrix.ps1" in text
    assert "Live control workflow smoke" in text
    assert "control_workflow_smoke.ps1 exit=$exitCode" in text
    assert "exit 1" in text


def test_windows_packaging_prereq_report_is_non_mutating_and_actionable():
    text = (ROOT / "tools" / "windows_packaging_prereqs.ps1").read_text(encoding="utf-8")

    for required in [
        "ReadOut Windows packaging prerequisite report",
        "Python 3.10-3.12",
        "Python.Python.3.12",
        "eSpeak NG runtime",
        "espeakng-loader",
        "dist\\ReadOut\\ReadOut.exe",
        "windows_package_smoke.ps1",
        "Quiet",
        "exit 1",
    ]:
        assert required in text

    for forbidden in [
        "pip install",
        "-m venv",
        "-m PyInstaller",
        "Start-Process",
        "Remove-Item",
    ]:
        assert forbidden not in text


def test_upstream_reconciliation_helper_is_report_only():
    text = (ROOT / "tools" / "upstream_reconciliation.ps1").read_text(encoding="utf-8")

    assert "HEAD...$Upstream" in text
    assert "safe.directory=$script:GitSafeDirectory" in text
    assert "@GitArgs" in text
    assert "rev-list" in text
    assert "diff\", \"--name-status\"" in text
    assert "log\", \"--oneline\"" in text
    assert "Runtime-sensitive upstream paths" in text
    assert "UPSTREAM_RECONCILIATION.md" in text
    assert "Quiet" in text
    assert "Result -ne \"PASS\"" in text
    assert "exit 1" in text

    for forbidden in ["fetch", "pull", "merge", "rebase", "reset", "checkout", "restore"]:
        assert f'"{forbidden}"' not in text.lower()


def test_roadmap_audit_helper_rolls_up_release_gates_without_mutation():
    text = (ROOT / "tools" / "roadmap_audit.ps1").read_text(encoding="utf-8")

    for required in [
        "ROADMAP_STATUS.md",
        "P0-A1",
        "P3-A4",
        "architect_signoff_check.ps1",
        "packaging_validation_check.ps1",
        "manual_smoke_check.ps1",
        "Python 3.10-3.12",
        "eSpeak NG runtime",
        "espeakng_loader",
        "Upstream graph",
        "safe.directory=$script:GitSafeDirectory",
        "Next Action",
        "exit 1",
    ]:
        assert required in text

    for forbidden in ["fetch", "pull", "merge", "rebase", "reset", "checkout", "build_mac.sh", "build_windows.ps1"]:
        assert f'"{forbidden}"' not in text.lower()


def test_architect_signoff_check_requires_acceptance_without_revise():
    text = (ROOT / "tools" / "architect_signoff_check.ps1").read_text(encoding="utf-8")

    for item_id in ["P0-A4", "P1-A2", "P1-A4", "P1-A5", "P2-A1", "P2-A4", "P3-A4"]:
        assert item_id in text

    assert "ARCHITECT_SIGNOFF.md" in text
    assert "Accept is not checked" in text
    assert "Revise is checked" in text
    assert "Both Accept and Revise are checked" in text
    assert "Quiet" in text
    assert "exit 1" in text


def test_packaging_validation_check_requires_target_evidence():
    text = (ROOT / "tools" / "packaging_validation_check.ps1").read_text(encoding="utf-8")

    for required in [
        "PACKAGING_VALIDATION.md",
        "P3-A1 macOS packaging",
        "P3-A2 Windows packaging",
        "P3-A4 release checklist accepted",
        "tools/mac_package_smoke.sh",
        "tools\\windows_package_smoke.ps1",
        "ACCEPTED GAP",
        "Result must be PASS",
        "with evidence",
        "Packaging validation file not found",
        "Quiet",
        "exit 1",
    ]:
        assert required in text


def test_manual_smoke_check_requires_interactive_evidence():
    text = (ROOT / "tools" / "manual_smoke_check.ps1").read_text(encoding="utf-8")

    for required in [
        "MANUAL_SMOKE_VALIDATION.md",
        "Source `/control` manual smoke",
        "Tk desktop manual smoke",
        "Chrome extension manual smoke",
        "Popup shows READY",
        "Context menu Read aloud works",
        "ACCEPTED GAP",
        "Result must be PASS",
        "with evidence",
        "Manual smoke validation file not found",
        "Quiet",
        "exit 1",
    ]:
        assert required in text


def test_architect_signoff_check_behaviour(workspace_tmp_dir):
    rows = "\n".join(
        f"| {item_id} | Decision | Evidence | [ ] | [ ] | |"
        for item_id in ["P0-A4", "P1-A2", "P1-A4", "P1-A5", "P2-A1", "P2-A4", "P3-A4"]
    )
    unsigned = workspace_tmp_dir / "unsigned.md"
    unsigned.write_text(
        "# Sign-off\n\n"
        "| ID | Decision / Gate | Evidence | Accept | Revise | Notes |\n"
        "|---|---|---|---|---|---|\n"
        f"{rows}\n",
        encoding="utf-8",
    )

    result = _run_ps_script("architect_signoff_check.ps1", "-Path", str(unsigned))
    output = _combined_output(result)
    assert result.returncode == 1
    assert "P0-A4" in output
    assert "Accept is not checked" in output

    accepted_rows = "\n".join(
        f"| {item_id} | Decision | Evidence | [x] | [ ] | Accepted by Architect |"
        for item_id in ["P0-A4", "P1-A2", "P1-A4", "P1-A5", "P2-A1", "P2-A4", "P3-A4"]
    )
    accepted = workspace_tmp_dir / "accepted.md"
    accepted.write_text(
        "# Sign-off\n\n"
        "| ID | Decision / Gate | Evidence | Accept | Revise | Notes |\n"
        "|---|---|---|---|---|---|\n"
        f"{accepted_rows}\n",
        encoding="utf-8",
    )

    result = _run_ps_script("architect_signoff_check.ps1", "-Path", str(accepted), "-Quiet")
    output = _combined_output(result)
    assert result.returncode == 0
    assert output.strip() == ""

    revise = workspace_tmp_dir / "revise.md"
    revise.write_text(
        accepted.read_text(encoding="utf-8").replace("| P2-A4 | Decision | Evidence | [x] | [ ] |", "| P2-A4 | Decision | Evidence | [x] | [x] |"),
        encoding="utf-8",
    )
    result = _run_ps_script("architect_signoff_check.ps1", "-Path", str(revise))
    output = _combined_output(result)
    assert result.returncode == 1
    assert "Both Accept and Revise are checked" in output


def test_packaging_validation_check_behaviour(workspace_tmp_dir):
    pending = workspace_tmp_dir / "pending.md"
    pending.write_text((ROOT / "PACKAGING_VALIDATION.md").read_text(encoding="utf-8"), encoding="utf-8")

    result = _run_ps_script("packaging_validation_check.ps1", "-Path", str(pending))
    output = _combined_output(result)
    assert result.returncode == 1
    assert "`./build_mac.sh` completed" in output
    assert "Menu-bar/tray icon visible" in output
    assert "Current: Pending manual" in output

    complete = workspace_tmp_dir / "complete.md"
    complete.write_text(
        textwrap.dedent(
            """\
            # Packaging Validation

            | Check | Result | Notes |
            |---|---|---|
            | `ARCHITECT_SIGNOFF.md` reviewed | PASS | Architect accepted all rows |
            | `.\\tools\\release_preflight.ps1` or target equivalent run | PASS | preflight transcript attached |
            | Python 3.10-3.12 confirmed | PASS | Python 3.12.4 |
            | `espeak-ng` confirmed on PATH | PASS | espeak-ng 1.52 |
            | Full test suite run | PASS | 135 passed |

            | Check | Result | Evidence |
            |---|---|---|
            | `./build_mac.sh` completed | PASS | dist/ReadOut.app built |
            | `dist/ReadOut.app` exists | PASS | Finder and ls confirmed |
            | `tools/mac_package_smoke.sh` passed | PASS | smoke transcript attached |
            | Menu-bar/tray icon visible | ACCEPTED GAP | Architect accepted remote CI screenshot gap |
            | Tray `Open Control Panel` opens `/control` | PASS | manual smoke transcript |
            | macOS preview/speak/stop lifecycle verified | PASS | manual audio smoke transcript |
            | App quits cleanly | PASS | smoke script stopped app |

            | Check | Result | Evidence |
            |---|---|---|
            | `.\\build_windows.ps1` completed | PASS | dist\\ReadOut\\ReadOut.exe built |
            | `dist\\ReadOut\\ReadOut.exe` exists | PASS | Test-Path confirmed |
            | `tools\\windows_package_smoke.ps1` passed | PASS | smoke transcript attached |
            | Server starts on `127.0.0.1:7778` | PASS | /status returned 200 |
            | `/control` opens and displays controls | PASS | manual browser smoke |
            | Windows preview/speak/stop lifecycle verified | PASS | manual audio smoke transcript |
            | App process stops cleanly | PASS | smoke script stopped process |

            | Item | Status | Notes |
            |---|---|---|
            | P3-A1 macOS packaging | PASS | macOS worksheet complete |
            | P3-A2 Windows packaging | PASS | Windows worksheet complete |
            | P3-A4 release checklist accepted | PASS | Architect accepted checklist |
            """
        ),
        encoding="utf-8",
    )

    result = _run_ps_script("packaging_validation_check.ps1", "-Path", str(complete), "-Quiet")
    output = _combined_output(result)
    assert result.returncode == 0
    assert output.strip() == ""

    no_evidence = workspace_tmp_dir / "no-evidence.md"
    no_evidence.write_text(complete.read_text(encoding="utf-8").replace("| `./build_mac.sh` completed | PASS | dist/ReadOut.app built |", "| `./build_mac.sh` completed | PASS | |"), encoding="utf-8")
    result = _run_ps_script("packaging_validation_check.ps1", "-Path", str(no_evidence))
    output = _combined_output(result)
    assert result.returncode == 1
    assert "`./build_mac.sh` completed" in output
    assert "with evidence" in output


def test_manual_smoke_check_behaviour(workspace_tmp_dir):
    pending = workspace_tmp_dir / "manual-pending.md"
    pending.write_text((ROOT / "MANUAL_SMOKE_VALIDATION.md").read_text(encoding="utf-8"), encoding="utf-8")

    result = _run_ps_script("manual_smoke_check.ps1", "-Path", str(pending))
    output = _combined_output(result)
    assert result.returncode == 0
    assert "`/control` Preview Voice plays audio" in output
    assert "Chrome extension manual smoke | PASS" in output

    complete = workspace_tmp_dir / "manual-complete.md"
    complete.write_text(
        textwrap.dedent(
            """\
            # Manual Smoke

            | Check | Result | Evidence |
            |---|---|---|
            | `/control` opens on `127.0.0.1:7778` | PASS | browser smoke transcript |
            | `/control` status display updates | PASS | READY and loading observed |
            | `/control` Preview Voice plays audio | PASS | audio heard on speakers |
            | `/control` Speak text works | PASS | speech heard |
            | `/control` Speak + Save WAV creates WAV | PASS | WAV file inspected |
            | `/control` Stop playback works | PASS | playback stopped |
            | `/control` history toggle and Clear History work | PASS | history cleared |
            | Tk desktop opens on supported non-macOS target or `READOUT_FORCE_TK=1` | ACCEPTED GAP | Architect accepted macOS-only release target |
            | Desktop engine, voice, and speed controls persist through backend config | PASS | config changed and survived restart |
            | Desktop Preview Voice plays audio | PASS | audio heard |
            | Desktop Speak, Save WAV, and Stop work | PASS | desktop smoke transcript |
            | Extension origin added to `allowed_origins` | PASS | config row captured |
            | Popup shows READY when server is up | PASS | screenshot captured |
            | Popup shows OFFLINE or next action when server is down | PASS | screenshot captured |
            | Popup Preview Voice works | PASS | audio heard |
            | Context menu Read aloud works on selected page text | PASS | selected text spoken |
            | Extension Stop playback works | PASS | playback stopped |

            | Item | Status | Notes |
            |---|---|---|
            | Source `/control` manual smoke | PASS | source control panel complete |
            | Tk desktop manual smoke | ACCEPTED GAP | macOS-only release accepted |
            | Chrome extension manual smoke | PASS | extension smoke complete |
            """
        ),
        encoding="utf-8",
    )

    result = _run_ps_script("manual_smoke_check.ps1", "-Path", str(complete), "-Quiet")
    output = _combined_output(result)
    assert result.returncode == 0
    assert output.strip() == ""

    no_evidence = workspace_tmp_dir / "manual-no-evidence.md"
    no_evidence.write_text(
        complete.read_text(encoding="utf-8").replace(
            "| Popup shows READY when server is up | PASS | screenshot captured |",
            "| Popup shows READY when server is up | PASS | |",
        ),
        encoding="utf-8",
    )
    result = _run_ps_script("manual_smoke_check.ps1", "-Path", str(no_evidence))
    output = _combined_output(result)
    assert result.returncode == 1
    assert "Popup shows READY when server is up" in output
    assert "with evidence" in output


def test_roadmap_audit_current_blocker_behaviour():
    result = _run_ps_script("roadmap_audit.ps1")
    output = _combined_output(result)

    assert result.returncode == 1
    assert "ReadOut roadmap audit" in output
    assert "Roadmap item coverage | PASS" in output
    assert "Upstream graph |" in output
    assert "Architect sign-off | PASS" in output
    assert "Packaging validation | FAIL" in output
    assert "Manual smoke validation | PASS" in output


def test_windows_package_smoke_validates_packaged_exe_lifecycle():
    text = (ROOT / "tools" / "windows_package_smoke.ps1").read_text(encoding="utf-8")

    assert "dist\\ReadOut\\ReadOut.exe" in text
    assert "Start-Process" in text
    assert "Stop-Process" in text
    assert "--headless" in text
    assert "--no-browser" in text
    assert "RedirectStandardOutput" in text
    assert "Get-LogTail" in text
    assert "ExitCode" in text
    assert "dependency_issues" in text
    assert "load_error" in text
    assert "GET /status" not in text  # implementation probes the URL, output stays operator-oriented
    assert "/status" in text
    assert "server_smoke.ps1" in text
    assert "cors_origin_matrix.ps1" in text
    assert "A server is already responding" in text
    assert "IncludeAudio" in text
    assert "AudioTimeoutSec" in text
    assert "SkipCors" in text
    assert "exit 1" in text


def test_mac_package_smoke_validates_packaged_app_lifecycle():
    text = (ROOT / "tools" / "mac_package_smoke.sh").read_text(encoding="utf-8")

    assert "dist/ReadOut.app" in text
    assert "open -n" in text
    assert "osascript" in text
    assert "App quits cleanly" in text
    assert "wait_for_app_shutdown" in text
    assert "pgrep" in text
    assert "/status" in text
    assert "/voices" in text
    assert "/history" in text
    assert "/control" in text
    assert "primary macOS control surface" in text
    assert "Speak + Save WAV" in text
    assert "/preview" in text
    assert "/speak" in text
    assert "/stop" in text
    assert "POST /stop after preview" in text
    assert "POST /stop after speak" in text
    assert "status=playing" in text
    assert "INCLUDE_AUDIO" in text
    assert "SKIP_CORS" in text
    assert "https://evil.com" in text
    assert "exit \"$FAILED\"" in text


def test_secret_scan_targets_provider_key_literals():
    text = (ROOT / "tools" / "secret_scan.ps1").read_text(encoding="utf-8")

    assert "OpenAI API key literal" in text
    assert "ElevenLabs API key literal" in text
    assert "Committed provider key value" in text
    assert "openai_api_key|elevenlabs_api_key" in text
    assert ".git" in text
    assert "dist" in text
    assert "Secret scan | PASS" in text
    assert "Quiet" in text
    assert "exit 1" in text


def test_requirements_pin_torch_below_frozen_runtime_regression():
    text = (ROOT / "requirements.txt").read_text(encoding="utf-8")

    assert "torch>=2.10,<2.12" in text
    assert "c10.dll" in text
    assert "en_core_web_sm-3.8.0-py3-none-any.whl" in text
