import os
import fixate.config

local_config_path = os.path.join(os.path.dirname(__file__), 'local_config.json')


def load_local_config():
    if os.path.isfile(local_config_path):
        with open(local_config_path, 'r') as f:
            fixate.config.load_json_config(f)
