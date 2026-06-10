"""PJM OASIS Java CLI helpers — legacy module, prefer cli_adapter."""

from __future__ import annotations

import subprocess
from pathlib import Path

from pjm_api.config import DEFAULT_ENVIRONMENT, EXTENDED_OASIS_URLS, get_env_url

MEM_ARGS = ["-Xms64m", "-Xmx256m"]
TIMEOUT = ["-z", "180000"]
DEFAULT_ENV = DEFAULT_ENVIRONMENT
SMOKE_OUTFILE = "config_smoke_transserv.txt"
ENV_URLS = EXTENDED_OASIS_URLS


def _config() -> dict[str, str]:
    from pjm_api.config import load_settings

    s = load_settings()
    return {
        "java_path": s.java_path,
        "jar_path": str(s.jar_path or ""),
        "downloads": str(s.downloads_dir),
        "user": s.username,
        "password": s.password,
        "certificate": s.certificate_legacy(),
    }


def ensure_output_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def filename_only(value: str) -> str:
    return value.replace("\\", "/").split("/")[-1]


def normalize_template_name(template: str) -> str:
    value = (template or "").strip()
    if not value:
        raise ValueError("template is required")
    return value.upper()


def mask_command_for_display(cmd: list[str]) -> list[str]:
    masked = list(cmd)
    for flag in ("-p", "-r"):
        if flag in masked:
            idx = masked.index(flag)
            if idx + 1 < len(masked):
                masked[idx + 1] = "***REDACTED***"
    return masked


def require_cli_config(cfg: dict[str, str] | None = None) -> dict[str, str]:
    cfg = cfg or _config()
    missing = []
    if not cfg["jar_path"]:
        missing.append("PJM_CLI_JAR_PATH")
    if not cfg["user"]:
        missing.append("PJM_CLI_USER")
    if not cfg["password"]:
        missing.append("PJM_CLI_PASSWORD")
    if not cfg["certificate"]:
        missing.append("PJM_CLI_CERTIFICATE")
    if missing:
        raise ValueError("Missing required environment variables: " + ", ".join(missing))
    return cfg


def make_template_cmd(
    *,
    template: str,
    env: str | None = None,
    outfile: str | None = None,
    method: str = "GET",
    action_override: str | None = None,
    params: dict[str, str] | None = None,
    continuation_flag: str | None = None,
    template_name: str | None = None,
    include_template_param: bool = True,
) -> list[str]:
    from pjm_api.cli_adapter import CliBackend
    from pjm_api.config import load_settings

    settings = load_settings(environment=env or DEFAULT_ENV, backend="cli")
    backend = CliBackend(settings)
    normalized = normalize_template_name(template_name or template)
    qparams = dict(params or {})
    if not include_template_param:
        cmd = backend.make_template_cmd(
            template=normalized,
            outfile=outfile,
            method=method,
            action_override=action_override,
            params={},
            continuation_flag=continuation_flag,
        )
        filtered: list[str] = []
        skip_next = False
        for part in cmd:
            if skip_next:
                skip_next = False
                continue
            if part == "-q" and len(filtered) < len(cmd) - 1:
                nxt = cmd[cmd.index(part) + 1]
                if nxt.startswith("TEMPLATE="):
                    skip_next = True
                    continue
            filtered.append(part)
        for key, value in qparams.items():
            filtered.extend(["-q", f"{key}={value}"])
        return filtered
    return backend.make_template_cmd(
        template=normalized,
        outfile=outfile,
        method=method,
        action_override=action_override,
        params=qparams,
        continuation_flag=continuation_flag,
    )


def run_template(**kwargs) -> tuple[int, str, str]:
    from pjm_api.cli_adapter import CliBackend
    from pjm_api.config import load_settings

    env = kwargs.pop("env", DEFAULT_ENV)
    settings = load_settings(environment=env, backend="cli")
    backend = CliBackend(settings)
    result = backend.run_template(**kwargs)
    return result.returncode, result.stdout, result.stderr


def _format_block(returncode: int, stdout: str, stderr: str) -> str:
    def bullets(label: str, text: str) -> str:
        text = (text or "").strip()
        if not text:
            return f"{label}:"
        lines = [line.rstrip() for line in text.splitlines()]
        return f"{label}:\n  - " + "\n  - ".join(lines)

    return "\n".join(
        [
            f"returncode: {returncode}",
            bullets("stdout", stdout),
            bullets("stderr", stderr),
        ]
    )


def run_cli(
    cmd: list[str],
    *,
    timeout_sec: int = 120,
    print_results: bool = True,
    print_command: bool = False,
) -> tuple[int, str, str]:
    if print_command:
        print("command:")
        print(" ".join(mask_command_for_display(cmd)))
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
    if print_results:
        print(_format_block(res.returncode, res.stdout or "", res.stderr or ""))
    return res.returncode, res.stdout, res.stderr


def qualify_result_with_criteria(
    code: int, stdout: str | None, stderr: str | None, **kwargs
) -> bool:
    s_out, s_err = stdout or "", stderr or ""
    if kwargs.get("code_equals") is not None and code != kwargs["code_equals"]:
        return False
    if kwargs.get("stderr_must_be_empty") and s_err.strip():
        return False
    for needle in kwargs.get("stdout_contains_all") or []:
        if needle and needle not in s_out:
            return False
    return True


def build_smoke_test_cmd(env: str, *, outfile: str | None = None) -> list[str]:
    from pjm_api.cli_adapter import CliBackend
    from pjm_api.config import load_settings

    settings = load_settings(environment=env, backend="cli")
    return CliBackend(settings).build_smoke_test_cmd(outfile=outfile)


def smoke_test(env: str = DEFAULT_ENV, **kwargs) -> bool:
    from pjm_api.cli_adapter import CliBackend
    from pjm_api.config import load_settings

    settings = load_settings(environment=env, backend="cli")
    return CliBackend(settings).smoke_test(**kwargs)


def run_all_smoke_tests() -> dict[str, bool]:
    from pjm_api.cli_adapter import CliBackend
    from pjm_api.config import load_settings

    settings = load_settings(backend="cli")
    return CliBackend(settings).run_all_smoke_tests()


def parse_key_value_pairs(values: list[str] | None) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in values or []:
        if "=" not in item:
            raise ValueError(f"Query parameter must be KEY=VALUE, got {item!r}")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Query parameter key cannot be empty: {item!r}")
        parsed[key] = value
    return parsed
