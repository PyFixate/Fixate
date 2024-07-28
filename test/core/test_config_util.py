from tempfile import TemporaryDirectory
import pytest
from fixate.core import config_util
import cmd2_ext_test


class FxConfigTester(cmd2_ext_test.ExternalTestMixin, config_util.FxConfigCmd):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


@pytest.fixture
def test_app():
    app = FxConfigTester()
    app.fixture_setup()
    yield app
    app.fixture_teardown()


@pytest.fixture
def config_file_dir():
    with TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_open_fxconfig_no_file(test_app):
    with pytest.raises(FileNotFoundError):
        # there should be no file at the default path at this point.
        test_app.do_open("")


def test_new_config_file(test_app, config_file_dir):
    # don't want to use the default path.
    # the default path (based on `INSTRUMENT_CONFIG_FILE`) on mac apparently doesn't work because of permissions.
    out = test_app.do_new(config_file_dir + "/test_config.json")
    assert (
        out.out
    ).strip() == f"Config loaded: {config_file_dir + '/test_config.json'}"
