from fixate.config import RESOURCES
from fixate.config.local_config import load_local_config
import fixate.sequencer

__version__ = '0.4.3'

RESOURCES["SEQUENCER"] = fixate.sequencer.Sequencer()
load_local_config()
