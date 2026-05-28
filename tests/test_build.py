from click.testing import CliRunner

from krillbuild import cli

def test_hello_world():
    runner = CliRunner()
    result = runner.invoke(cli, ['Peter'])
    assert result.exit_code == 0
    assert result.output == 'Hello Peter!\n'