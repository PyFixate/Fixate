import time
from fixate.core.exceptions import ParameterError, InstrumentError


def _range_gen(value=None):
    if value is None:
        while True:
            yield True
    else:
        for _ in range(value + 1):
            yield True


def converge_scalar_tolerance(
    dmm,
    funcgen,
    set_point,
    tolerance,
    limit_amplitude=None,
    settle_number=1,
    attempts=5,
):
    p = LinearScalarControl(funcgen.amplitude_ch1)
    p.set_point(set_point)
    settle_cnt = 0
    for _ in range(attempts):
        test_val = dmm.measurement()
        if test_val > 1e10:
            raise InstrumentError("Measurement outside the specified dmm range")
        # Test in range
        if set_point * (1 - tolerance) <= test_val <= set_point * (1 + tolerance):
            settle_cnt += 1
        else:
            settle_cnt = 0
        if settle_cnt >= settle_number:
            return
        # Get the control value from controller
        contr_val = p.update(test_val)
        # Put the control value into the kwargs for the control function
        if contr_val >= limit_amplitude:
            raise InstrumentError(
                "Converge function value {}Vpp exceeded the limit set {}Vpp".format(
                    contr_val, limit_amplitude
                )
            )
        funcgen.amplitude_ch1 = contr_val
    raise InstrumentError("Could not converge in {} attempts".format(attempts))


def converge_amplitude_scalar(
    dmm,
    funcgen_or_ps,
    set_point,
    cur_amplitude,
    mode=None,
    frequency=None,
    offset=0,
    retries=None,
    timeout=None,
    settle_min=None,
    settle_max=None,
    settle_number=1,
    limit_amplitude=None,
):
    """
    :param dmm:
        the instantiated class used as a dmm.
        The dmm should have the measurement type already set up
    :param funcgen_or_ps:
        the instantited class used as the control
        This can be a function generator or a programmable power supply
    :param set_point:
        The desired final resting value as measured through the dmm
    :param cur_amplitude:
        The current amplitude sent to the function generator or programmable power supply
    :param mode:
        Used for function generator and indicates the waveform
        eg. 'sin' or 'square'
    :param frequency:
        Used for function generator and indicates the waveform frequency
        eg. 1000
    :param offset:
        Used for function generator and indicates the waveform offset
        eg. 0.0
    :param retries:
    The amount of times the control is updated if it is not successful in converging first.
    Function will return True if all retries are attempted and settle parameters are not set
    Function will return False if all retries are attempted and settle parameters are set

    :param timeout:
    The amount of time the control will be updated if it is not successful in converging first or all retries attempted.
    Function will return True if timeout is reached and retries and settle parameters are not set
    Function will return False if timeout occurs and retries are set and settle parameters are set

    :param feedback_return_index:
    This is the index used from the return value.
    eg. dmm.measure()[0] would have feedback_return_index = 0
    eg. dmm.measure()["data"] would have feedback_return_index = 'data'

    :param settle_min:
    The minimum value that is considered to be at an acceptable settle point
    :param settle_max:
    The maximum value that is considered to be at an acceptable settle point
    :param settle_number:
    The number of consecutive measurements in a that are within settle_min <= value <= settle_max
    before the function returns True

    :return:
    True if converged
    False if not completed before retries or timeout
    Parameter error if parsed parameters are incompatible
    Calling functions exceptions are not handled
    """

    # Check if function gen
    # if issubclass(FuncGen, funcgen_or_ps):
    # if any(x is None for x in [mode, frequency, offset]):
    # raise MissingParameters("Need frequency and offset for function generator")
    # TODO Setup Timeout
    p = LinearScalarControl(cur_amplitude)
    p.set_point(set_point)
    settle_cnt = 0
    new_kwargs = {"frequency": frequency, "offset": offset}

    for _ in _range_gen(retries):
        test_val = dmm.measure()
        try:
            test_val = test_val[0]
        except TypeError:
            pass
        if test_val > 1e10:
            raise InstrumentError("Measurement outside the specified dmm range")
        # Test in range
        if settle_min is not None and settle_max is not None:
            if settle_min <= test_val <= settle_max:
                settle_cnt += 1
            else:
                settle_cnt = 0
            if settle_cnt >= settle_number:
                return True
        # Get the control value from controller
        contr_val = p.update(test_val)
        # Put the control value into the kwargs for the control function
        if limit_amplitude and contr_val >= limit_amplitude:
            raise InstrumentError(
                "Converge function value {}Vpp exceeded the limit set {}Vpp".format(
                    contr_val, limit_amplitude
                )
            )
        new_kwargs.update(dict([("amplitude", contr_val)]))
        funcgen_or_ps.function(mode, **new_kwargs)
        if not (contr_val * 0.95 < funcgen_or_ps.amplitude_ch1 <= contr_val * 1.05):
            raise InstrumentError(
                "Amplitude {} set outside of instrument range {}".format(
                    contr_val, funcgen_or_ps.amplitude_ch1
                )
            )
            # Check if programmable power supply
            # raise NotImplementedError("Programmable Power Supply Not implemented for this control")
            # if issubclass(ProgPS, funcgen_or_ps):
            # pass


