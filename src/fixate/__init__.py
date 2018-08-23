from fixate.config import CONFIG_LOADED, RESOURCES
from fixate.config.local_config import setup_config
from .__main__ import run_main_program

__version__ = '0.2.2'

if not CONFIG_LOADED:
    setup_config()
