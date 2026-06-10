from pjm_api.templates import get_template_info, list_templates, suggest_params


def test_list_templates():
    templates = list_templates()
    assert any(t.name == "TRANSSERV" for t in templates)


def test_get_template_info():
    info = get_template_info("transserv")
    assert info is not None
    assert info.name == "TRANSSERV"


def test_suggest_params():
    params = suggest_params("TRANSSERV")
    assert "OUTPUT_FORMAT" in params


def test_unknown_template():
    assert get_template_info("NOTREAL") is None
    assert suggest_params("NOTREAL") == {}
