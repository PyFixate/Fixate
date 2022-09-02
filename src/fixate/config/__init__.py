"""
This is the configuration module
All available configuration is loaded into the module
Drivers are hard coded into the config to prevent issues arising from auto discovery
Must ensure driver imports are infallible to prevent program crash on start
"""
from fixate.config.helper import (
    load_dict_config,
    load_yaml_config,
    get_plugin_data,
    get_plugins,
    get_config_dict,
    render_template,
)
import os.path
import json
import dataclasses
from typing import Dict, List, Optional
import enum
import re
import platformdirs
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

CONFIG_DIRECTORY = Path(platformdirs.site_config_dir("Fixate", False))
LOG_DIRECTORY = Path(platformdirs.user_log_dir("Fixate", False))
INSTRUMENT_CONFIG_FILE = CONFIG_DIRECTORY / "instruments.json"


INSTRUMENTS = []
RESOURCES = {}

DEBUG = False

# Begin default "plugins"
# Use plg_ prefix with dictionary of values to indicate to fixate to install this at startup
# Default settings for csv reporting. Can be configured via yaml either removing or overriding with plg_csv
tpl_csv_path = ["{start_date_time}-{index}.csv"]
tpl_time_stamp = "{0:%Y}{0:%m}{0:%d}-{0:%H}{0:%M}{0:%S}"

plg_csv = {
    "import_name": "fixate.reporting.csv",
    "REPORT_FORMAT_VERSION": 3,
    "tpl_first_line": [
        "0",
        "Sequence",
        "started={start_date_time}",
        "fixate-version={fixate_version}",
        "test-script-name={test_script_name}",
        "report-format={REPORT_FORMAT_VERSION}",
        "index_string={index}",
    ],
}


index = None


class InstrumentType(enum.Enum):
    SERIAL = "serial"
    VISA = "visa"


@dataclasses.dataclass()
class InstrumentConfig:
    id: str
    address: str
    instrument_type: InstrumentType
    parameters: Dict[str, str]


def load_instrument_config(local_config_path: str) -> List[InstrumentConfig]:
    """read instruments.json and return the instrument config.

    instruments.json should have this shape:
    {
        "INSTRUMENTS": {
            "serial": {
                "COM37": [
                    "address: 0,checksum: 28,command: 49,model: 6823,serial_number: 3697210019,software_version: 29440,start: 170,",
                    9600
                ]
            },
            "visa": [
                [
                    "RIGOL TECHNOLOGIES,DG1022 ,DG1D144904270,,00.03.00.09.00.02.11\n",
                    "USB0::0x09C4::0x0400::DG1D144904270::INSTR"
                ],
                [
                    "FLUKE,8846A,3821015,08/02/10-11:53\r\n",
                    "ASRL38::INSTR"
                ],
                [
                    "AGILENT TECHNOLOGIES,MSO-X 3014A,MY52160892,02.41.2015102200",
                    "USB0::0x0957::0x17A8::MY52160892::INSTR"
                ]
            ]
        }
    }
    """
    local_config_data = {}
    if os.path.isfile(local_config_path):
        with open(local_config_path, "r") as f:
            local_config_data = json.load(f)
    else:
        logger.debug(f"No instrument config found at {local_config_path}")
    instruments = local_config_data.get("INSTRUMENTS", {})
    serial_instruments = instruments.get(InstrumentType.SERIAL.value, {})
    visa_instruments = instruments.get(InstrumentType.VISA.value, [])

    instrument_configs = []
    for serial_port, parameters in serial_instruments.items():
        identity, baud_rate = parameters
        instrument_configs.append(
            InstrumentConfig(
                id=identity,
                address=serial_port,
                instrument_type=InstrumentType.SERIAL,
                parameters={"baud_rate": baud_rate},
            )
        )

    for identity, visa_address in visa_instruments:
        instrument_configs.append(
            InstrumentConfig(
                id=identity,
                address=visa_address,
                instrument_type=InstrumentType.VISA,
                parameters={},
            )
        )
    return instrument_configs


def load_config(config_files: Optional[List[str]] = None):
    """
    Call to initialise various config at startup.

    By default will load the fixate.yml which mostly is used for logging options.
    It also loads the instruments.json, which is used to configure instruments
    which are connected to the test station.

    config_files is a list of yaml files. Each will be loaded. Any values
    passed in those files will override the default fixate.yml.
    """

    # Load python environment fixate config
    env_config = CONFIG_DIRECTORY / "fixate.yml"
    if os.path.exists(env_config):
        load_yaml_config(env_config)

    # Load a list of config files
    if config_files is not None:
        for config_file in config_files:
            load_yaml_config(config_file)

    INSTRUMENTS[:] = list(load_instrument_config(INSTRUMENT_CONFIG_FILE))


def find_instrument_by_id(regex_id) -> Optional[InstrumentConfig]:
    """Search for instruments whose id matches the regex passed in.

    This should probably live over in drivers module?
    """
    for instrument_config in INSTRUMENTS:
        if re.search(regex_id, instrument_config.id):
            return instrument_config
    return None
