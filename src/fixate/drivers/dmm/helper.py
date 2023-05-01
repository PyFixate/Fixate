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
        Use remote() to restore remote operation.
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

    def measurement(self):
        raise NotImplementedError

    def voltage_ac(self, _range=None):
        raise NotImplementedError

    def voltage_dc(self, _range=None, auto_impedance=False):
        raise NotImplementedError

    def current_ac(self, _range):
        raise NotImplementedError

    def current_dc(self, _range):
        raise NotImplementedError

    def resistance(self, _range=None):
        raise NotImplementedError

    def frequency(self, _range=None):
        raise NotImplementedError

    def fresistance(self, _range=None):
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
