import pytest

from pjm_api.exceptions import PJMOasisError
from pjm_api.oasis import build_query_params, build_template_url, normalize_template_name
from pjm_api.response import OasisResponse


def test_normalize_template_name():
    assert normalize_template_name("transserv") == "TRANSSERV"


def test_build_template_url():
    url = build_template_url("https://oasis.ac1train.pjm.com/OASIS/", "TRANSSERV")
    assert url.endswith("rest/secure/transserv")


def test_build_query_params():
    params = build_query_params("TRANSSERV", {"VERSION": "3.3"}, output_format="DATA")
    assert params["TEMPLATE"] == "TRANSSERV"
    assert params["OUTPUT_FORMAT"] == "DATA"
    assert params["VERSION"] == "3.3"


def test_invalid_output_format():
    with pytest.raises(PJMOasisError):
        build_query_params("TRANSSERV", output_format="INVALID")


def test_response_helpers(tmp_path):
    resp = OasisResponse(
        status_code=200,
        headers={},
        content=b'{"ok": true}',
        template="TRANSSERV",
        environment="TRAIN",
    )
    assert resp.json() == {"ok": True}
    assert resp.text() == '{"ok": true}'
    path = resp.save(tmp_path / "out.json")
    assert path.exists()
