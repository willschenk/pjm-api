from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "index.html"
PAGES_WORKFLOW = ROOT / ".github" / "workflows" / "pages.yml"


class _HTMLCheck(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.buttons = 0
        self.svgs = 0
        self.scripts = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        del attrs
        if tag == "button":
            self.buttons += 1
        if tag == "svg":
            self.svgs += 1
        if tag == "script":
            self.scripts += 1


def test_github_pages_guide_is_valid_static_html():
    parser = _HTMLCheck()
    parser.feed(PAGE.read_text(encoding="utf-8"))
    assert parser.buttons >= 6
    assert parser.svgs >= 2
    assert parser.scripts == 1


def test_github_pages_guide_teaches_beginner_setup_path():
    text = PAGE.read_text(encoding="utf-8")
    for expected in [
        "pjm-api setup, explained",
        "pjm-api cli install --dir ~/.pjm/cli",
        "pjm-api init",
        "pjm-api doctor",
        "CliBackend",
        "load_settings",
    ]:
        assert expected in text


def test_pages_workflow_publishes_docs_directory():
    text = PAGES_WORKFLOW.read_text(encoding="utf-8")
    assert "enablement: true" in text
    assert "actions/upload-pages-artifact@v3" in text
    assert "path: docs" in text
    assert "actions/deploy-pages@v4" in text
