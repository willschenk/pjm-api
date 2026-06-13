import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = Path("pjm_oasis_cli_quickstart.ipynb")


def test_single_notebook_is_valid_json():
    notebooks = [
        path.relative_to(ROOT)
        for path in ROOT.rglob("*.ipynb")
        if ".venv" not in path.parts and ".ipynb_checkpoints" not in path.parts
    ]
    assert notebooks == [NOTEBOOK]
    data = json.loads((ROOT / NOTEBOOK).read_text(encoding="utf-8"))
    assert data["nbformat"] == 4


def test_notebook_has_no_local_secrets_or_private_urls():
    text = (ROOT / NOTEBOOK).read_text(encoding="utf-8")
    forbidden = [
        "7Bing" + "America",
        "sche" + "nc",
        "Hotline" + "2",
        "Personal" + "/Projects",
        "mega" + "watt",
        "oasis" + ".test" + ".pjm",
        "ac1" + "stage",
    ]
    for value in forbidden:
        assert value not in text


def test_notebook_does_not_require_interactive_prompt_support():
    text = (ROOT / NOTEBOOK).read_text(encoding="utf-8")
    assert "input(" not in text
    assert "getpass" not in text


def test_notebook_uses_package_helpers_instead_of_local_functions():
    data = json.loads((ROOT / NOTEBOOK).read_text(encoding="utf-8"))
    code = "\n".join(
        "".join(cell.get("source", []))
        for cell in data["cells"]
        if cell.get("cell_type") == "code"
    )
    assert "from pjm_api" in code
    assert "\ndef " not in code


def test_notebook_teaches_default_cli_jar_lookup():
    text = (ROOT / NOTEBOOK).read_text(encoding="utf-8")
    assert "~/.pjm/cli/pjm-cli.jar" in text
    assert "default jar lookup" in text
