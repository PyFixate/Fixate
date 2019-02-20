"""
funcgen is the function generator driver.

Use funcgen.open to connect to a connected digital multi meter
Functions are dictacted by the metaclass in helper.py

Usage:
myfuncgen = funcgen.open()
myfuncgen.function('sin', freq='1kHz')
myfuncgen.function('square', 'ch2', amplit=5, offset=2.5, freq='1kHz')
myfuncgen.output_ch1 = True
myfuncgen.output_ch2 = True

functions:
function(self, *mode, **mode_params):
adv_function(self, *mode, **mode_params):
reset(self):

properties:
output_ch1
output_ch2
output_ch3
output_ch4
"""
from fixate.drivers.funcgen.helper import open, FuncGen
