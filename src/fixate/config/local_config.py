import os
from io import StringIO
import json

import visa

import fixate.config
from fixate.core.ui import user_info
from fixate.sequencer import Sequencer

local_vars = ["INSTRUMENTS"]
local_config_path = os.path.join(os.path.dirname(__file__), 'local_config.json')
local_data_path = os.path.join(os.path.dirname(__file__), 'drivers.data')


def load_local_config():
    if os.path.isfile(local_config_path):
        with open(local_config_path, 'r') as f:
            fixate.config.load_json_config(f)
    else:
        # Build local config from discovery
        pass


def save_local_config():
    backup = StringIO()
    if os.path.isfile(local_config_path):
        # Backup local config
        with open(local_config_path, 'r') as f:
            backup.write(f.read())

    try:
        with open(local_config_path, 'w') as f:
            f.write(json.dumps({k: getattr(fixate.config, k) for k in local_vars},
                               sort_keys=True,
                               indent=4,
                               separators=(',', ': ')))
    except:
        # Restore from backup
        with open(local_config_path, 'w') as f:
            backup.seek(0)
            f.write(backup.read())
        raise


def setup_config():
    """
     Configuration that is initialised on first import of fixate
    :return:
    """
    try:
        fixate.config.RESOURCES["VISA_RESOURCE_MANAGER"] = visa.ResourceManager()
    except:
        fixate.config.RESOURCES["VISA_RESOURCE_MANAGER"] = None
        user_info("Warning no PyVISA install found")

    fixate.config.RESOURCES["SEQUENCER"] = Sequencer()
    fixate.config.CONFIG_LOADED = True