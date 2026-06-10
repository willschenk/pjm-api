from pjm_api.cli import main
from pjm_api.guide import format_api_guide


def test_guide_lists_templates():
    text = format_api_guide()
    assert "TRANSSERV" in text
    assert "pjm-api template TRANSSERV" in text
    assert "pjm-api smoke" in text


def test_guide_command():
    code = main(["guide"])
    assert code == 0