def converge_scalar(
    control_func,
    feedback_func,
    set_point,
    initial_state,
    settle_min,
    settle_max,
    limit_control=(None, None),
    timeout=10,
    settle_number=1,
):
    """
    Uses a linear scalar controller to converge two functions.
    Best used in a linear system and with an informed starting point.
    Usage example;
    >>>dm.funcgen.channel1.waveform.sin()
    >>>dm.funcgen.channel1.frequency(1000)
    >>>dm.funcgen.channel1.vrms(0.1)
    >>>dm.dmm.voltage_ac()
    >>>dm.funcgen.channel1(True)
    >>>converged = converge_scalar(control_func = dm.funcgen.channel1.vrms,
    >>>                            feedback_func = dm.dmm.measurement,
    >>>                            set_point = 5.0,
    >>>                            initial_state = 0.1,
    >>>                            settle_min = 4.95,
    >>>                            settle_max = 5.05,
    >>>                            settle_number = 1)
    This will converge the function generator (sin 1kHz) so that the multimeter reading will read
    between 4.95 and 5.05 at least 3 times before returning.

    :param control_func: function
    the function that needs to be called to control
    eg. funcgen.channel1.vpp
    Must accept a single parameter which is the control value.
    ie. control_func(value)
    :param feedback_func: function
    The function that reads the value to compare to the set point
    Must work without accepting any parameters
    eg. dmm.measurement
    :param set_point: [float, int]
    The desired endpoint for the function. Must be a number
    eg. 5.0
    :param initial_state: [float, int]
    The value that has already been parsed into the control function before entering the function. This acts as an
    initial state of the controlled input for the output controller.
    :param timeout: [float, int]
    Maximum time allowed in seconds for the control to complete its task. Will wait until calling functions are completed
    before timing out. ie. This will not account for timeouts on the control function and feedback function.
    :param settle_min: [float, int]
    The minimum value that is considered to be at an acceptable settle point
    :param settle_max: [float, int]
    The maximum value that is considered to be at an acceptable settle point
    :param settle_number: [float, int]
    The number of consecutive measurements in a that are within settle_min <= value <= settle_max
    before the function returns True
    :param limit_control: (minimum: [float, int], maximum: [float, int])
    Limits that the control is allowed to reach before aborting. None for each parameter places no limits.
    Values smaller than minimum and numbers greater than maximum are aborted.
    :return:
    True if converged
    False if not completed before timeout
    Parameter error if parsed parameters are incompatible
    Calling functions exceptions are not handled
    """
    contr_val = initial_state
    p = LinearScalarControl(contr_val)
    p.set_point(set_point)
    settle_cnt = 0
    time_start = time.time()
    minimum, maximum = limit_control
    while True:
        test_val = feedback_func()
        # Test in range
        if settle_min <= test_val <= settle_max:
            settle_cnt += 1
        else:
            settle_cnt = 0
        if settle_cnt >= settle_number:
            return True
        if time.time() - time_start > timeout:
            return False
        # Get the control value from controller
        contr_val = p.update(test_val)
        # Bounds checks
        if minimum is not None and contr_val < minimum:
            return False
        if maximum is not None and contr_val > maximum:
            return False
        control_func(contr_val)


