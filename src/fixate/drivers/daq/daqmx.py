r"""
NI IO Trace can be used to troubleshoot & debug the setup. It should be installed
when the NI-DAQmx driver is installed.

PyDAQmx parses the NIDAQmx.h header to build ctypes wrappers for all function,
constants, etc. It also wraps the functions which return errors codes to raise
exceptions (and warnings) based on the return value.

https://www.ni.com/en-au/support/downloads/drivers/download.ni-daqmx.html#409845

API Reference manual:
https://zone.ni.com/reference/en-XX/help/370471AM-01/

C:\Program Files (x86)\National Instruments\NI-DAQ\DAQmx ANSI C Dev\include\NIDAQmx.h
C:\Program Files\National Instruments\NI-DAQ\DAQmx ANSI C Dev\include\NIDAQmx.h

"""
from collections import namedtuple
from fixate.core.common import ExcThread
from queue import Queue, Empty

from ctypes import byref, c_char_p
import numpy


# Basic Functions
from PyDAQmx import (
    DAQmxResetDevice,
    TaskHandle,
    int32,
    uInt8,
    float64,
    uInt64,
    uInt32,
)

# Tasks
from PyDAQmx import (
    DAQmxCreateTask,
    DAQmxStartTask,
    DAQmxWaitUntilTaskDone,
    DAQmxStopTask,
    DAQmxClearTask,
)

# Channels
from PyDAQmx import (
    DAQmxCreateDOChan,
    DAQmxCreateDIChan,
    DAQmxReadDigitalLines,
    DAQmxWriteDigitalLines,
    DAQmx_Val_GroupByScanNumber,
    DAQmx_Val_ChanPerLine,
    DAQmxReadCounterScalarF64,
    DAQmx_Val_Rising,
    DAQmx_Val_Seconds,
    DAQmxCfgSampClkTiming,
    DAQmx_Val_FiniteSamps,
)

# Two Edge Separation
from PyDAQmx import (
    DAQmxCreateCITwoEdgeSepChan,
    DAQmxSetCITwoEdgeSepFirstTerm,
    DAQmxGetCITwoEdgeSepFirstTerm,
    DAQmxSetCITwoEdgeSepSecondTerm,
    DAQmxGetCITwoEdgeSepSecondTerm,
    DAQmx_Val_Falling,
)

# Signal Routing
from PyDAQmx import (
    DAQmxConnectTerms,
    DAQmxDisconnectTerms,
    DAQmxTristateOutputTerm,
    DAQmx_Val_InvertPolarity,
    DAQmx_Val_DoNotInvertPolarity,
)

from fixate.core.exceptions import InstrumentError, ParameterError

IORange = namedtuple("IORange", ["port", "range_start", "range_end"])
IORange.__new__.__defaults__ = (0, None, None)

IOLine = namedtuple("IOLine", ["port", "line"])
IOLine.__new__.__defaults__ = (0, None)


class DaqTask:
    """ """

    task_state = ""
    task = None

    def read(self):
        raise NotImplementedError("Read not available for this Task")

    def write(self, data):
        raise NotImplementedError("Write not available for this Task")

    def trigger(self):
        raise NotImplementedError("Trigger not available for this Task")

    def init(self):
        """
        This method should be overridden to create the task
        :return:
        """

    def stop(self):
        if self.task_state == "running":
            DAQmxStopTask(self.task)
            self.task_state = "stopped"

    def clear(self):
        self.stop()
        if self.task_state != "":
            DAQmxClearTask(self.task)
            self.task = None
            self.task_state = ""

    def start(self):
        if self.task_state == "running":
            return
        if self.task_state == "":
            self.init()
        DAQmxStartTask(self.task)
        self.task_state = "running"


