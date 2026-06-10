from pjm_api.oasis_cli import (
    filename_only,
    get_env_url,
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


def test_qualify_result_with_criteria():
    assert qualify_result_with_criteria(
        0, "SUCCESS", "", code_equals=0, stdout_contains_all=["SUCCESS"], stderr_must_be_empty=True
    )
    assert not qualify_result_with_criteria(1, "SUCCESS", "", code_equals=0)


def test_parse_key_value_pairs():
    assert parse_key_value_pairs(["OUTPUT_FORMAT=DATA"]) == {"OUTPUT_FORMAT": "DATA"}
