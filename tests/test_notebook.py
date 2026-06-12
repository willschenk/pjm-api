import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_single_notebook_is_valid_json():
    notebooks = [
        path.relative_to(ROOT)
        for path in ROOT.rglob("*.ipynb")
        if ".venv" not in path.parts and ".ipynb_checkpoints" not in path.parts
    ]
    assert notebooks == [Path("debug.ipynb")]
    data = json.loads((ROOT / "debug.ipynb").read_text(encoding="utf-8"))
    assert data["nbformat"] == 4


def test_notebook_has_no_local_secrets_or_private_urls():
    text = (ROOT / "debug.ipynb").read_text(encoding="utf-8")
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
