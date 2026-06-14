from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
NOTEBOOK = ROOT / "pjm_oasis_cli_quickstart.ipynb"


def test_readme_is_the_beginner_setup_entrypoint():
    text = README.read_text(encoding="utf-8")

    assert "https://willschenk.github.io/pjm-api/" not in text
    for expected in [
        "~/.pjm/cli/pjm-cli.jar",
        "~/.pjm/credentials.enc",
        "pjm-api doctor --offline",
        "from pjm_api import CliBackend, load_settings",
        "CliBackend(load_settings())",
    ]:
        assert expected in text


def test_readme_keeps_simple_explainer_diagrams():
    text = README.read_text(encoding="utf-8")

    assert "flowchart TD" in text
    assert "sequenceDiagram" in text


def test_notebook_teaches_persistent_import_path():
    text = NOTEBOOK.read_text(encoding="utf-8")

    for expected in [
        "USE_SAVED_SETUP",
        "PJM_MASTER_PASSWORD",
        "use_credentials_file=USE_SAVED_SETUP",
        "CliBackend(load_settings())",
    ]:
        assert expected in text
