__version__ = "0.5.7"

import fixate.sequencer
import fixate.config
# Create the global sequencer here so it can be imported and 
#   used elsewhere with better traceability/type-hints/auto-complete
global_sequencer = fixate.sequencer.Sequencer()
# Plan to deprecate calls to RESOURCES[] and gradual replace.
#   Keep here now for backwards-compatibility with test_scripts
fixate.config.RESOURCES["SEQUENCER"] = global_sequencer
