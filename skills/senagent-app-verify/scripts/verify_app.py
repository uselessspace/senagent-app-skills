"""Reference acceptance gate for trusted SenAgent apps, not a security sandbox.

POSIX developer hosts only. No publish, credentials, or live model calls.
Run --help for the command-line contract. The CLI prefix is a JSON argv array.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import selectors
import signal
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import IO

PROTOCOL = "senagent.application-verification-report.v1"
COMMON = {
    "static.application",
    "static.backend-implementation",
    "verification.source-stable",
    "smoke.startup",
    "smoke.readiness",
    "smoke.liveness",
    "smoke.instance-initialize",
    "smoke.instance-idempotency",
    "smoke.instance-delete",
    "smoke.process-cleanup",
    "smoke.log",
}
LANGUAGE = {
    "python": {
        "build.python-version",
        "build.python-uv",
        "build.python-files",
        "build.python-dependencies",
        "build.python-checks",
    },
    "go": {
        "build.go-version",
        "build.go-files",
        "build.go-dependencies",
        "build.go-checks",
        "build.go-artifact",
    },
}
REPORT_FIELDS = {
    "protocol",
    "generated_at",
    "runtime_version",
    "profile",
    "status",
    "achieved_level",
    "application_root",
    "source_digest",
    "application_id",
    "application_version",
    "backend_language",
    "backend_build_system",
    "log_path",
    "checks",
}
CHECK_FIELDS = {"id", "status", "message", "command", "exit_code", "duration_ms"}
CHECK_REQUIRED_FIELDS = {"id", "status", "message"}
MAX_CLI_OUTPUT_BYTES = 2_000_000


class _RunnerExecutionError(RuntimeError):
    def __init__(self, *, cleanup_succeeded: bool) -> None:
        super().__init__("verification CLI monitoring failed")
        self.cleanup_succeeded = cleanup_succeeded


def _load_json(raw: bytes | str) -> object:
    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate_json_key")
            result[key] = value
        return result

    def reject_non_finite(_value: str) -> object:
        raise ValueError("non_finite_json_number")

    return json.loads(raw, object_pairs_hook=reject_duplicate_keys, parse_constant=reject_non_finite)


def _process_group_exists(process_group: int) -> bool:
    try:
        os.killpg(process_group, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _stop_process_group(process: subprocess.Popen[bytes], grace_seconds: float = 5) -> bool:
    """Stop and reap this runner's exact process group."""
    if not _process_group_exists(process.pid):
        return process.poll() is not None
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except PermissionError:
        return False
    except ProcessLookupError:
        return process.poll() is not None
    deadline = time.monotonic() + grace_seconds
    if process.poll() is None:
        try:
            process.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            pass
    while _process_group_exists(process.pid) and time.monotonic() < deadline:
        time.sleep(0.05)
    if _process_group_exists(process.pid):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except PermissionError:
            return False
        except ProcessLookupError:
            pass
    if process.poll() is None:
        try:
            process.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            return False
    return not _process_group_exists(process.pid)


def _run_cli(command: list[str], cwd: Path, timeout_seconds: int) -> tuple[int | None, bytes, str | None, bool]:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    assert process.stdout is not None and process.stderr is not None
    streams = (process.stdout, process.stderr)
    for stream in streams:
        os.set_blocking(stream.fileno(), False)
    captured = bytearray()
    total_output = 0
    eof: set[int] = set()
    failure: str | None = None
    deadline = time.monotonic() + timeout_seconds
    try:
        with selectors.DefaultSelector() as selector:
            for stream in streams:
                selector.register(stream, selectors.EVENT_READ)
            registered = set(range(len(streams)))
            while process.poll() is None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    failure = "timeout"
                    break
                wait_seconds = min(remaining, 0.05)
                if registered:
                    selector.select(timeout=wait_seconds)
                else:
                    try:
                        process.wait(timeout=wait_seconds)
                    except subprocess.TimeoutExpired:
                        pass
                total_output, exceeded = _drain_cli_output(streams, captured, eof, total_output)
                for index in eof & registered:
                    selector.unregister(streams[index])
                registered -= eof
                if exceeded:
                    failure = "output_limit"
                    break
            if process.poll() is not None and failure is None:
                total_output, exceeded = _drain_cli_output(streams, captured, eof, total_output)
                if exceeded:
                    failure = "output_limit"

        group_alive = _process_group_exists(process.pid)
        detached_writer = process.poll() is not None and not group_alive and len(eof) != len(streams)
        if failure is None and (group_alive or detached_writer):
            failure = "process_leak"
        cleanup_succeeded = True
        if failure is not None:
            cleanup_succeeded = _stop_process_group(process) and not detached_writer
        return process.poll(), bytes(captured), failure, cleanup_succeeded
    except Exception as exc:
        try:
            cleanup_succeeded = _stop_process_group(process)
        except Exception:
            cleanup_succeeded = False
        raise _RunnerExecutionError(cleanup_succeeded=cleanup_succeeded) from exc
    except BaseException:
        try:
            _stop_process_group(process)
        except Exception:
            pass
        raise
    finally:
        for stream in streams:
            stream.close()


