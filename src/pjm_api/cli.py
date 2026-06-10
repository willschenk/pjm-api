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
from pjm_api.credentials import (
    StoredCredentials,
    credentials_exist,
    credentials_path,
    rotate_master_password,
    save_credentials,
)
from pjm_api.doctor import format_doctor_report, run_doctor
from pjm_api.exceptions import PJMError
from pjm_api.logging_utils import configure_logging, get_logger
from pjm_api.oasis import OasisClient
from pjm_api.oasis_cli import parse_key_value_pairs
from pjm_api.templates import get_template_info, list_templates
from pjm_api.unlock import clear_unlock_cache

logger = get_logger()

NO_UNLOCK_COMMANDS = frozenset({"init", "templates", "cli", "config", "credentials"})


def _non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("--preview-chars must be zero or greater")
    return parsed


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
        description="PJM OASIS client.",
        parents=[shared],
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create encrypted credentials file.")
    init.add_argument("--force", action="store_true")
    doctor = sub.add_parser("doctor", parents=[shared], help="Run all setup checks.")
    doctor.add_argument(
        "--offline",
        action="store_true",
        help="Check local credentials and certificate only; skip network calls.",
    )
    creds = sub.add_parser("credentials", help="Manage credentials file.")
    creds_sub = creds.add_subparsers(dest="credentials_cmd", required=True)
    creds_sub.add_parser("show", help="Show redacted credentials summary.")
    rotate = creds_sub.add_parser("rotate-password", help="Change master password.")
    rotate.add_argument("--force", action="store_true")

    sub.add_parser("config", parents=[shared], help="Show resolved configuration.")
    auth = sub.add_parser("auth-check", parents=[shared], help="Verify authentication.")
    auth.add_argument("--full", action="store_true")
    cert = sub.add_parser("cert-doctor", parents=[shared], help="Inspect certificate file.")
    cert.add_argument("--json", action="store_true")

    smoke = sub.add_parser("smoke", parents=[shared], help="Run TRANSSERV smoke test.")
    smoke.add_argument("--all", action="store_true")
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
    tmpl.add_argument("--preview-chars", type=_non_negative_int, default=2000)

    tlist = sub.add_parser("templates", help="Template catalog (advanced).")
    tsub = tlist.add_subparsers(dest="templates_cmd", required=True)
    tsub.add_parser("list")
    info = tsub.add_parser("info")
    info.add_argument("name")

    cli_install = sub.add_parser("cli", help="PJM Java CLI (advanced).")
    cli_sub = cli_install.add_subparsers(dest="cli_cmd", required=True)
    inst = cli_sub.add_parser("install")
    inst.add_argument("--dir", default="~/.pjm/cli")
    inst.add_argument("--force", action="store_true")

    return parser


def _cmd_init(args) -> int:
    cred_path = credentials_path()
    print("pjm-api init — create encrypted credentials")
    print(f"File: {cred_path}\n")

    if credentials_exist() and not args.force:
        print(f"Existing credentials: {cred_path}")
        answer = input("Overwrite existing credentials? [y/N]: ").strip().lower()
        if answer not in ("y", "yes"):
            print("Canceled.")
            return 1

    username = input("PJM username: ").strip()
    password = getpass.getpass("PJM password: ")
    cert_path = input("Path to login .p12/.pfx file: ").strip()
    cert_password = getpass.getpass("Certificate password: ")

    resolved_cert = Path(cert_path).expanduser()
    if not resolved_cert.exists():
        print(f"Certificate file not found: {resolved_cert}", file=sys.stderr)
        return 2

    report = inspect_certificate(resolved_cert, cert_password)
    if report.errors:
        for error in report.errors:
            print(error, file=sys.stderr)
        return 2

    print(f"kind:    {report.kind.value}")
    if report.not_after:
        print(f"expires: {report.not_after.date()}")
    for warning in report.warnings:
        print(f"WARN: {warning}")

    env = input("Environment [TRAIN]: ").strip().upper() or DEFAULT_ENVIRONMENT
    if env not in EXTENDED_OASIS_URLS:
        valid = ", ".join(sorted(EXTENDED_OASIS_URLS))
        print(f"Invalid environment: {env}", file=sys.stderr)
        print(f"Valid choices: {valid}", file=sys.stderr)
        return 2

    master = getpass.getpass("Master password (encrypts credentials file): ")
    master_confirm = getpass.getpass("Confirm master password: ")
    if master != master_confirm:
        print("Master passwords do not match.", file=sys.stderr)
        return 2

    data = StoredCredentials(
        username=username,
        password=password,
        cert_path=str(resolved_cert),
        cert_password=cert_password,
        environment=env,
    )
    path = save_credentials(data, master)
    print(f"\nSaved: {path}")
    print("Next: pjm-api doctor")
    return 0


def _cmd_credentials(args) -> int:
    if args.credentials_cmd == "show":
        if not credentials_exist():
            print("No credentials file. Run: pjm-api init")
            return 1
        from pjm_api.unlock import load_unlocked_credentials

        creds = load_unlocked_credentials(prompt=True)
        if not creds:
            print("Could not unlock credentials.", file=sys.stderr)
            return 2
        for key, val in creds.redacted_summary().items():
            print(f"  {key + ':':14} {val}")
        print(f"  file:          {credentials_path()}")
        return 0

    if args.credentials_cmd == "rotate-password":
        if not credentials_exist():
            print("No credentials file. Run: pjm-api init")
            return 1
        old = getpass.getpass("Current master password: ")
        new = getpass.getpass("New master password: ")
        confirm = getpass.getpass("Confirm new master password: ")
        if new != confirm:
            print("Passwords do not match.", file=sys.stderr)
            return 2
        path = rotate_master_password(old, new)
        clear_unlock_cache()
        print(f"Updated: {path}")
        return 0

    return 2


