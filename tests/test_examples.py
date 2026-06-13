from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = [
    ROOT / "examples" / "quickstart.py",
    ROOT / "examples" / "template.py",
    ROOT / "examples" / "template_query.py",
]


def test_copyable_examples_use_cli_backend():
    for path in EXAMPLES:
        text = path.read_text(encoding="utf-8")
        assert "CliBackend" in text
        assert "OasisClient" not in text