def _drain_cli_output(
    streams: tuple[IO[bytes], IO[bytes]],
    captured: bytearray,
    eof: set[int],
    total_output: int,
) -> tuple[int, bool]:
    for index, stream in enumerate(streams):
        if index in eof:
            continue
        while True:
            try:
                chunk = os.read(stream.fileno(), 65_536)
            except BlockingIOError:
                break
            if not chunk:
                eof.add(index)
                break
            remaining = max(0, MAX_CLI_OUTPUT_BYTES - total_output)
            if index == 0 and remaining:
                captured.extend(chunk[:remaining])
            total_output += len(chunk)
            if total_output > MAX_CLI_OUTPUT_BYTES:
                return total_output, True
    return total_output, False


def evaluate_report(report: object, exit_code: int, root: Path, required_checks: set[str] | None = None) -> dict:
    """Check observable CLI evidence; do not infer semantic/business readiness."""
    if not isinstance(report, dict):
        raise ValueError("report_not_object")
    if set(report) != REPORT_FIELDS:
        raise ValueError("invalid_report_fields")
    if report.get("protocol") != PROTOCOL:
        raise ValueError("unsupported_report_protocol")
    generated_at = report.get("generated_at")
    try:
        parsed_generated_at = datetime.fromisoformat(generated_at) if isinstance(generated_at, str) else None
    except ValueError as exc:
        raise ValueError("invalid_generated_at") from exc
    if parsed_generated_at is None or parsed_generated_at.utcoffset() is None:
        raise ValueError("invalid_generated_at")
    runtime_version = report.get("runtime_version")
    if not isinstance(runtime_version, str) or not 1 <= len(runtime_version) <= 64:
        raise ValueError("invalid_runtime_version")
    if report.get("profile") != "full":
        raise ValueError("full_profile_required")
    if report.get("status") not in {"passed", "failed"}:
        raise ValueError("invalid_report_status")
    if report.get("achieved_level") not in {"none", "structure_valid", "runtime_ready", "function_ready"}:
        raise ValueError("invalid_achieved_level")
    if report.get("application_root") != str(root.resolve()):
        raise ValueError("application_root_mismatch")
    for field, limit in (("application_id", 64), ("application_version", 32)):
        value = report.get(field)
        if not isinstance(value, str) or not 1 <= len(value) <= limit:
            raise ValueError(f"invalid_{field}")
    language = report.get("backend_language")
    if language not in LANGUAGE:
        raise ValueError("unsupported_language")
    if report.get("backend_build_system") != {"python": "uv", "go": "go_modules"}[language]:
        raise ValueError("backend_build_system_mismatch")
    log_path = report.get("log_path")
    if log_path is not None and (not isinstance(log_path, str) or not 1 <= len(log_path) <= 4096):
        raise ValueError("invalid_log_path")
    checks = report.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("missing_checks")
    indexed: dict[str, str] = {}
    for check in checks:
        if not isinstance(check, dict):
            raise ValueError("invalid_check")
        if not CHECK_REQUIRED_FIELDS <= set(check) <= CHECK_FIELDS:
            raise ValueError("invalid_check_fields")
        check_id, status = check.get("id"), check.get("status")
        if not isinstance(check_id, str) or not re.fullmatch(r"[a-z][a-z0-9._-]{0,95}", check_id):
            raise ValueError("invalid_check_id")
        if check_id in indexed or status not in {"passed", "failed", "skipped"}:
            raise ValueError("duplicate_or_invalid_check")
        message = check.get("message")
        if not isinstance(message, str) or not 1 <= len(message) <= 4000:
            raise ValueError("invalid_check_message")
        command = check.get("command", [])
        if not isinstance(command, list) or len(command) > 64 or any(not isinstance(part, str) for part in command):
            raise ValueError("invalid_check_command")
        check_exit_code = check.get("exit_code")
        if check_exit_code is not None and (not isinstance(check_exit_code, int) or isinstance(check_exit_code, bool)):
            raise ValueError("invalid_check_exit_code")
        duration_ms = check.get("duration_ms", 0)
        if not isinstance(duration_ms, int) or isinstance(duration_ms, bool) or duration_ms < 0:
            raise ValueError("invalid_check_duration")
        if status == "passed" and check_exit_code not in {None, 0}:
            raise ValueError("passed_check_has_nonzero_exit")
        indexed[check_id] = status
    requested = required_checks or set()
    if any(not isinstance(key, str) or re.fullmatch(r"[a-z][a-z0-9._-]{0,95}", key) is None for key in requested):
        raise ValueError("invalid_required_check")
    required = COMMON | LANGUAGE[language] | requested
    blocked = sorted(key for key in required if indexed.get(key) != "passed")
    for phase in ("build", "smoke"):
        aggregate = f"{phase}.surfaces"
        granular = [key for key in indexed if key.startswith(f"{phase}.surface.")]
        if aggregate in indexed:
            if indexed[aggregate] != "skipped" or granular:
                blocked.append(f"{phase}.surface-evidence")
        elif not granular:
            blocked.append(f"{phase}.surface-evidence")
        else:
            blocked.extend(key for key in granular if indexed[key] != "passed")
    blocked.sort()
    failed = sorted(key for key, value in indexed.items() if value == "failed")
    digest = report.get("source_digest")
    valid_digest = isinstance(digest, str) and re.fullmatch(r"[a-f0-9]{64}", digest) is not None
    passed = (
        exit_code == 0
        and report.get("status") == "passed"
        and report.get("achieved_level") == "runtime_ready"
        and valid_digest
        and not blocked
        and not failed
    )
    return {
        "protocol": "senagent.skill-local-gate.example.v1",
        "status": "passed" if passed else "failed",
        "local_runtime_verified": bool(passed),
        "business_acceptance": "not_run",
        "live_model_acceptance": "not_run",
        "target_install_acceptance": "not_run",
        "source_digest": digest if valid_digest else None,
        "failed_checks": failed,
        "missing_or_unpassed_required_checks": blocked,
        "skipped_checks": sorted(key for key, value in indexed.items() if value == "skipped"),
        "cli_exit_code": exit_code,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("application_root", type=Path)
    parser.add_argument("--cli-json", default='["senagent"]', help="JSON array; never a shell command")
    parser.add_argument("--report", required=True, type=Path, help="New file outside the application tree")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--require-check", action="append", default=[])
    args = parser.parse_args()
    if args.application_root.is_symlink():
        parser.error("application root must not be a symbolic link")
    root = args.application_root.resolve()
    output = args.report.resolve()
    prefix = json.loads(args.cli_json)
    if os.name != "posix":
        parser.error("This reference runner supports macOS/Linux only")
    if not (root / "application.yaml").is_file():
        parser.error("application.yaml is required")
    if output.is_relative_to(root) or not output.parent.is_dir():
        parser.error("report must have an existing parent outside the application tree")
    if not isinstance(prefix, list) or not prefix or any(not isinstance(s, str) or not s for s in prefix):
        parser.error("--cli-json must be a nonempty string array")
    if args.timeout <= 0:
        parser.error("timeout must be positive")
    # Reserve before executing app-owned code; never overwrite an existing report.
    with output.open("x", encoding="utf-8") as destination:
        output.chmod(0o600)
        result: dict[str, object] = {"status": "failed", "reason": "runner_error"}
        with tempfile.TemporaryDirectory(prefix="senagent-skill-verify-") as verification_dir:
            try:
                code, raw, failure, cleanup_succeeded = _run_cli(
                    prefix
                    + [
                        "app",
                        "verify",
                        str(root),
                        "--profile",
                        "full",
                        "--format",
                        "json",
                        "--cache-dir",
                        str(Path(verification_dir) / "cache"),
                    ],
                    Path(verification_dir),
                    args.timeout,
                )
                if failure is not None:
                    result = {
                        "status": "failed",
                        "reason": failure if cleanup_succeeded else "cleanup_failed",
                        "cleanup_review_required": True,
                    }
                else:
                    assert code is not None
                    result = evaluate_report(_load_json(raw), code, root, set(args.require_check))
            except _RunnerExecutionError as exc:
                result = {
                    "status": "failed",
                    "reason": "execution_error" if exc.cleanup_succeeded else "cleanup_failed",
                    "cleanup_review_required": True,
                }
            except (OSError, ValueError, TypeError):
                # Never copy raw command output or exception text that may contain secrets.
                result = {"status": "failed", "reason": "invalid_report_or_execution_error"}
        destination.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
