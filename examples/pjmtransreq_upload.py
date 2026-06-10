"""Upload a CSV via pjmtransreq template."""

from pathlib import Path

from pjm_api import OasisClient, load_settings


def main() -> None:
    csv_path = Path("request.csv")
    if not csv_path.exists():
        raise SystemExit("Place your CSV at request.csv")

    settings = load_settings(environment="TRAIN")
    with OasisClient(settings) as client:
        response = client.submit_transmission_request(csv_path)
        print(response.text()[:1000])


if __name__ == "__main__":
    main()
