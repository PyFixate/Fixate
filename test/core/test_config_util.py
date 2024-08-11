import pytest
from fixate.core import config_util
from fixate import config


# Ideally these tests would be done with the cmd2 test plugin (https://pypi.org/project/cmd2-ext-test/)
# by the people who made CMD2, however it have proved to be more work than it is worth.
# So the tests will focus on the internal methods of the FxConfigCmd class.


class FxConfigTester(config_util.FxConfigCmd):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


@pytest.fixture
def test_app():
    app = config_util.FxConfigCmd()
    yield app


@pytest.fixture
def open_config_file(test_app):
    test_app.do_open("test/config/instruments.json")
    yield test_app


def test_open_fxconfig_no_file(test_app, monkeypatch):
    # for local testing we don't want the tests picking up the default config file.
    # So patch it to simulate no file.
    monkeypatch.setattr(config, "INSTRUMENT_CONFIG_FILE", "")
    with pytest.raises(Exception):
        # there should be no file at the default path at this point.
        test_app.do_open("")


def test_new_config_file_default(test_app, monkeypatch, tmp_path):
    # monkeypath the default path to 1: avoid the default path and 2: avoid permissions issues on mac.
    monkeypatch.setattr(config, "INSTRUMENT_CONFIG_FILE", tmp_path / "test_config.json")
    test_app.do_new("")
    assert test_app.config_file_path == config.INSTRUMENT_CONFIG_FILE
    assert test_app.updated_config_dict == {"INSTRUMENTS": {"visa": [], "serial": {}}}


def test_new_config_file_with_path(test_app, tmp_path):
    test_app.do_new(tmp_path / "test_config.json")
    assert test_app.config_file_path == tmp_path / "test_config.json"
    assert test_app.updated_config_dict == {"INSTRUMENTS": {"visa": [], "serial": {}}}


def test_new_config_file_exists(test_app, tmp_path):
    # create an empty file, could also just call do_new twice.
    with open(tmp_path / "test_config.json", "w") as f:
        f.write("")

    with pytest.raises(Exception):
        test_app.do_new(tmp_path / "test_config.json")


def test_open_fxconfig(test_app):
    test_app.do_open("test/config/instruments.json")
    assert test_app.config_file_path == "test/config/instruments.json"
    assert test_app.updated_config_dict == {
        "INSTRUMENTS": {
            "visa": [
                [
                    "RIGOL TECHNOLOGIES,DG1022 ,DG1D144904270,,00.03.00.09.00.02.11\n",
                    "USB0::0x09C4::0x0400::DG1D144904270::INSTR",
                ],
                ["FLUKE,8846A,3821015,08/02/10-11:53\r\n", "ASRL38::INSTR"],
                [
                    "AGILENT TECHNOLOGIES,MSO-X 3014A,MY52160892,02.41.2015102200",
                    "USB0::0x0957::0x17A8::MY52160892::INSTR",
                ],
            ],
            "serial": {
                "COM37": [
                    "address: 0,checksum: 28,command: 49,model: 6823,serial_number: 3697210019,software_version: 29440,start: 170,",
                    9600,
                ]
            },
        }
    }


# testing the _add_visa_to_config method directly since there is too much reliance on the ResourceManager
# which would need to be monkeypatched or mocked.
def test_add_visa_to_config_duplicate(test_app, open_config_file):
    before_add = test_app.updated_config_dict["INSTRUMENTS"]["visa"]
    test_app._add_visa_to_config(
        "FLUKE,8846A,3821015,08/02/10-11:53\r\n", "ASRL38::INSTR"
    )
    assert before_add == test_app.updated_config_dict["INSTRUMENTS"]["visa"]


def test_add_visa_to_config(test_app, open_config_file):
    test_app._add_visa_to_config(
        "FLUKE,8846A,3821015,08/02/10-11:55\r\n", "ASRL39::INSTR"
    )
    assert (
        test_app.updated_config_dict["INSTRUMENTS"]["visa"][-1][0]
        == "FLUKE,8846A,3821015,08/02/10-11:55\r\n"
    )
    assert test_app.updated_config_dict["INSTRUMENTS"]["visa"][-1][1] == "ASRL39::INSTR"


def test_add_serial_error(test_app):
    with pytest.raises(Exception):
        test_app.do_add("serial com38")


def test_add_serial_duplicate(test_app, monkeypatch, open_config_file):
    monkeypatch.setattr(
        config_util,
        "serial_id_query",
        lambda x, y: "address: 0,checksum: 28,command: 49,model: 6823,serial_number: 3697210019,software_version: 29440,start: 170,",
    )
    before_add = test_app.updated_config_dict["INSTRUMENTS"]["serial"]
    test_app.do_add("serial COM37 9600")
    assert before_add == test_app.updated_config_dict["INSTRUMENTS"]["serial"]
