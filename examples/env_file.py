"""Load configuration from a .env file."""

try:
    from dotenv import load_dotenv
except ImportError as exc:
    raise SystemExit("Install dotenv extra: pip install pjm-api[dotenv]") from exc

from pjm_api import load_settings


def main() -> None:
    load_dotenv()
    settings = load_settings()
    print(f"Environment: {settings.environment}")
    print(f"Backend:     {settings.backend}")
    print(f"OASIS URL:   {settings.oasis_base_url}")


if __name__ == "__main__":
    main()