class DigitalOut(DaqTask):
    """ """

    def __init__(self, task_string, io_length):
        self.io_length = io_length
        self.task_string = task_string

    def init(self):
        if self.task_state == "":
            self.task = TaskHandle()
            DAQmxCreateTask(b"", byref(self.task))
            DAQmxCreateDOChan(self.task, self.task_string, b"", DAQmx_Val_ChanPerLine)
            self.task_state = "init"
        if self.task_state in ["init", "stopped"]:
            self.start()

    def read(self):
        self.init()
        data_arr = numpy.zeros(self.io_length, uInt8)
        samples_per_chan = int32()
        num_bytes_per_sample = int32()
        DAQmxReadDigitalLines(
            self.task,
            1,  # Samples per channel
            2.0,  # Timeout
            DAQmx_Val_GroupByScanNumber,  # Interleaved
            data_arr,
            len(data_arr),
            byref(samples_per_chan),
            byref(num_bytes_per_sample),
            None,
        )
        return data_arr

    def write(self, data):
        """
        Data must be an iterable like a list of 1s and 0s
        Data is grouped by scan number. Each element in the array will write to each line in the digital output until
        exhausted and then will start from the beginning for the next sample. Sample rate is as set in creating the IO
        task.
        """
        self.init()
        try:
            if len(data) % self.io_length:
                raise ValueError(
                    "data must be a length divisible by {}".format(self.io_length)
                )
            data_arr = numpy.zeros(len(data), uInt8)
            data_arr[:] = data
        except TypeError:
            if self.io_length != 1:
                raise ValueError(
                    "data must be a list of length divisible by {}".format(
                        self.io_length
                    )
                )
            data_arr = numpy.zeros(1, uInt8)
            data_arr[:] = [data]

        written = int32()
        DAQmxWriteDigitalLines(
            self.task,
            len(data_arr) // self.io_length,  # Samples per channel
            1,  # Autostart task
            2.0,  # Timeout
            DAQmx_Val_GroupByScanNumber,  # Interleaved
            data_arr,
            written,
            None,
        )


class DigitalIn(DaqTask):
    """ """

    def __init__(self, task_string, io_length):
        self.io_length = io_length
        self.task_string = task_string

    def init(self):
        if self.task_state == "":
            self.task = TaskHandle()
            DAQmxCreateTask(b"", byref(self.task))
            DAQmxCreateDIChan(self.task, self.task_string, b"", DAQmx_Val_ChanPerLine)
            self.task_state = "init"
        if self.task_state in ["init", "stopped"]:
            self.start()

    def read(self):
        self.init()
        data_arr = numpy.zeros(self.io_length, uInt8)
        samples_per_chan = int32()
        num_bytes_per_sample = int32()
        DAQmxReadDigitalLines(
            self.task,
            1,  # Samples per channel
            2.0,  # Timeout
            DAQmx_Val_GroupByScanNumber,  # Interleaved
            data_arr,
            len(data_arr),
            byref(samples_per_chan),
            byref(num_bytes_per_sample),
            None,
        )
        return data_arr


