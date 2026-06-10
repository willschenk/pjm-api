"""Quickstart — requires pjm-api init first."""

from pjm_api import OasisClient, load_settings


def main() -> None:
    with OasisClient(load_settings()) as client:
        response = client.smoke_transserv()
        print(response.text()[:500])


if __name__ == "__main__":
    main()
