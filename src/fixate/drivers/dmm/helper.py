class DMM:
    REGEX_ID = "DMM"
    is_connected = False

    def measurement(self):
        raise NotImplementedError

    def voltage_ac(self, _range=None):
        raise NotImplementedError

    def voltage_dc(self, _range=None):
        raise NotImplementedError

    def current_ac(self, _range):
        raise NotImplementedError

    def current_dc(self, _range):
        raise NotImplementedError

    def analog_filter(self, bandwidth=None):
        raise NotImplementedError

    def digital_filter(self):
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

    def temperature(self):
        raise NotImplementedError

    def ftemperature(self):
        raise NotImplementedError

    def continuity(self):
        raise NotImplementedError

    def diode(self, low_current=True, high_voltage=False):
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError

    def get_identity(self):
        raise NotImplementedError
