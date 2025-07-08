from dataclasses import dataclass
from typing import Literal


class DMM:
    REGEX_ID = "DMM"
    is_connected = False

    def remote(self):
        """
        Sets instrument to remote mode
        """
        raise NotImplementedError

    def local(self):
        """
        Sets instrument to local mode
        Use `remote()` to restore remote operation.
        """
        raise NotImplementedError

    def set_manual_trigger(self, samples=1):
        """
        Setup instrument for manual triggering.
        :param samples: Number of samples to take per trigger event
        """
        raise NotImplementedError

    def trigger(self):
        """
        Manually trigger measurement and store in instrument buffer.
        """
        raise NotImplementedError

    def measurement(self, delay=None):
        """
        Trigger and return measurement from the instrument buffer.

        Args:
            delay (bool): If True, waits for `self.measurement_delay` seconds then triggers a measurement.

        Returns:
            float: measured value
        """
        raise NotImplementedError

    def voltage_ac(self, _range=None):
        """
        Sets the DMM in AC voltage measurement mode and puts it in the range given
        by the argument _range. Signals expected to be measured must be < _range.

        Args:
            _range (???): The range to set the DMM to.
        """
        raise NotImplementedError

    def voltage_dc(self, _range=None, auto_impedance=False):
        """
        Sets the DMM in DC voltage measurement mode and puts it in the range given
        by the argument _range. Signals expected to be measured must be < _range.
        """
        raise NotImplementedError

    def current_ac(self, _range, port: Literal["HIGH", "LOW"]):
        """
        Sets the DMM in AC current measurement mode and puts it in the range given
        by the argument _range. Signals expected to be measured must be < _range.
        """
        raise NotImplementedError

    def current_dc(self, _range, port: Literal["HIGH", "LOW"]):
        """
        Sets the DMM in DC current measurement mode and puts it in the range given
        by the argument _range. Signals expected to be measured must be < _range.
        """
        raise NotImplementedError

    def resistance(self, _range=None):
        """
        Sets the DMM in 2-wire resistance measurement mode and puts it in the range
        given by the argument _range. Signals expected to be measured must be < _range.
        """
        raise NotImplementedError

    def frequency(self, _range=None):
        raise NotImplementedError

    def fresistance(self, _range=None):
        """
        Sets the DMM in 4-wire resistance measurement mode and puts it in the range
        given by the argument _range. Signals expected to be measured must be < _range.
        """
        raise NotImplementedError

    def period(self, _range=None):
        raise NotImplementedError

    def capacitance(self, _range=None):
        raise NotImplementedError

    def continuity(self):
        raise NotImplementedError

    def diode(self, low_current=True, high_voltage=False):
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError

    def get_identity(self):
        raise NotImplementedError

    @dataclass
    class MeasurementStats:
        min: float
        max: float
        avg: float

    # context manager for setting NPLC
    class _nplc_context_manager(object):
        def __init__(self, dmm, nplc=None):
            self.dmm = dmm
            self.nplc = nplc
            self.original_nplc = None

        def __enter__(self):
            # store the original NPLC setting
            self.original_nplc = self.dmm.get_nplc()
            self.dmm.set_nplc(self.nplc)

        # return to default NPLC setting
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.dmm.set_nplc(self.original_nplc)

    def nplc(self, nplc=None):
        return self._nplc_context_manager(self, nplc)
