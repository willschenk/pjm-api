"""Quickstart: authenticate and run TRANSSERV on TRAIN."""

from pjm_api import OasisClient, load_settings


def main() -> None:
    settings = load_settings()
    with OasisClient(settings) as client:
        response = client.smoke_transserv()
        print(response.text()[:500])


if __name__ == "__main__":
    main()
