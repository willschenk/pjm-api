"""Use the official PJM Java CLI fallback backend."""

from pjm_api.cli_adapter import CliBackend
from pjm_api.config import load_settings


def main() -> None:
    settings = load_settings(backend="cli", environment="TRAIN")
    backend = CliBackend(settings)
    ok = backend.smoke_test(print_results=True)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
