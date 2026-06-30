from featurization import get_package_info, get_cli_command_names


def test_get_cli_command_names():
    commands = get_cli_command_names()
    assert isinstance(commands, list)
    assert "init" in commands
    assert "run" in commands
    assert "bootstrap" in commands
    assert "advise" in commands


def test_get_package_info():
    info = get_package_info()
    assert isinstance(info, dict)
    assert info["package_name"] == "kmds-featurization"
    assert info["entry_point"] == "featurization-cli"
    assert "version" in info
    assert isinstance(info["cli_commands"], list)
    assert "run" in info["cli_commands"]
    assert "documentation_note" in info


def test_client_onboarding_metadata():
    info = get_package_info()
    assert info["package_name"] == "kmds-featurization"
    assert info["entry_point"] == "featurization-cli"
    assert "cli_commands" in info
    assert set(["init", "bootstrap", "run", "advise"]).issubset(set(info["cli_commands"]))
    assert "documentation_note" in info
