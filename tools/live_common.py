from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://127.0.0.1:8080"
PORT = 8080
EXPECTED_ALIAS = "Qwen3.8-27B-AD-IQ2_S.gguf"
EXPECTED_BUILD = "b10434-7e4c0a968"
EXPECTED_CONTEXT = 25088
EXPECTED_MAIN_LAYERS = 66


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def require_clean_tree() -> None:
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    if status:
        raise RuntimeError(f"worktree is not clean:\n{status}")


def port_open(port: int = PORT) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.25)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def active_llama_server_pids() -> list[int]:
    if sys.platform != "win32":
        return []
    output = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq llama-server.exe", "/FO", "CSV", "/NH"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    found: list[int] = []
    for row in csv.reader(io.StringIO(output)):
        if len(row) >= 2 and row[0].lower() == "llama-server.exe":
            found.append(int(row[1]))
    return found


def gpu_snapshot() -> dict[str, Any]:
    gpu = subprocess.run(
        ["nvidia-smi", "--query-gpu=index,name,memory.total,memory.used", "--format=csv,noheader,nounits"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip().splitlines()
    processes = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader,nounits"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip().splitlines()
    return {"gpus": gpu, "compute_processes": [line for line in processes if line.strip()]}


def get_json(url: str, timeout: int = 10) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        value = json.loads(response.read())
    if not isinstance(value, dict):
        raise RuntimeError(f"non-object response from {url}")
    return value


class ProviderCallError(RuntimeError):
    """A provider attempt failed after any available bytes were custodied."""

    def __init__(
        self,
        message: str,
        *,
        receipt: dict[str, Any],
        request_body: bytes,
        response_body: bytes,
    ) -> None:
        super().__init__(message)
        self.receipt = receipt
        self.request_body = request_body
        self.response_body = response_body


def _error_bytes(exc: BaseException) -> bytes:
    return (
        f"{type(exc).__module__}.{type(exc).__qualname__}: {exc}"
    ).encode("utf-8", errors="backslashreplace")


def _write_provider_receipt(custody_root: Path | None, receipt: dict[str, Any]) -> None:
    if custody_root is not None:
        path = custody_root / "PROVIDER_CALL_RECEIPT.json"
        merged: dict[str, Any] = {}
        if path.is_file():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(existing, dict):
                raise RuntimeError("provider call receipt is not an object")
            merged.update(existing)
        merged.update(receipt)
        write_json(path, merged)


def _update_provider_receipt(custody_root: Path | None, updates: dict[str, Any]) -> dict[str, Any]:
    if custody_root is None:
        return dict(updates)
    receipt_path = custody_root / "PROVIDER_CALL_RECEIPT.json"
    if receipt_path.is_file():
        value = json.loads(receipt_path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise RuntimeError("provider call receipt is not an object")
    else:
        value = {}
    value.update(updates)
    write_json(receipt_path, value)
    return value


def post_json(
    path: str,
    value: dict[str, Any],
    timeout: int = 900,
    *,
    custody_root: Path | None = None,
) -> tuple[bytes, dict[str, Any], float]:
    """POST JSON, optionally preserving a complete transport-attempt record.

    With ``custody_root`` supplied, the canonical request is written before
    any network I/O.  A raw response file and receipt are then written for
    success, HTTP error, malformed JSON, timeout, disconnect, and other
    transport failures.  Callers should use a unique empty directory per
    attempt; the function refuses to overwrite prior request custody.
    """
    body = canonical_bytes(value)
    custody = custody_root.resolve() if custody_root is not None else None
    if custody is not None:
        custody.mkdir(parents=True, exist_ok=True)
        request_path = custody / "request.body.json"
        if request_path.exists():
            raise FileExistsError(f"provider attempt custody already exists: {request_path}")
        request_path.write_bytes(body)
        _write_provider_receipt(
            custody,
            {
                "schema_version": "provider-call-custody-v1",
                "endpoint": path,
                "timeout_seconds": timeout,
                "attempted": False,
                "request_bytes": len(body),
                "request_sha256": hashlib.sha256(body).hexdigest(),
                "response_received": False,
                "response_status": None,
                "response_bytes": 0,
                "response_sha256": None,
                "elapsed_seconds": None,
                "outcome": "request_custodied_before_io",
                "error_type": None,
                "error_bytes": 0,
                "error_sha256": None,
            },
        )
        # Create the raw-response target before I/O. Bytes are appended as
        # they arrive so a mid-body disconnect still leaves exact partial
        # custody rather than an empty post-hoc placeholder.
        (custody / "response.body.bin").write_bytes(b"")
    request = urllib.request.Request(
        BASE_URL + path,
        data=body,
        headers={"Content-Type": "application/json"},
    )
    started = time.perf_counter()
    _update_provider_receipt(
        custody,
        {
            "attempted": True,
            "outcome": "provider_io_started",
        },
    )
    raw = b""
    raw_parts: list[bytes] = []
    status: int | None = None

    def drain(stream: Any) -> bytes:
        response_path = None if custody is None else custody / "response.body.bin"
        handle = response_path.open("ab") if response_path is not None else None
        try:
            while True:
                chunk = stream.read(64 * 1024)
                if not chunk:
                    break
                if not isinstance(chunk, bytes):
                    raise TypeError("provider response stream returned non-bytes")
                raw_parts.append(chunk)
                if handle is not None:
                    handle.write(chunk)
                    handle.flush()
        finally:
            if handle is not None:
                handle.close()
        return b"".join(raw_parts)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = int(response.getcode())
            raw = drain(response)
    except urllib.error.HTTPError as exc:
        original_http_error = exc
        status = int(exc.code)
        try:
            raw = drain(exc)
        except Exception as read_exc:
            raw = b"".join(raw_parts)
            exc = urllib.error.HTTPError(
                exc.url,
                exc.code,
                f"{exc.reason}; response read failed: {type(read_exc).__name__}: {read_exc}",
                exc.headers,
                None,
            )
        finally:
            original_http_error.close()
        elapsed = time.perf_counter() - started
        error = _error_bytes(exc)
        receipt = {
            "schema_version": "provider-call-custody-v1",
            "endpoint": path,
            "attempted": True,
            "request_bytes": len(body),
            "request_sha256": hashlib.sha256(body).hexdigest(),
            "response_received": True,
            "response_status": status,
            "response_bytes": len(raw),
            "response_sha256": hashlib.sha256(raw).hexdigest(),
            "elapsed_seconds": elapsed,
            "outcome": "http_error",
            "error_type": type(exc).__name__,
            "error_bytes": len(error),
            "error_sha256": hashlib.sha256(error).hexdigest(),
        }
        if custody is not None:
            (custody / "error.bin").write_bytes(error)
        _write_provider_receipt(custody, receipt)
        raise ProviderCallError(
            f"provider HTTP {exc.code}",
            receipt=receipt,
            request_body=body,
            response_body=raw,
        ) from exc
    except Exception as exc:
        elapsed = time.perf_counter() - started
        raw = b"".join(raw_parts)
        error = _error_bytes(exc)
        receipt = {
            "schema_version": "provider-call-custody-v1",
            "endpoint": path,
            "attempted": True,
            "request_bytes": len(body),
            "request_sha256": hashlib.sha256(body).hexdigest(),
            "response_received": status is not None,
            "response_status": status,
            "response_bytes": len(raw),
            "response_sha256": hashlib.sha256(raw).hexdigest() if status is not None else None,
            "elapsed_seconds": elapsed,
            "outcome": "transport_error",
            "error_type": type(exc).__name__,
            "error_bytes": len(error),
            "error_sha256": hashlib.sha256(error).hexdigest(),
        }
        if custody is not None:
            (custody / "error.bin").write_bytes(error)
        _write_provider_receipt(custody, receipt)
        raise ProviderCallError(
            "provider transport failed",
            receipt=receipt,
            request_body=body,
            response_body=raw,
        ) from exc
    elapsed = time.perf_counter() - started
    try:
        decoded = json.loads(raw)
    except Exception as exc:
        error = _error_bytes(exc)
        receipt = {
            "schema_version": "provider-call-custody-v1",
            "endpoint": path,
            "attempted": True,
            "request_bytes": len(body),
            "request_sha256": hashlib.sha256(body).hexdigest(),
            "response_received": True,
            "response_status": status,
            "response_bytes": len(raw),
            "response_sha256": hashlib.sha256(raw).hexdigest(),
            "elapsed_seconds": elapsed,
            "outcome": "invalid_json_response",
            "error_type": type(exc).__name__,
            "error_bytes": len(error),
            "error_sha256": hashlib.sha256(error).hexdigest(),
        }
        if custody is not None:
            (custody / "error.bin").write_bytes(error)
        _write_provider_receipt(custody, receipt)
        raise ProviderCallError(
            "provider returned invalid JSON",
            receipt=receipt,
            request_body=body,
            response_body=raw,
        ) from exc
    if not isinstance(decoded, dict):
        exc = RuntimeError("provider returned non-object JSON")
        error = _error_bytes(exc)
        receipt = {
            "schema_version": "provider-call-custody-v1",
            "endpoint": path,
            "attempted": True,
            "request_bytes": len(body),
            "request_sha256": hashlib.sha256(body).hexdigest(),
            "response_received": True,
            "response_status": status,
            "response_bytes": len(raw),
            "response_sha256": hashlib.sha256(raw).hexdigest(),
            "elapsed_seconds": elapsed,
            "outcome": "non_object_json_response",
            "error_type": type(exc).__name__,
            "error_bytes": len(error),
            "error_sha256": hashlib.sha256(error).hexdigest(),
        }
        if custody is not None:
            (custody / "error.bin").write_bytes(error)
        _write_provider_receipt(custody, receipt)
        raise ProviderCallError(
            str(exc),
            receipt=receipt,
            request_body=body,
            response_body=raw,
        ) from exc
    _write_provider_receipt(
        custody,
        {
            "schema_version": "provider-call-custody-v1",
            "endpoint": path,
            "attempted": True,
            "request_bytes": len(body),
            "request_sha256": hashlib.sha256(body).hexdigest(),
            "response_received": True,
            "response_status": status,
            "response_bytes": len(raw),
            "response_sha256": hashlib.sha256(raw).hexdigest(),
            "elapsed_seconds": elapsed,
            "outcome": "json_object_received",
            "error_type": None,
            "error_bytes": 0,
            "error_sha256": None,
        },
    )
    return raw, decoded, elapsed


def wait_ready(process: subprocess.Popen[Any], timeout: int = 240) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"llama-server exited during startup: {process.returncode}")
        try:
            health = get_json(BASE_URL + "/health")
            if health.get("status") == "ok":
                return get_json(BASE_URL + "/props")
        except Exception:
            pass
        time.sleep(1)
    raise TimeoutError("llama-server did not become ready")


def wait_for_exact_offload(stderr_path: Path, timeout: int = 90) -> list[tuple[int, int]]:
    deadline = time.monotonic() + timeout
    matches: list[tuple[int, int]] = []
    while time.monotonic() < deadline:
        text = stderr_path.read_text(encoding="utf-8", errors="replace") if stderr_path.exists() else ""
        matches = [
            (int(left), int(right))
            for left, right in re.findall(r"offloaded\s+(\d+)/(\d+)\s+layers\s+to\s+GPU", text, re.I)
        ]
        if (EXPECTED_MAIN_LAYERS, EXPECTED_MAIN_LAYERS) in matches:
            return matches
        time.sleep(0.5)
    return matches


def verify_runtime(props: dict[str, Any], stderr_path: Path, pid: int) -> dict[str, Any]:
    matches = wait_for_exact_offload(stderr_path)
    gpu = gpu_snapshot()
    pid_seen = any(line.split(",", 1)[0].strip() == str(pid) for line in gpu["compute_processes"])
    observed_context = props.get("default_generation_settings", {}).get("n_ctx")
    failures: list[str] = []
    if props.get("model_alias") != EXPECTED_ALIAS:
        failures.append("model_alias_mismatch")
    if props.get("build_info") != EXPECTED_BUILD:
        failures.append("build_mismatch")
    if observed_context != EXPECTED_CONTEXT:
        failures.append("context_mismatch")
    if (EXPECTED_MAIN_LAYERS, EXPECTED_MAIN_LAYERS) not in matches:
        failures.append("exact_66_of_66_offload_not_observed")
    if not pid_seen:
        failures.append("server_pid_not_seen_on_gpu")
    return {
        "schema_version": "runtime-gate-v1",
        "passed": not failures,
        "failures": failures,
        "model_alias": props.get("model_alias"),
        "build_info": props.get("build_info"),
        "observed_context_tokens": observed_context,
        "offload_matches": matches,
        "expected_main_layers": EXPECTED_MAIN_LAYERS,
        "server_pid": pid,
        "server_pid_observed_on_gpu": pid_seen,
        "gpu_snapshot": gpu,
        "props": props,
    }


def start_server(log_root: Path) -> tuple[subprocess.Popen[Any], Any, Any, dict[str, Any]]:
    if port_open():
        raise RuntimeError(f"port {PORT} already open")
    existing = active_llama_server_pids()
    if existing:
        raise RuntimeError(f"pre-existing llama-server processes: {existing}")
    command = json.loads((ROOT / "MEASURED_RUNTIME_COMMAND.json").read_text(encoding="utf-8"))
    log_root.mkdir(parents=True, exist_ok=True)
    stdout_path = log_root / "server.stdout.log"
    stderr_path = log_root / "server.stderr.log"
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    # Snapshot before opening handles so a failed prerequisite cannot leak the
    # log streams.  Popen itself is also inside the guarded region below.
    before = gpu_snapshot()
    stdout = None
    stderr = None
    process: subprocess.Popen[Any] | None = None
    try:
        stdout = stdout_path.open("wb")
        stderr = stderr_path.open("wb")
        process = subprocess.Popen(
            [command["executable"], *command["arguments"]],
            cwd=ROOT,
            stdout=stdout,
            stderr=stderr,
            creationflags=creationflags,
        )
        props = wait_ready(process)
        stderr.flush()
        gate = verify_runtime(props, stderr_path, process.pid)
        gate["gpu_snapshot_before"] = before
        write_json(log_root / "RUNTIME_GATE.json", gate)
        if not gate["passed"]:
            raise RuntimeError(f"runtime gate failed: {gate['failures']}")
        return process, stdout, stderr, gate
    except Exception as exc:
        release: dict[str, Any] | None = None
        if process is not None:
            release = stop_server(process, stdout, stderr, log_root)
        else:
            close_errors: list[str] = []
            for label, handle in (("stdout", stdout), ("stderr", stderr)):
                if handle is not None:
                    try:
                        handle.close()
                    except Exception as close_exc:
                        close_errors.append(f"{label}_close:{type(close_exc).__name__}:{close_exc}")
            port_after: bool | None = None
            try:
                port_after = port_open()
            except Exception as probe_exc:
                close_errors.append(f"port_probe:{type(probe_exc).__name__}:{probe_exc}")
            active_after: list[int] | None = None
            try:
                active_after = active_llama_server_pids()
            except Exception as probe_exc:
                close_errors.append(f"process_probe:{type(probe_exc).__name__}:{probe_exc}")
            gpu_after: dict[str, Any] | None = None
            try:
                gpu_after = gpu_snapshot()
            except Exception as probe_exc:
                close_errors.append(f"gpu_probe:{type(probe_exc).__name__}:{probe_exc}")
            release = {
                "schema_version": "runtime-release-v1",
                "server_pid": None,
                "process_returncode": None,
                "process_stopped": True,
                "port_open_after": port_after,
                "server_pid_on_gpu_after": False,
                "active_llama_server_pids_after": active_after,
                "gpu_snapshot_after": gpu_after,
                "cleanup_errors": close_errors,
                "released": not close_errors and port_after is False,
            }
            try:
                write_json(log_root / "RUNTIME_RELEASE.json", release)
            except Exception:
                pass
        try:
            write_json(
                log_root / "RUNTIME_START_FAILURE.json",
                {
                    "schema_version": "runtime-start-failure-v1",
                    "exception_type": type(exc).__name__,
                    "exception": str(exc),
                    "release": release,
                },
            )
        except Exception:
            pass
        raise


def stop_server(process: subprocess.Popen[Any], stdout: Any, stderr: Any, log_root: Path) -> dict[str, Any]:
    """Best-effort server release that always returns a report.

    Cleanup failures are accumulated in ``cleanup_errors`` rather than raised,
    allowing the runner to seal the run first and then fail the stage based on
    ``released``.  The receipt write itself is best effort because a storage
    failure must not interrupt the remaining cleanup probes.
    """
    pid = process.pid
    errors: list[str] = []
    try:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=15)
    except Exception as exc:
        errors.append(f"process_release:{type(exc).__name__}:{exc}")
    for label, handle in (("stdout", stdout), ("stderr", stderr)):
        try:
            if handle is not None:
                handle.close()
        except Exception as exc:
            errors.append(f"{label}_close:{type(exc).__name__}:{exc}")

    port_after: bool | None = None
    try:
        deadline = time.monotonic() + 20
        while port_open() and time.monotonic() < deadline:
            time.sleep(0.25)
        port_after = port_open()
    except Exception as exc:
        errors.append(f"port_probe:{type(exc).__name__}:{exc}")

    after: dict[str, Any] | None = None
    pid_seen: bool | None = None
    try:
        after = gpu_snapshot()
        pid_seen = any(
            line.split(",", 1)[0].strip() == str(pid)
            for line in after["compute_processes"]
        )
    except Exception as exc:
        errors.append(f"gpu_probe:{type(exc).__name__}:{exc}")

    active: list[int] | None = None
    try:
        active = active_llama_server_pids()
    except Exception as exc:
        errors.append(f"process_probe:{type(exc).__name__}:{exc}")

    process_stopped = process.poll() is not None
    released = (
        not errors
        and process_stopped
        and port_after is False
        and pid_seen is False
        and active is not None
        and pid not in active
    )
    receipt = {
        "schema_version": "runtime-release-v1",
        "server_pid": pid,
        "process_returncode": process.returncode,
        "process_stopped": process_stopped,
        "port_open_after": port_after,
        "server_pid_on_gpu_after": pid_seen,
        "active_llama_server_pids_after": active,
        "gpu_snapshot_after": after,
        "cleanup_errors": errors,
        "released": released,
    }
    try:
        write_json(log_root / "RUNTIME_RELEASE.json", receipt)
    except Exception as exc:
        receipt["cleanup_errors"].append(
            f"release_receipt_write:{type(exc).__name__}:{exc}"
        )
        receipt["released"] = False
    return receipt


def assert_authorization(
    receipt_path: Path,
    scope: str,
    maximum_calls: int,
    *,
    run_id: str,
) -> dict[str, Any]:
    resolved_receipt = receipt_path.resolve()
    try:
        resolved_receipt.relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        raise RuntimeError("live authorization receipt must remain outside the repository")
    receipt = json.loads(resolved_receipt.read_text(encoding="utf-8"))
    authorization_scope = json.loads((ROOT / "AUTHORIZATION_REQUEST.json").read_text(encoding="utf-8"))
    failures: list[str] = []
    if receipt.get("authorized") is not True:
        failures.append("not_authorized")
    if receipt.get("authorized_freeze_commit") != git_commit():
        failures.append("commit_mismatch")
    if receipt.get("user_quote") != authorization_scope.get("user_quote"):
        failures.append("user_quote_mismatch")
    if receipt.get("authorized_scopes") != [scope]:
        failures.append("scope_must_be_exact_single_stage")
    if receipt.get("authorized_run_id") != run_id:
        failures.append("run_id_mismatch")
    if not isinstance(receipt.get("authorization_id"), str) or not receipt.get("authorization_id"):
        failures.append("authorization_id_missing")
    if receipt.get("maximum_model_calls") != maximum_calls:
        failures.append("call_ceiling_mismatch")
    if receipt.get("retries") != 0:
        failures.append("retries_must_be_zero")
    if failures:
        raise RuntimeError(f"authorization receipt failed: {failures}")
    return receipt


def provider_payload(
    messages: list[dict[str, str]],
    seed: int,
    response_format: dict[str, Any],
    *,
    max_tokens: int = 4096,
) -> dict[str, Any]:
    return {
        "model": EXPECTED_ALIAS,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 20,
        "min_p": 0.0,
        "presence_penalty": 1.5,
        "repeat_penalty": 1.0,
        "seed": seed,
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": False, "preserve_thinking": False},
        "response_format": response_format,
    }


class LiveTokenizer:
    def tokenize(self, content: str) -> list[int]:
        _, value, _ = post_json("/tokenize", {"content": content, "add_special": False, "parse_special": True})
        tokens = value.get("tokens")
        if not isinstance(tokens, list) or not all(isinstance(item, int) for item in tokens):
            raise RuntimeError("/tokenize did not return token ids")
        return tokens

    def render(self, messages: list[dict[str, str]]) -> str:
        _, value, _ = post_json(
            "/apply-template",
            {
                "messages": messages,
                "add_generation_prompt": True,
                "chat_template_kwargs": {"enable_thinking": False, "preserve_thinking": False},
            },
        )
        prompt = value.get("prompt")
        if not isinstance(prompt, str):
            raise RuntimeError("/apply-template did not return prompt")
        return prompt

    def count_messages(self, messages: list[dict[str, str]]) -> tuple[int, str]:
        rendered = self.render(messages)
        return len(self.tokenize(rendered)), rendered


def complete(
    payload: dict[str, Any],
    *,
    custody_root: Path | None = None,
    timeout: int = 900,
) -> dict[str, Any]:
    """Execute one chat completion, with optional pre-I/O exact custody.

    Existing callers may omit ``custody_root``.  Live measured runners should
    pass a unique per-attempt directory; doing so preserves the request before
    I/O and records raw/error bytes even when this function raises.
    """
    request_body = canonical_bytes(payload)
    raw, response, elapsed = post_json(
        "/v1/chat/completions",
        payload,
        timeout=timeout,
        custody_root=custody_root,
    )
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        exc = RuntimeError("completion lacks choices")
        error = _error_bytes(exc)
        if custody_root is not None:
            custody_root.mkdir(parents=True, exist_ok=True)
            (custody_root / "error.bin").write_bytes(error)
        receipt = _update_provider_receipt(
            custody_root,
            {
                "outcome": "invalid_completion_response",
                "completion_response_valid": False,
                "error_type": type(exc).__name__,
                "error_bytes": len(error),
                "error_sha256": hashlib.sha256(error).hexdigest(),
            },
        )
        raise ProviderCallError(
            str(exc),
            receipt=receipt,
            request_body=request_body,
            response_body=raw,
        ) from exc
    message = choices[0].get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str):
        exc = RuntimeError("completion lacks assistant content")
        error = _error_bytes(exc)
        if custody_root is not None:
            custody_root.mkdir(parents=True, exist_ok=True)
            (custody_root / "error.bin").write_bytes(error)
        receipt = _update_provider_receipt(
            custody_root,
            {
                "outcome": "invalid_completion_response",
                "completion_response_valid": False,
                "error_type": type(exc).__name__,
                "error_bytes": len(error),
                "error_sha256": hashlib.sha256(error).hexdigest(),
            },
        )
        raise ProviderCallError(
            str(exc),
            receipt=receipt,
            request_body=request_body,
            response_body=raw,
        ) from exc
    _update_provider_receipt(
        custody_root,
        {
            "outcome": "valid_completion_response",
            "completion_response_valid": True,
        },
    )
    return {
        "request_body": request_body,
        "response_body": raw,
        "response": response,
        "content": content,
        "usage": response.get("usage", {}),
        "finish_reason": choices[0].get("finish_reason"),
        "http_seconds": elapsed,
    }


def complete_custodied(
    payload: dict[str, Any],
    custody_root: Path,
    *,
    timeout: int = 900,
) -> dict[str, Any]:
    """Explicit measured-call interface; equivalent to `complete(..., custody_root=...)`."""
    return complete(payload, custody_root=custody_root, timeout=timeout)
