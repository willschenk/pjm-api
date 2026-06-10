"""Unified command-line entry point for PJM OASIS integration."""

from __future__ import annotations

import argparse
import getpass
import json
import sys
from pathlib import Path

from pjm_api.certs import inspect_certificate
from pjm_api.cli_adapter import CLI_ARGV_SECRET_WARNING, CliBackend
from pjm_api.cli_zip import install_cli_zip
from pjm_api.config import DEFAULT_ENVIRONMENT, EXTENDED_OASIS_URLS, load_settings
from pjm_api.exceptions import PJMError
from pjm_api.logging_utils import configure_logging, get_logger
from pjm_api.oasis import OasisClient
from pjm_api.oasis_cli import parse_key_value_pairs
from pjm_api.templates import get_template_info, list_templates

logger = get_logger()


def _build_parser() -> argparse.ArgumentParser:
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--env", default=DEFAULT_ENVIRONMENT, choices=sorted(EXTENDED_OASIS_URLS))
    shared.add_argument("--username")
    shared.add_argument("--password")
    shared.add_argument("--cert")
    shared.add_argument("--cert-password")
    shared.add_argument("--backend", choices=("native", "cli"))
    shared.add_argument("--downloads")
    shared.add_argument("--oasis-url")
    shared.add_argument("-v", "--verbose", action="store_true")
    shared.add_argument("-q", "--quiet", action="store_true")

    parser = argparse.ArgumentParser(
        prog="pjm-api",
        description="PJM OASIS client — authenticate, diagnose, and run templates.",
        parents=[shared],
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("config", parents=[shared], help="Show resolved configuration.")
    auth = sub.add_parser("auth-check", parents=[shared], help="Verify authentication.")
    auth.add_argument("--full", action="store_true", help="Run TRANSSERV smoke after SSO check.")
    cert = sub.add_parser("cert-doctor", parents=[shared], help="Inspect certificate file.")
    cert.add_argument("--json", action="store_true")

    smoke = sub.add_parser("smoke", parents=[shared], help="Run TRANSSERV smoke test.")
    smoke.add_argument("--all", action="store_true", help="Run TEST, STAGE, TRAIN batch.")
    smoke.add_argument("--outfile")
    smoke.add_argument("--save")
    smoke.add_argument("--output-format")
    smoke.add_argument("--timeout-sec", type=int, default=120)

    tmpl = sub.add_parser("template", parents=[shared], help="Run OASIS template.")
    tmpl.add_argument("name")
    tmpl.add_argument("--outfile")
    tmpl.add_argument("--save")
    tmpl.add_argument("--output-format")
    tmpl.add_argument("--timeout-sec", type=int, default=120)
    tmpl.add_argument("--method", default="GET")
    tmpl.add_argument("--action")
    tmpl.add_argument("--query-param", action="append", default=[])
    tmpl.add_argument("--continuation-flag", default="N")

    tlist = sub.add_parser("templates", help="Template catalog commands.")
    tsub = tlist.add_subparsers(dest="templates_cmd", required=True)
    tsub.add_parser("list")
    info = tsub.add_parser("info")
    info.add_argument("name")

    cli_install = sub.add_parser("cli", help="PJM Java CLI management.")
    cli_sub = cli_install.add_subparsers(dest="cli_cmd", required=True)
    inst = cli_sub.add_parser("install", help="Download and install PJM CLI ZIP.")
    inst.add_argument("--dir", default="~/.pjm/cli")
    inst.add_argument("--force", action="store_true")

    return parser


def _prompt_secrets(args: argparse.Namespace, settings_kwargs: dict) -> dict:
    if args.command in ("config", "templates", "cli", "cert-doctor"):
        return settings_kwargs
    if not settings_kwargs.get("password") and not args.password:
        settings_kwargs["password"] = getpass.getpass("PJM password: ")
    cert_path = settings_kwargs.get("certificate") or args.cert
    if cert_path and str(cert_path).endswith((".p12", ".pfx")):
        if not settings_kwargs.get("certificate_password") and not args.cert_password:
            settings_kwargs["certificate_password"] = getpass.getpass("Certificate password: ")
    return settings_kwargs


def _load_from_args(args: argparse.Namespace):
    kwargs = dict(
        username=args.username or "",
        password=args.password or "",
        certificate=args.cert or "",
        certificate_password=args.cert_password or "",
        environment=args.env,
        oasis_url=getattr(args, "oasis_url", "") or "",
        backend=args.backend or "",
        downloads_dir=args.downloads or "",
    )
    kwargs = _prompt_secrets(args, kwargs)
    return load_settings(**kwargs)


def _cmd_config(settings) -> int:
    print("Resolved configuration:")
    for key, val in [
        ("backend", settings.backend),
        ("environment", settings.environment),
        ("oasis_url", settings.oasis_base_url),
        ("sso_url", settings.sso_url),
        ("username", settings.username or "(not set)"),
        ("password", "***" if settings.password else "(not set)"),
        ("certificate", settings.certificate_path or "(not set)"),
        ("downloads", settings.downloads_dir),
        ("jar_path", settings.jar_path or "(not set)"),
    ]:
        print(f"  {key + ':':14} {val}")
    missing = settings.missing_for_backend()
    if missing:
        print(f"  missing:       {', '.join(missing)}")
        return 1
    if settings.backend == "cli":
        print(f"  note:          {CLI_ARGV_SECRET_WARNING}")
    return 0


def _cmd_cert_doctor(settings, args) -> int:
    if not settings.certificate_path:
        print("[cert-doctor] No certificate configured.")
        return 1
    report = inspect_certificate(settings.certificate_path, settings.certificate_password)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(f"[cert-doctor] path:       {report.path}")
        print(f"[cert-doctor] kind:       {report.kind.value}")
        print(f"[cert-doctor] subject:    {report.subject or '(unknown)'}")
        print(f"[cert-doctor] issuer:     {report.issuer or '(unknown)'}")
        print(f"[cert-doctor] thumbprint: {report.thumbprint or '(unknown)'}")
        if report.not_after:
            print(f"[cert-doctor] expires:    {report.not_after.isoformat()}")
        for w in report.warnings:
            print(f"[cert-doctor] WARN: {w}")
        for e in report.errors:
            print(f"[cert-doctor] ERROR: {e}")
    return 0 if report.healthy else 2


def _cmd_auth_check(settings, args) -> int:
    settings.validate()
    if settings.backend == "cli" and not args.full:
        backend = CliBackend(settings)
        result = backend.run_cli(backend.build_smoke_test_cmd(), timeout_sec=60)
        ok = result.returncode == 0 and "SUCCESS" in result.stdout
        print("[auth-check] PASS" if ok else "[auth-check] FAIL")
        return 0 if ok else 1

    with OasisClient(settings) as client:
        client.authenticate()
        print("[auth-check] PASS — SSO token obtained.")
        if args.full:
            resp = client.smoke_transserv()
            ok = resp.ok and resp.text()
            print(
                "[auth-check] TRANSSERV smoke PASS" if ok else "[auth-check] TRANSSERV smoke FAIL"
            )
            return 0 if ok else 1
    return 0


def _save_response(resp, settings, save_path: str | None, outfile: str | None) -> None:
    if save_path:
        path = Path(save_path)
    elif outfile:
        path = settings.downloads_dir / outfile
    else:
        return
    saved = resp.save(path)
    print(f"Saved output to {saved}")


def _cmd_smoke_native(settings, args) -> int:
    settings.downloads_dir.mkdir(parents=True, exist_ok=True)
    if args.all:
        from pjm_api.config import load_settings

        results = {}
        for env in ("TEST", "STAGE", "TRAIN"):
            env_settings = load_settings(
                username=settings.username,
                password=settings.password,
                certificate=str(settings.certificate_path or ""),
                certificate_password=settings.certificate_password or "",
                environment=env,
                backend="native",
            )
            try:
                with OasisClient(env_settings) as client:
                    resp = client.smoke_transserv()
                    ok = resp.ok
                    if args.save or args.outfile:
                        _save_response(
                            resp,
                            env_settings,
                            args.save,
                            args.outfile or f"smoke_{env.lower()}.txt",
                        )
                    results[env] = ok
                    print(f"[SMOKE TEST:{env}] {'PASS' if ok else 'FAIL'}")
            except Exception as exc:
                print(f"[SMOKE TEST:{env}] ERROR - {exc}")
                results[env] = False
        return 0 if all(results.values()) else 1

    with OasisClient(settings) as client:
        params = {}
        if args.output_format:
            params["OUTPUT_FORMAT"] = args.output_format
        resp = client.request("TRANSSERV", params) if params else client.smoke_transserv()
        ok = resp.ok
        _save_response(resp, settings, args.save, args.outfile)
        print(f"[SMOKE TEST:{settings.environment}] {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1


def _cmd_template_native(settings, args) -> int:
    settings.downloads_dir.mkdir(parents=True, exist_ok=True)
    params = parse_key_value_pairs(args.query_param)
    with OasisClient(settings) as client:
        resp = client.request(
            args.name,
            params,
            method=args.method,
            output_format=args.output_format,
            continuation_flag=args.continuation_flag,
            action_override=args.action,
        )
        _save_response(resp, settings, args.save, args.outfile or f"{args.name.lower()}_output.txt")
        print(resp.text()[:2000])
        return 0 if resp.ok else 1


def _cmd_templates(args) -> int:
    if args.templates_cmd == "list":
        for info in list_templates():
            tag = " [PJM custom]" if info.pjm_custom else ""
            print(f"{info.name:20} {info.type:8}{tag}  {info.description}")
        return 0
    info = get_template_info(args.name)
    if not info:
        print(f"Unknown template: {args.name}")
        return 1
    print(f"Name:        {info.name}")
    print(f"Type:        {info.type}")
    print(f"Methods:     {', '.join(info.supported_methods)}")
    print(f"NAESB:       {info.naesb_version_default}")
    print(f"Description: {info.description}")
    if info.common_params:
        print("Common params:")
        for k, v in info.common_params.items():
            print(f"  {k}={v}")
    return 0


def _cmd_cli_install(args) -> int:
    jar = install_cli_zip(Path(args.dir).expanduser(), force=args.force)
    print(f"Installed: {jar}")
    print(f"Set PJM_CLI_JAR_PATH={jar}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    configure_logging(verbose=args.verbose, quiet=args.quiet)

    if args.command == "templates":
        return _cmd_templates(args)
    if args.command == "cli":
        return _cmd_cli_install(args)

    settings = _load_from_args(args)

    try:
        if args.command == "config":
            return _cmd_config(settings)
        if args.command == "cert-doctor":
            return _cmd_cert_doctor(settings, args)
        if args.command == "auth-check":
            return _cmd_auth_check(settings, args)

        settings.validate()

        if settings.backend == "cli":
            backend = CliBackend(settings)
            if args.command == "smoke":
                if args.all:
                    results = backend.run_all_smoke_tests()
                    return 0 if all(results.values()) else 1
                ok = backend.smoke_test(
                    timeout_sec=args.timeout_sec,
                    print_results=not args.quiet,
                    outfile=args.outfile,
                )
                return 0 if ok else 1
            if args.command == "template":
                params = parse_key_value_pairs(args.query_param)
                if args.output_format:
                    params["OUTPUT_FORMAT"] = args.output_format
                result = backend.run_template(
                    template=args.name,
                    outfile=args.outfile,
                    timeout_sec=args.timeout_sec,
                    params=params,
                    action_override=args.action,
                    continuation_flag=args.continuation_flag,
                    method=args.method,
                    print_results=not args.quiet,
                )
                return result.returncode

        if args.command == "smoke":
            return _cmd_smoke_native(settings, args)
        if args.command == "template":
            return _cmd_template_native(settings, args)

    except PJMError as exc:
        logger.error(str(exc))
        if exc.hint:
            logger.error(exc.hint)
        return 1
    except (ValueError, FileNotFoundError) as exc:
        logger.error(str(exc))
        return 2

    print(f"Unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
