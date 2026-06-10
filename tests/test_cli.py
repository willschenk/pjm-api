from pjm_api.cli import main


def test_cli_config_exit_code():
    code = main(["config"])
    assert code in (0, 1)


def test_cli_templates_list():
    code = main(["templates", "list"])
    assert code == 0
