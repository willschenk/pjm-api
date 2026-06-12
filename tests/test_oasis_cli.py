import pytest

from pjm_api.config import get_env_url
from pjm_api.oasis_cli import (
    filename_only,
    mask_command_for_display,
    normalize_template_name,
    parse_key_value_pairs,
    qualify_result_with_criteria,
)


def test_normalize_template_name():
    assert normalize_template_name("transserv") == "TRANSSERV"


def test_filename_only():
    assert filename_only(r"C:\downloads\foo.txt") == "foo.txt"


def test_get_env_url():
    assert "train" in get_env_url("TRAIN").lower()


def test_mask_command_for_display():
    cmd = ["java", "-p", "secret", "-r", "cert|pass"]
    masked = mask_command_for_display(cmd)
    assert masked[2] == "***REDACTED***"


def test_make_template_cmd_shape(monkeypatch, tmp_path):
    jar = tmp_path / "pjm-cli.jar"
    jar.write_bytes(b"jar")
    monkeypatch.setenv("PJM_CLI_JAVA_PATH", "java")
    monkeypatch.setenv("PJM_CLI_JAR_PATH", str(jar))
    monkeypatch.setenv("PJM_USERNAME", "user")
    monkeypatch.setenv("PJM_PASSWORD", "pass")
    monkeypatch.setenv("PJM_CERT", "/tmp/cert.p12|pw")
    monkeypatch.setenv("PJM_ENV", "TRAIN")
    monkeypatch.setenv("PJM_BACKEND", "cli")

    from pjm_api.oasis_cli import make_template_cmd

    cmd = make_template_cmd(template="TRANSSERV", env="TRAIN")
    assert "java" in cmd
    assert str(jar) in cmd
    assert "TEMPLATE=TRANSSERV" in cmd
    assert "-t" not in cmd
    assert cmd[cmd.index("-s") + 2] == "-a"
    assert cmd.index("-o") > max(i for i, part in enumerate(cmd) if part == "-q")
    assert cmd[-2:] == ["-z", "180000"]


def test_qualify_result_with_criteria():
    assert qualify_result_with_criteria(
        0, "SUCCESS", "", code_equals=0, stdout_contains_all=["SUCCESS"], stderr_must_be_empty=True
    )
    assert not qualify_result_with_criteria(1, "SUCCESS", "", code_equals=0)


def test_parse_key_value_pairs_valid():
    assert parse_key_value_pairs(["RETURN_TZ=EP"]) == {"RETURN_TZ": "EP"}


def test_parse_key_value_pairs_allows_empty_value():
    assert parse_key_value_pairs(["OUTPUT_FORMAT="]) == {"OUTPUT_FORMAT": ""}


def test_parse_key_value_pairs_missing_equals_sign():
    with pytest.raises(ValueError, match=r"Invalid query parameter 'BAD'\. Use KEY=VALUE\."):
        parse_key_value_pairs(["BAD"])


def test_parse_key_value_pairs_empty_key():
    with pytest.raises(
        ValueError, match=r"Invalid query parameter '=VALUE'\. Key cannot be empty\."
    ):
        parse_key_value_pairs(["=VALUE"])


def test_parse_key_value_pairs_duplicate_keys_last_value_wins():
    assert parse_key_value_pairs(["OUTPUT_FORMAT=DATA", "OUTPUT_FORMAT=JSON"]) == {
        "OUTPUT_FORMAT": "JSON"
    }