class BufferedWrite(DaqTask):
    """ """

    def __init__(self, task_string, io_length, frequency):
        self.task_string = task_string
        self.io_length = io_length
        self.frequency = frequency

    def init(self):
        if self.task_state == "":
            self.task = TaskHandle()
            DAQmxCreateTask(b"", byref(self.task))
            DAQmxCreateDOChan(self.task, self.task_string, b"", DAQmx_Val_ChanPerLine)
            self.task_state = "init"

    def write(self, data):
        """
        The task should be in stopped state when calling write, it automatically starts the task through the
        DAQmxWriteDigitalLines call. When write is finished it is back in a stopped state
        :param data:
        :return:
        """
        self.init()
        try:
            if len(data) % self.io_length:
                raise ValueError(
                    "data must be a length divisible by {}".format(self.io_length)
                )
        except TypeError as e:
            raise ValueError(
                "data must be in an list divisible by {}".format(self.io_length)
            ) from e
        if len(data) == self.io_length:
            # Sample clock only works for more than one sample so duplicate the sample
            data = list(data)
            data.extend(data)

        DAQmxCfgSampClkTiming(
            self.task,
            None,
            float64(self.frequency),
            DAQmx_Val_Rising,
            DAQmx_Val_FiniteSamps,
            uInt64(int(len(data) // self.io_length)),
        )

        try:
            data_arr = numpy.zeros((len(data)), uInt8)
            data_arr[:] = data

            written = int32()
            DAQmxWriteDigitalLines(
                self.task,
                int(len(data) // self.io_length),
                1,
                -1,
                DAQmx_Val_GroupByScanNumber,
                data_arr,
                written,
                None,
            )
            self.task_state = "running"
            DAQmxWaitUntilTaskDone(self.task, -1)
            if written.value != len(data) // self.io_length:
                raise InstrumentError("Values not written correctly")
        finally:
            self.stop()


class TwoEdgeSeparation(DaqTask):
    _data = float64()
    _trigger_thread = None

    def __init__(
        self,
        device_name,
        counter_chan,
        min_val,
        max_val,
        first_edge_type,
        second_edge_type,
        source_terminal,
        destination_terminal,
    ):
        self.device_name = device_name
        self.counter_chan = counter_chan
        self.min_val = min_val
        self.max_val = max_val
        self.first_edge_type = first_edge_type
        self.second_edge_type = second_edge_type
        self.source_terminal = source_terminal
        self.destination_terminal = destination_terminal
        self._error_queue = Queue()
        self._thread_timeout = 10

    def init(self):
        if self.task_state == "":
            self.task = TaskHandle()
            DAQmxCreateTask(b"", byref(self.task))
            DAQmxCreateCITwoEdgeSepChan(
                self.task,
                "{}/{}".format(self.device_name, self.counter_chan).encode(),
                b"",
                float64(self.min_val),
                float64(self.max_val),
                DAQmx_Val_Seconds,
                self.first_edge_type,
                self.second_edge_type,
                b"",
            )
            if self.source_terminal:
                DAQmxSetCITwoEdgeSepFirstTerm(
                    self.task,
                    "{}/{}".format(self.device_name, self.counter_chan).encode(),
                    self.source_terminal.encode(),
                )

            if self.destination_terminal:
                DAQmxSetCITwoEdgeSepSecondTerm(
                    self.task,
                    "{}/{}".format(self.device_name, self.counter_chan).encode(),
                    self.destination_terminal.encode(),
                )
            self.task_state = "init"

    def read(self):
        self._trigger_thread.join(self._thread_timeout)
        if self._trigger_thread.is_alive():
            raise InstrumentError("Trigger thread failed to terminate")
        try:
            err = self._error_queue.get_nowait()
        except Empty:
            # no error in queue
            pass
        else:
            raise err
        # TODO: consider making this return self._data.value. We should return a python
        # float object, not a ctypes.c_double
        return self._data

    def _read(self):
        try:
            DAQmxReadCounterScalarF64(
                self.task, float64(self._thread_timeout), byref(self._data), None
            )
        except Exception as e:
            self._error_queue.put(ThreadError(e))
        return

    def trigger(self):
        if self._trigger_thread:
            self.clear()
            self._trigger_thread.join(self._thread_timeout)
            if self._trigger_thread.is_alive():
                raise InstrumentError("Existing Trigger Event in Progress")
        self.init()
        self._trigger_thread = ExcThread(target=self._read)
        self._trigger_thread.start()


class ThreadError(Exception):
    """
    give a name to an error that came from a thread
    """

    pass


class DaqMx:
    """
    Implements the digital input and output functions of the National Instruments DAQ
    usage:
    daq = DaqMx()

    # Create a digital output from port 0 line 2 to line 4 named 'P0.2:4'
    daq.create_digital_output('P0.2:4', port=0, range_start=2, length=3)

    # Create a digital output with default port 0, at line 7 named 'reset'
    daq.create_digital_output('reset', 7)

    # Create a digital input at port 0 line 1
    daq.create_digital_input('P0.1', range_start=1)

    # This example assumes that port 0 line 1 is shorted to port 0 line 7 named reset

    daq.start()
    print("Port 7:", daq["reset"], "Echo Port:", daq["P0.1"])
    >>>'Port 7: [0] Echo Port: [0]'
    daq["P0.7"] = 1 # or True or '1' or [1]
    print("Port 7:", daq["reset"], "Echo Port:", daq["P0.1"])
    >>>'Port 7: [1] Echo Port: [1]'
    print(daq["P0.2:4"])
    >>>'[0 0 0]'
    daq["P0.2:4"] = [0, 1, 0] # Need to assign all values if initialised as multiple
    print(daq["P0.2:4"])
    >>>'[0 1 0]'
    daq.stop()
    """

    def __init__(self):
        self.device_name = "Dev1"
        self.tasks = {}
        self.reset()
        self.triggers = {}

    def reset(self):
        DAQmxResetDevice(self.device_name.encode())
        for _, task in self.tasks.items():
            task.task_state = ""

    def signal_route(
        self,
        source_terminal,
        destination_terminal,
        disconnect=False,
        tri_state=False,
        invert=False,
    ):
        """
        Immediately routes a signal between two terminals
        Set destination_terminal to '' if tri_state output is required on the source_terminal
        terminals are PFI X as they are the programmable terminals.
        See NI-MAX Device Routes for available terminal names.
        Leave out the device name
        eg. /Dev 1/PFI0 would be PFI0
        """
        source_terminal = "/{}/{}".format(self.device_name, source_terminal).encode()
        destination_terminal = "/{}/{}".format(
            self.device_name, destination_terminal
        ).encode()

        if disconnect:
            DAQmxDisconnectTerms(source_terminal, destination_terminal)
        elif tri_state:
            DAQmxTristateOutputTerm(source_terminal)
        else:
            if invert:
                invert = DAQmx_Val_InvertPolarity
            else:
                invert = DAQmx_Val_DoNotInvertPolarity
            DAQmxConnectTerms(source_terminal, destination_terminal, invert)

    def create_two_edge_separation(
        self,
        ident,
        counter_chan,
        min_val,
        max_val,
        first_edge_type,
        second_edge_type,
        source_terminal=None,
        destination_terminal=None,
    ):
        """
        Returns the two edge separation of two signals
        :param ident:
        Identification string used for reading the data via
        daq = DaqMx()
        daq.create_two_edge_separation(ident, **params)
        daq.trigger_measurement(ident)
        # Do stuff
        # Read the edge separation after causing the event
        edge_sep = daq[ident]
        :param counter_chan:
        For X-Series DAQs PCI
        'ctr0', 'ctr1', 'ctr2', 'ctr3' where the connected terminals are:
        Start = "AUX", Stop = "GATE"
        ctr0                ctr1                ctr2                 ctr3
        Start: PFI 10 Pin45 Start: PFI 11 Pin46 Start: PFI 2 Pin43   Start: PFI 7 Pin38
        Stop: PFI 9 Pin3    Stop: PFI 4 Pin41   Stop: PFI 1 Pin10     Stop: PFI 6 Pin5
        :param min_val:
        The minimum value, in units, that you expect to measure.
        eg. 0.0001
        :param max_val:
        The maximum value, in units, that you expect to measure.
        eg. 0.83
        :param first_edge_type:
        The start trigger on the first edge
        "rising" or "falling"
        :param second_edge_type:
        The stop trigger on the second edge
        "rising" or "falling"
        :param source_terminal
        :param destination_terminal
        Override the default counter terminals.
        eg.
        ctr0
        eg. source_terminal = "PFI14" will make the Start pin as PFI 14 in stead of 10
        """
        if counter_chan not in ["ctr0", "ctr1", "ctr2", "ctr3"]:
            raise ValueError("Invalid counter channel selected")
        if first_edge_type.lower() == "falling":
            first_edge_type = DAQmx_Val_Falling
        else:
            first_edge_type = DAQmx_Val_Rising
        if second_edge_type.lower() == "falling":
            second_edge_type = DAQmx_Val_Falling
        else:
            second_edge_type = DAQmx_Val_Rising

        self.tasks[ident] = TwoEdgeSeparation(
            self.device_name,
            counter_chan,
            min_val,
            max_val,
            first_edge_type,
            second_edge_type,
            source_terminal,
            destination_terminal,
        )

    def trigger_measurement(self, ident):
        try:
            self.tasks[ident].trigger()
        except KeyError as e:
            raise ValueError("{} is not a valid task".format(ident)) from e

    def create_buffered_write(self, ident, frequency, *dio_ranges):
        """
        Sets up the ranges to synchronize when writing to output at a specified frequency.
        This will force each write to the output for this ident to contain the amount of samples specified.
        eg.
        >>>daq = DaqMx()
        # Setup output @ 100Hz, 3 samples on port0 line 7 and 9
        >>>daq.create_buffered_write("MyOutput", 100, (0, 7, 7), (0, 9, 9))
        3 samples over 2 lines is 6 data values.
        >>>daq["MyOutput"] = [0 ,0, 1, 1, 0, 1]
        it is interleaved so it is written [line7, line9, line7, line9, line7, line9]
        Requires ports that enable buffered writes.
        In the X-Series daq this is port 0
        This disables reading from the output port for these pins.

        :param ident
        The identification used to access this message
        :param frequency
        The sample frequency for writing
        :type frequency integer or float
        :param io_ranges
        :type (port, line_start, line_end)
        :param samples
        The amount of samples that are required for each digital output write
        """
        if ident in self.tasks:
            raise ParameterError("Ident {} already used".format(ident))
        do_channel, data_length = self._build_digital_task_string(*dio_ranges)
        self.tasks[ident] = BufferedWrite(
            task_string=do_channel, io_length=data_length, frequency=frequency
        )

    def _build_digital_task_string(self, *dio_ranges):
        """
        :param dio_ranges:
        each dio_range is a tuple of ('port', 'range_start', 'range_end') or an IORange instance.
        :return:
        The string used to create the task by connecting each of the ports togeter
        """
        data_length = 0
        task_arr = []
        for rng in dio_ranges:
            task_arr.append(self.device_name + "/port{}/line{}:{}".format(*rng))
            data_length += rng[2] - rng[1] + 1  # range end - range start + 1
        return ", ".join(task_arr).encode(), data_length

    def create_digital_output(self, ident, *dio_ranges):
        """
        :param dio_ranges
        each dio_range is a tuple of ('port', 'range_start', 'range_end') or an IORange instance.
        A digital output is created in the order of the dio_ranges and can be accessed by the ident key.
        >>>daq = DaqMx()
        >>>rng_1 = IORange(0, 7, 9)  # Port 0 line 7 to line 9
        >>>rng_2 = IORange(0, 11,11) # Port 0 line 11
        >>>daq.create_digital_output("MyOut", rng_1, rng_2)
        >>>daq["MyOut"] = [0, 1, 0, 1]  # Port 0 Line 8 and 11 high
        >>>print(daq["MyOut"])  # Read back the value
        >>>[0, 1, 0, 1]
        """
        if ident in self.tasks:
            raise ParameterError("Ident {} already used".format(ident))
        task_string, data_length = self._build_digital_task_string(*dio_ranges)
        self.tasks[ident] = DigitalOut(task_string, io_length=data_length)

    def create_digital_input(self, ident, *dio_ranges):
        """
        :param dio_ranges
        each dio_range is a tuple of ('port', 'range_start', 'range_end') or an IORange instance.
        A digital output is created in the order of the dio_ranges and can be accessed by the ident key.
        >>>daq = DaqMx()
        >>>rng_1 = IORange(0, 7, 9)  # Port 0 line 7 to line 9
        >>>rng_2 = IORange(0, 11,11) # Port 0 line 11
        >>>daq.create_digital_input("MyOut", rng_1, rng_2)
        >>>print(daq["MyOut"])  # Tie Port 0 line 8 and line 11 high
        >>>[0, 1, 0, 1]
        """
        if ident in self.tasks:
            raise ParameterError("Ident {} already used".format(ident))
        task_string, data_length = self._build_digital_task_string(*dio_ranges)
        self.tasks[ident] = DigitalIn(task_string, io_length=data_length)

    def __getitem__(self, ident):
        return self.read(ident)

    def __setitem__(self, ident, data):
        self.write(ident, data)

    def write(self, ident, value):
        try:
            return self.tasks[ident].write(value)
        except KeyError:
            raise KeyError("{} is not a valid identifier".format(ident))

    def read(self, ident):
        try:
            return self.tasks[ident].read()
        except KeyError:
            raise KeyError(
                "{} is not a valid identifier\nAvailable tasks: {}".format(
                    ident, sorted(self.tasks)
                )
            )

    def start_task(self, ident):
        """

        :param ident:
        :return:
        """
        self.tasks[ident].start()

    def stop_task(self, ident):
        """
        Stops a task to be
        :param ident:
        :return:
        """
        self.tasks[ident].stop()

    def clear_task(self, ident):
        """
        Stops a task and clear up the resources allocated to the
        :param ident:
        :return:
        """
        self.tasks[ident].clear()