def _cmd_doctor(settings, args) -> int:
    steps, passed = run_doctor(settings, offline=args.offline)
    print(format_doctor_report(steps, passed, offline=args.offline))
    return 0 if passed else 1


def _load_from_args(args: argparse.Namespace, *, prompt_unlock: bool = True):
    prompt_secrets = args.command not in NO_UNLOCK_COMMANDS
    kwargs = dict(
        username=args.username or "",
        password=args.password or "",
        certificate=args.cert or "",
        certificate_password=args.cert_password or "",
        environment=args.env,
        oasis_url=getattr(args, "oasis_url", "") or "",
        backend=args.backend or "",
        downloads_dir=args.downloads or "",
        prompt_unlock=prompt_unlock and prompt_secrets,
    )
    if prompt_secrets and not kwargs["password"] and not args.password:
        if not credentials_exist():
            kwargs["password"] = getpass.getpass("PJM password: ") if False else ""
    return load_settings(**kwargs)


def _cmd_config(settings) -> int:
    print("Resolved configuration:")
    for key, val in [
        ("backend", settings.backend),
        ("environment", settings.environment),
        ("oasis_url", settings.oasis_base_url),
        ("username", settings.username or "(not set)"),
        ("password", "***" if settings.password else "(not set)"),
        ("certificate", settings.certificate_path or "(not set)"),
        ("credentials", credentials_path() if credentials_exist() else "(not set)"),
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
        print("No certificate configured. Run: pjm-api init")
        return 1
    report = inspect_certificate(settings.certificate_path, settings.certificate_password)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        for line in [
            f"path:       {report.path}",
            f"kind:       {report.kind.value}",
            f"subject:    {report.subject or '(unknown)'}",
            f"expires:    {report.not_after.date() if report.not_after else '(unknown)'}",
        ]:
            print(line)
        for w in report.warnings:
            print(f"WARN: {w}")
        for e in report.errors:
            print(f"ERROR: {e}")
    return 0 if report.healthy else 2


def _cmd_auth_check(settings, args) -> int:
    settings.validate()
    with OasisClient(settings) as client:
        client.authenticate()
        print("SSO authentication: OK")
        if args.full:
            resp = client.smoke_transserv()
            print(f"TRANSSERV smoke: {'OK' if resp.ok else 'FAIL'}")
            return 0 if resp.ok else 1
    return 0


def _save_response(resp, settings, save_path: str | None, outfile: str | None) -> None:
    if save_path:
        path = Path(save_path)
    elif outfile:
        path = settings.downloads_dir / outfile
    else:
        return
    print(f"Saved: {resp.save(path)}")


def _cmd_smoke_native(settings, args) -> int:
    settings.downloads_dir.mkdir(parents=True, exist_ok=True)
    with OasisClient(settings) as client:
        params = {"OUTPUT_FORMAT": args.output_format} if args.output_format else None
        resp = client.request("TRANSSERV", params or {}) if params else client.smoke_transserv()
        _save_response(resp, settings, args.save, args.outfile)
        print(f"TRANSSERV: {'OK' if resp.ok else 'FAIL'}")
        return 0 if resp.ok else 1


def _cmd_template_native(settings, args) -> int:
    if args.outfile:
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
        _save_response(resp, settings, args.save, args.outfile)
        if args.preview_chars:
            print(resp.text()[: args.preview_chars])
        return 0 if resp.ok else 1


def _cmd_templates(args) -> int:
    if args.templates_cmd == "list":
        for info in list_templates():
            print(f"{info.name:20} {info.description}")
        return 0
    info = get_template_info(args.name)
    if not info:
        print(f"Unknown template: {args.name}")
        return 1
    print(json.dumps(info.__dict__, indent=2, default=list))
    return 0


def _handle_error(exc: Exception) -> int:
    if isinstance(exc, PJMError):
        print(f"Error: {exc}", file=sys.stderr)
        if exc.fix:
            print(f"Fix:  {exc.fix}", file=sys.stderr)
        return 1
    print(f"Error: {exc}", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    configure_logging(verbose=args.verbose, quiet=args.quiet)

    try:
        if args.command == "init":
            return _cmd_init(args)
        if args.command == "templates":
            return _cmd_templates(args)
        if args.command == "cli":
            jar = install_cli_zip(Path(args.dir).expanduser(), force=args.force)
            print(f"Installed: {jar}")
            return 0
        if args.command == "credentials":
            return _cmd_credentials(args)

        settings = _load_from_args(args)

        if args.command == "config":
            return _cmd_config(settings)
        if args.command == "doctor":
            return _cmd_doctor(settings, args)
        if args.command == "cert-doctor":
            return _cmd_cert_doctor(settings, args)
        if args.command == "auth-check":
            return _cmd_auth_check(settings, args)

        settings.validate()

        if settings.backend == "cli":
            backend = CliBackend(settings)
            if args.command == "smoke":
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
                return backend.run_template(
                    template=args.name,
                    outfile=args.outfile,
                    timeout_sec=args.timeout_sec,
                    params=params,
                    action_override=args.action,
                    continuation_flag=args.continuation_flag,
                    method=args.method,
                    print_results=not args.quiet,
                ).returncode

        if args.command == "smoke":
            return _cmd_smoke_native(settings, args)
        if args.command == "template":
            return _cmd_template_native(settings, args)

    except PJMError as exc:
        return _handle_error(exc)
    except (ValueError, FileNotFoundError) as exc:
        return _handle_error(exc)

    print(f"Unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
