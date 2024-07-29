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


@pytest.fixture
def open_config_file(test_app):
    test_app.do_open("src/fixate/config/local_config.json.tmpl")
    yield test_app


def test_open_fxconfig_no_file(test_app):
    with pytest.raises(Exception):
        # there should be no file at the default path at this point.
        test_app.do_open("")


@pytest.mark.windows
def test_new_config_file_default(test_app, capfd):
    # on windows, the default path should work without elevation.
    # on mac, the default path required fxconfig to be run with elevated permissions.
    test_app.do_new("")
    out = capfd.readouterr()
    assert (out.out).strip() == f"Config loaded: {config_util.INSTRUMENT_CONFIG_FILE}"


def test_new_config_file(test_app, config_file_dir, capfd):
    # don't want to use the default path.
    # the default path (based on `INSTRUMENT_CONFIG_FILE`) on mac apparently doesn't work because of permissions.
    test_app.do_new(config_file_dir + "/test_config.json")
    out = capfd.readouterr()
    assert (
        out.out
    ).strip() == f"Config loaded: {config_file_dir + '/test_config.json'}"


def test_new_config_file_exists(test_app, config_file_dir):
    # create an empty file, could also just call do_new twice.
    with open(config_file_dir + "/test_config.json", "w") as f:
        f.write("")

    with pytest.raises(Exception):
        test_app.do_new(config_file_dir + "/test_config.json")


def test_open_fxconfig(test_app, capfd):
    # use the template config file to test the open command.
    test_app.do_open("src/fixate/config/local_config.json.tmpl")
    out = capfd.readouterr()
    assert (
        out.out
    ).strip() == f"Config loaded: {'src/fixate/config/local_config.json.tmpl'}"


def test_list_existing(test_app, open_config_file, capfd):
    test_app.do_list("existing")
    out = capfd.readouterr()
    print(out.out)
    assert (
        out.out
    ).strip() == "VISA || USB0::0x09C4::0x0400::DG1D144904270::INSTR || RIGOL TECHNOLOGIES,DG1022 ,DG1D144904270,,00.03.00.09.00.02.11\nVISA || ASRL38::INSTR || FLUKE,8846A,3821015,08/02/10-11:53\nVISA || USB0::0x0957::0x17A8::MY52160892::INSTR || AGILENT TECHNOLOGIES,MSO-X 3014A,MY52160892,02.41.2015102200\nSERIAL || COM37 || ['address: 0,checksum: 28,command: 49,model: 6823,serial_number: 3697210019,software_version: 29440,start: 170,', 9600]"
