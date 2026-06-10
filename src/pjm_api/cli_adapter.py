"""Official PJM Java CLI fallback adapter."""

from __future__ import annotations

import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from pjm_api.config import PJMSettings
from pjm_api.exceptions import PJMConfigError, PJMTimeoutError
from pjm_api.oasis_cli import (
    MEM_ARGS,
    SMOKE_OUTFILE,
    TIMEOUT,
    _format_block,
    filename_only,
    mask_command_for_display,
    normalize_template_name,
    qualify_result_with_criteria,
)

# PJM CLI requires credentials via flags; native backend avoids argv secret exposure.
CLI_ARGV_SECRET_WARNING = (
    "CLI backend passes credentials on the subprocess command line. "
    "Prefer --backend native when possible."
)


@dataclass(frozen=True)
class BackendResult:
    returncode: int
    stdout: str
    stderr: str
    output_file: Path | None = None


class CliBackend:
    """Adapter for the official PJM Java CLI."""

    def __init__(self, settings: PJMSettings) -> None:
        self.settings = settings
        self._validate()

    def _validate(self) -> None:
        if not self.settings.jar_path:
            raise PJMConfigError("PJM_CLI_JAR_PATH is required for CLI backend")
        if not self.settings.jar_path.exists():
            raise PJMConfigError(f"JAR not found: {self.settings.jar_path}")

    def _base_cmd(self) -> list[str]:
        return [
            self.settings.java_path,
            *MEM_ARGS,
            "-jar",
            str(self.settings.jar_path),
            "-d",
            str(self.settings.downloads_dir),
            "-u",
            self.settings.username,
            "-p",
            self.settings.password,
            "-r",
            self.settings.certificate_legacy(),
        ]

    def run_cli(
        self,
        cmd: list[str],
        *,
        timeout_sec: int = 120,
        print_results: bool = False,
    ) -> BackendResult:
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
        except subprocess.TimeoutExpired as exc:
            raise PJMTimeoutError(f"CLI subprocess timed out after {timeout_sec}s") from exc

        if print_results:
            print(_format_block(res.returncode, res.stdout or "", res.stderr or ""))

        return BackendResult(res.returncode, res.stdout or "", res.stderr or "")

    def make_template_cmd(
        self,
        *,
        template: str,
        outfile: str | None = None,
        method: str = "GET",
        action_override: str | None = None,
        params: dict[str, str] | None = None,
        continuation_flag: str | None = None,
    ) -> list[str]:
        normalized = normalize_template_name(template)
        template_path_name = normalized.lower()
        action = action_override or f"/rest/secure/{template_path_name}"
        out_name = filename_only(outfile or f"{template_path_name}_sample.txt")

        qparams: dict[str, str] = {"TEMPLATE": normalized}
        qparams.update(params or {})
        if continuation_flag is not None:
            qparams["CONTINUATION_FLAG"] = continuation_flag

        cmd = [
            *self._base_cmd(),
            "-s",
            self.settings.oasis_base_url,
            "-t",
            method.upper(),
            "-a",
            action,
            "-o",
            out_name,
        ]
        for key, value in qparams.items():
            cmd.extend(["-q", f"{key}={value}"])
        cmd.extend(TIMEOUT)
        return cmd

    def run_template(
        self,
        *,
        template: str,
        outfile: str | None = None,
        timeout_sec: int = 120,
        params: dict[str, str] | None = None,
        action_override: str | None = None,
        continuation_flag: str = "N",
        method: str = "GET",
        print_results: bool = False,
    ) -> BackendResult:
        self.settings.downloads_dir.mkdir(parents=True, exist_ok=True)
        out_name = filename_only(outfile or f"{template.lower()}_sample.txt")
        cmd = self.make_template_cmd(
            template=template,
            outfile=out_name,
            method=method,
            params=params,
            action_override=action_override,
            continuation_flag=continuation_flag,
        )
        result = self.run_cli(cmd, timeout_sec=timeout_sec, print_results=print_results)
        return BackendResult(
            result.returncode,
            result.stdout,
            result.stderr,
            self.settings.downloads_dir / out_name,
        )

    def build_smoke_test_cmd(self, *, outfile: str | None = None) -> list[str]:
        cmd = [
            *self._base_cmd(),
            "-s",
            self.settings.oasis_base_url,
            "-a",
            "/rest/secure/transserv",
            "-q",
            "TEMPLATE=TRANSSERV",
            "-q",
            "OUTPUT_FORMAT=DATA",
            "-q",
            "PRIMARY_PROVIDER_CODE=PJM",
            "-q",
            "PRIMARY_PROVIDER_DUNS=073647877",
            "-q",
            "RETURN_TZ=EP",
            "-q",
            "VERSION=3.3",
            *TIMEOUT,
        ]
        if outfile:
            cmd.extend(["-o", filename_only(outfile)])
        return cmd

    def smoke_test(
        self,
        *,
        timeout_sec: int = 120,
        print_results: bool = True,
        outfile: str | None = None,
    ) -> bool:
        self.settings.downloads_dir.mkdir(parents=True, exist_ok=True)
        cmd = self.build_smoke_test_cmd(outfile=outfile or SMOKE_OUTFILE)
        result = self.run_cli(cmd, timeout_sec=timeout_sec, print_results=print_results)
        ok = qualify_result_with_criteria(
            result.returncode,
            result.stdout,
            result.stderr,
            code_equals=0,
            stdout_contains_all=["SUCCESS"],
            stderr_must_be_empty=True,
        )
        env = self.settings.environment
        print(f"[SMOKE TEST:{env}] {'PASS' if ok else 'FAIL'}")
        return ok

    def run_all_smoke_tests(
        self, environments: Iterable[str] = ("TEST", "STAGE", "TRAIN")
    ) -> dict[str, bool]:
        from pjm_api.config import load_settings

        results: dict[str, bool] = {}
        for env in environments:
            print("=" * 72)
            print(f"Running smoke test for {env} ...")
            env_settings = load_settings(
                username=self.settings.username,
                password=self.settings.password,
                certificate=str(self.settings.certificate_path or ""),
                certificate_password=self.settings.certificate_password or "",
                environment=env,
                backend="cli",
                jar_path=str(self.settings.jar_path or ""),
                downloads_dir=str(self.settings.downloads_dir),
            )
            backend = CliBackend(env_settings)
            try:
                results[env] = backend.smoke_test(outfile=f"smoke_{env.lower()}.txt")
            except Exception as exc:
                print(f"Result [{env}]: ERROR - {exc}")
                results[env] = False
        return results


def mask_command(cmd: list[str]) -> list[str]:
    return mask_command_for_display(cmd)
