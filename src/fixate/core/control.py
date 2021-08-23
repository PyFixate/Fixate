import time
from fixate.core.exceptions import ParameterError, InstrumentError


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
