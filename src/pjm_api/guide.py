"""Post-setup API call guide."""

from __future__ import annotations

from pjm_api.templates import list_templates


def format_api_guide() -> str:
    lines = [
        "PJM API call options",
        "",
        "Setup checks",
        "  pjm-api doctor --offline     Local credentials and certificate only",
        "  pjm-api doctor               Full check including SSO and TRANSSERV",
        "  pjm-api cert-doctor          Inspect login certificate file",
        "  pjm-api credentials show     Redacted credentials summary",
        "",
        "OASIS requests (TRAIN by default)",
        "  pjm-api smoke                TRANSSERV smoke test",
        "  pjm-api template TRANSSERV   Query a template (preview to stdout)",
        "  pjm-api template NAME --outfile result.txt   Save to downloads/",
        "  pjm-api template NAME --query-param KEY=VALUE",
        "  pjm-api templates info NAME  Common parameters for a template",
        "",
        "Available templates:",
    ]
    for info in list_templates():
        lines.append(f"  {info.name:16} {info.description}")
    lines.extend(
        [
            "",
            "Examples",
            "  pjm-api template TRANSSERV",
            "  pjm-api template TRANSSERV --preview-chars 500",
            "  pjm-api smoke --env TRAIN",
            "",
            "Python: docs/python-usage.md",
            "Full setup: docs/setup.md",
        ]
    )
    return "\n".join(lines)
