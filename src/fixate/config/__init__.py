"""
This is the configuration module
All available configuration is loaded into the module
Drivers are hard coded into the config to prevent issues arising from auto discovery
Must ensure driver imports are infallible to prevent program crash on start
"""
import importlib
from fixate.config.helper import load_dict_config, load_json_config, load_yaml_config, get_plugin_data

DRIVER_LIST = {"DMM": {"dmm.fluke_8846a.Fluke8846A"},
               "FUNC_GEN": {"funcgen.rigol_dg1022.RigolDG1022", "funcgen.keysight_33500b.Keysight33500B"},
               "DAQ": {"daq.daqmx.DaqMx"},
               "LCR": {"lcr.agilent_u1732c.AgilentU1732C"},
               "PROGRESSION": {"progression.Progression"},
               "PPS": {'pps.bk_178x.BK178X', 'pps.siglent_spd_3303X.SPD3303X'},
               "DSO": {'dso.agilent_mso_x.MSO_X_3000'},
               "FTDI": {"ftdi.FTDI2xx"}}
CONFIG_LOADED = False
CLASS_LIST = None
INSTRUMENTS = {}
DUT = None
RESOURCES = {}
DRIVERS = {}
ASYNC_TASKS = []
DEBUG = False
importer = None
plugins = {
    "fixate.reporting.csv": {
        "REPORT_FORMAT_VERSION": 3,
        "tpl_time_stamp": "{0:%Y}{0:%m}{0:%d}-{0:%H}{0:%M}{0:%S}",
        "tpl_csv_path": ["{fixate.config.plugins[fixate.reporting.csv][tpl_time_stamp]}-{index}.csv"],
        "tpl_first_line": [
            "0",
            'Sequence',
            "started={start_date_time}",
            "fixate-version={fixate_version}",
            "test-script-name={test_script_name}",
            "test_script-version={test_script_version}",
            "report-format={REPORT_FORMAT_VERSION}",
            "part_number={part_number}",
            "module={module}",
            "serial_number={serial_number}",
            "index_string={index_string}"]
    }}
# Import the drivers from the DRIVER_LIST
for key, value in DRIVER_LIST.items():
    for drv in value:
        imp_path = '.'.join(drv.split('.')[:-1])
        cls = drv.split('.')[-1]

        if DRIVERS.get(key, None) is None:
            DRIVERS[key] = []
        try:
            DRIVERS[key].append((cls, getattr(importlib.import_module('fixate.drivers.' + imp_path), cls)))
        except Exception as e:
            # print(repr(e))
            pass
