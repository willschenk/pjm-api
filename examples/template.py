"""Generic template query — requires pjm-api init first."""

from pjm_api import OasisClient, load_settings
from pjm_api.templates import suggest_params


def main() -> None:
    params = suggest_params("TRANSSERV")
    with OasisClient(load_settings()) as client:
        response = client.request("TRANSSERV", params)
        print(response.text()[:1000])


if __name__ == "__main__":
    main()
