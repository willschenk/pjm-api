
from pjm_api.response import OasisResponse


def test_text_and_save(tmp_path):
    resp = OasisResponse(200, {}, b"hello", "T", "TRAIN")
    assert resp.text() == "hello"
    assert resp.save(tmp_path / "x.txt").read_text() == "hello"


def test_json_parse():
    resp = OasisResponse(200, {}, b"[1,2]", "T", "TRAIN")
    assert resp.json() == [1, 2]


def test_ok_property():
    assert OasisResponse(200, {}, b"", "T", "TRAIN").ok
    assert not OasisResponse(500, {}, b"", "T", "TRAIN").ok