class LinearScalarControl:
    """
    Approximates based on the ratio of the updated value to the desired set point
    initial_state needs to be a number that is non-zero as the returned result is a multiplication of the
    initial_state and previous updated_value.
    Assumes zero settling time as it should be settled by the time it is measured
    """

    def __init__(self, initial_state):
        self._set_point = 0.0
        try:
            self._updated_value = float(initial_state)
        except ValueError as e:
            raise ParameterError(
                "initial_state found {}. Must be a non-zero number".format(
                    initial_state
                )
            ) from e

    def update(self, measured_value):
        if self._updated_value == 0.0:
            raise ParameterError(
                "Cannot apply a scalar value to 0.0 because it will always return 0.0"
            )
        self._updated_value *= self._set_point / measured_value
        return self._updated_value

    def set_point(self, value):
        self._set_point = value


class LinearAbsoluteControl:
    """
    Approximates based on multiple readings of the error to gauge the affect of the variable has on the error value.
    Best used for calculating required offset values on dc measurements.
    Assumes zero settling time as it should be settled by the time it is measured
    x = LinearAbsoluteControl(5.0)
    """

    def __init__(self, initial_state):
        self._set_point = 0.0
        try:
            self._updated_value = float(initial_state)
        except ValueError as e:
            raise ParameterError(
                "initial_state found {}. Must be a number".format(initial_state)
            ) from e
        self._error_scalar = None
        self._error = None
        self._damp_factor = 0.8

    def update(self, measured_value):
        """
            If it is first time run than assume that the error scalar should be 1
            If it is past the first time then the error scalar needs to be updated based on the measured results
        """
        if self._error_scalar:
            self._error_scalar *= (
                self._error - (self._set_point - measured_value)
            ) * self._damp_factor
        else:
            self._error_scalar = 1
        self._error = self._set_point - measured_value
        print(
            "Update params error {} error scalar {}".format(
                self._error, self._error_scalar
            )
        )
        self._updated_value += self._error * self._error_scalar

        return self._updated_value

    def set_point(self, value):
        self._set_point = value


class PID:
    """
    Discrete PID control
    The recipe gives simple implementation of a Discrete Proportional-Integral-Derivative (PID) controller.
    PID controller gives output value for error between desired reference input and measurement feedback to
    minimize error value.
    More information: http://en.wikipedia.org/wiki/PID_controller

     cnr437@gmail.com

     ######	Usage #########

    p=PID(3.0,0.4,1.2)
    p.setPoint(5.0)
    while True:
         pid = p.update(measurement_value)


    """

    def __init__(
        self,
        P=2.0,
        I=0.0,
        D=1.0,
        Derivator=0,
        Integrator=0,
        Integrator_max=500,
        Integrator_min=-500,
    ):

        self.Kp = P
        self.Ki = I
        self.Kd = D
        self.Derivator = Derivator
        self.Integrator = Integrator
        self.Integrator_max = Integrator_max
        self.Integrator_min = Integrator_min

        self.set_point = 0.0
        self.error = 0.0

    def update(self, current_value):
        """
        Calculate PID output value for given reference input and feedback
        """

        self.error = self.set_point - current_value

        self.P_value = self.Kp * self.error
        self.D_value = self.Kd * (self.Derivator - current_value)
        self.Derivator = current_value

        self.Integrator += self.error

        if self.Integrator > self.Integrator_max:
            self.Integrator = self.Integrator_max
        elif self.Integrator < self.Integrator_min:
            self.Integrator = self.Integrator_min

        self.I_value = self.Integrator * self.Ki

        PID = self.P_value + self.I_value + self.D_value
        if PID > 1:
            PID = 1
        if PID < 0:
            PID = 0

        return PID

    def setPoint(self, set_point):
        """
        Initilize the setpoint of PID
        """
        self.set_point = set_point
        self.Integrator = 0
        self.Derivator = 0

    def setIntegrator(self, Integrator):
        self.Integrator = Integrator

    def setDerivator(self, Derivator):
        self.Derivator = Derivator

    def setKp(self, P):
        self.Kp = P

    def setKi(self, I):
        self.Ki = I

    def setKd(self, D):
        self.Kd = D

    def getPoint(self):
        return self.set_point

    def getError(self):
        return self.error

    def getIntegrator(self):
        return self.Integrator

    def getDerivator(self):
        return self.Derivator
