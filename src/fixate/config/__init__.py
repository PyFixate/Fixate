"""
This is the configuration module
All available configuration is loaded into the module
Drivers are hard coded into the config to prevent issues arising from auto discovery
Must ensure driver imports are infallible to prevent program crash on start
"""
import importlib

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