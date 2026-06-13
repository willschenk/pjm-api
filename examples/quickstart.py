"""Quickstart — requires pjm-api init first."""

from pjm_api import CliBackend, load_settings


def main() -> None:
    backend = CliBackend(load_settings())
    ok = backend.smoke_test()
    print("TRANSSERV:", "OK" if ok else "FAIL")


if __name__ == "__main__":
    main()
