import struct
import pyvisa
from fixate.core.exceptions import InstrumentError
from fixate.drivers.dso.helper import DSO
import time


# Example IDN Strings
# KEYSIGHT TECHNOLOGIES,DSOX1202G,CN60074190,02.10.2019111333
# KEYSIGHT TECHNOLOGIES,DSO-X 1102G,CN57096441,01.20.2019061038
# AGILENT TECHNOLOGIES,MSO-X 3014A,MY51360314,02.43.2018020635


class MSO_X_3000(DSO):
    REGEX_ID = "(KEYSIGHT|AGILENT) TECHNOLOGIES,[DM]SO-?X"
    INSTR_TYPE = "VISA"
    retrys_on_timeout = 1

    def __init__(self, instrument):
        super().__init__(instrument)
        self.display = "on"
        self.is_connected = True
        self._mode = "STOP"
        self._wave_acquired = False
        self._triggers_read = 0
        self.reset()
        self.instrument.query_delay = 0.2
        self._store = {}
        self.api = [
            ("source1.ch1", self.store, {"source1": "CHAN1"}),
            ("source1.ch2", self.store, {"source1": "CHAN2"}),
            ("source1.ch3", self.store, {"source1": "CHAN3"}),
            ("source1.ch4", self.store, {"source1": "CHAN4"}),
            ("source1.function", self.store, {"source1": "FUNC"}),
            ("source1.math", self.store, {"source1": "MATH"}),
            ("source1.wmemory1", self.store, {"source1": "WMEM1"}),
            ("source1.wmemory2", self.store, {"source1": "WMEM2"}),
            ("source2.ch1", self.store, {"source2": "CHAN1"}),
            ("source2.ch2", self.store, {"source2": "CHAN2"}),
            ("source2.ch3", self.store, {"source2": "CHAN3"}),
            ("source2.ch4", self.store, {"source2": "CHAN4"}),
            ("source2.function", self.store, {"source1": "FUNC"}),
            ("source2.math", self.store, {"source1": "MATH"}),
            ("source2.wmemory1", self.store, {"source1": "WMEM1"}),
            ("source2.wmemory2", self.store, {"source1": "WMEM2"}),
            ("ch1._call", self.write, "CHAN1:DISP {value:d}"),
            ("ch2._call", self.write, "CHAN2:DISP {value:d}"),
            ("ch3._call", self.write, "CHAN3:DISP {value:d}"),
            ("ch4._call", self.write, "CHAN4:DISP {value:d}"),
            ("ch1.scale", self.write, "CHAN1:SCAL {value}"),
            ("ch2.scale", self.write, "CHAN2:SCAL {value}"),
            ("ch3.scale", self.write, "CHAN3:SCAL {value}"),
            ("ch4.scale", self.write, "CHAN4:SCAL {value}"),
            ("ch1.offset", self.write, "CHAN1:OFFS {value}"),
            ("ch2.offset", self.write, "CHAN2:OFFS {value}"),
            ("ch3.offset", self.write, "CHAN3:OFFS {value}"),
            ("ch4.offset", self.write, "CHAN4:OFFS {value}"),
            ("ch1.coupling.ac", self.write, "CHAN1:COUP AC"),
            ("ch2.coupling.ac", self.write, "CHAN2:COUP AC"),
            ("ch3.coupling.ac", self.write, "CHAN3:COUP AC"),
            ("ch4.coupling.ac", self.write, "CHAN4:COUP AC"),
            ("ch1.coupling.dc", self.write, "CHAN1:COUP DC"),
            ("ch2.coupling.dc", self.write, "CHAN2:COUP DC"),
            ("ch3.coupling.dc", self.write, "CHAN3:COUP DC"),
            ("ch4.coupling.dc", self.write, "CHAN4:COUP DC"),
            ("ch1.probe.attenuation", self.write, "CHAN1:PROB {value}"),
            ("ch2.probe.attenuation", self.write, "CHAN2:PROB {value}"),
            ("ch3.probe.attenuation", self.write, "CHAN3:PROB {value}"),
            ("ch4.probe.attenuation", self.write, "CHAN4:PROB {value}"),
            ("time_base.scale", self.write, "TIM:SCAL {value}"),
            ("time_base.position", self.write, "TIM:POS {value}"),
            ("trigger.mode.edge._call", self.write, "TRIG:MODE EDGE"),
            ("trigger.mode.edge.level", self.write, "TRIG:EDGE:LEVEL {value}"),
            ("trigger.mode.edge.source.ch1", self.write, "TRIG:EDGE:SOUR CHAN1"),
            ("trigger.mode.edge.source.ch2", self.write, "TRIG:EDGE:SOUR CHAN2"),
            ("trigger.mode.edge.source.ch3", self.write, "TRIG:EDGE:SOUR CHAN3"),
            ("trigger.mode.edge.source.ch4", self.write, "TRIG:EDGE:SOUR CHAN4"),
            ("trigger.mode.edge.slope.rising", self.write, "TRIG:EDGE:SLOPE POS"),
            ("trigger.mode.edge.slope.falling", self.write, "TRIG:EDGE:SLOPE NEG"),
            ("trigger.mode.edge.slope.either", self.write, "TRIG:EDGE:SLOPE EITH"),
            ("trigger.mode.edge.slope.alternating", self.write, "TRIG:EDGE:SLOPE ALT"),
            ("trigger.sweep.normal", self.write, "TRIG:SWE NORM"),
            ("trigger.sweep.auto", self.write, "TRIG:SWE AUTO"),
            ("trigger.coupling.ac", self.write, "TRIG:COUP AC"),
            ("trigger.coupling.dc", self.write, "TRIG:COUP DC"),
            ("trigger.coupling.lf_reject", self.write, "TRIG:COUP LFR"),
            ("trigger.hf_reject", self.write, "TRIG:HFR {value}"),
            ("acquire.normal", self.write, "ACQ:TYPE NORM"),
            ("acquire.peak_detect", self.write, "ACQ:TYPE PEAK"),
            ("acquire.averaging", self.write, "ACQ:TYPE AVER;:ACQ:COUN {value}"),
            ("acquire.high_resolution", self.write, "ACQ:TYPE HRES"),
            ("events.trigger", self.query_bool, ":TER?"),
            # Measure
            (
                "measure.delay._call",
                self.query_after_acquire,
                "MEAS:DEL? {self._store[source1]},{self._store[source2]}",
            ),
            (
                "measure.define.threshold.percent",
                self.write,
                "MEAS:DEF THR,PERC,{upper},{middle},{lower}",
            ),
            (
                "measure.define.threshold.absolute",
                self.write,
                "MEAS:DEF THR,ABS,{upper},{middle},{lower}",
            ),
            ("measure.delay.edges.rising.rising", self.write, "MEAS:DEF DEL, +1, +1"),
            ("measure.delay.edges.rising.falling", self.write, "MEAS:DEF DEL, +1, -1"),
            ("measure.delay.edges.falling.rising", self.write, "MEAS:DEF DEL, -1, +1"),
            ("measure.delay.edges.falling.falling", self.write, "MEAS:DEF DEL, -1, -1"),
            (
                "measure.phase",
                self.query_after_acquire,
                "MEAS:PHAS? {self._store[source1]},{self._store[source2]}",
            ),
            (
                "measure.vratio.cycle",
                self.query_after_acquire,
                "MEAS:VRAT? CYCL,{self._store[source1]},{self._store[source2]}",
            ),
            (
                "measure.vratio.display",
                self.query_after_acquire,
                "MEAS:VRAT? DISP,{self._store[source1]},{self._store[source2]}",
            ),
            # Ch1 Measure
            ("measure.counter.ch1", self.query_after_acquire, "MEAS:COUN? CHAN1"),
            ("measure.duty.ch1", self.query_after_acquire, "MEAS:DUTY? CHAN1"),
            ("measure.fall_time.ch1", self.query_after_acquire, "MEAS:FALL? CHAN1"),
            ("measure.rise_time.ch1", self.query_after_acquire, "MEAS:RIS? CHAN1"),
            ("measure.frequency.ch1", self.query_after_acquire, "MEAS:FREQ? CHAN1"),
            (
                "measure.cnt_edge_rising.ch1",
                self.query_after_acquire,
                "MEAS:NEDG? CHAN1",
            ),
            (
                "measure.cnt_edge_falling.ch1",
                self.query_after_acquire,
                "MEAS:PEDG? CHAN1",
            ),
            (
                "measure.cnt_pulse_positive.ch1",
                self.query_after_acquire,
                "MEAS:NPUL? CHAN1",
            ),
            (
                "measure.cnt_pulse_negative.ch1",
                self.query_after_acquire,
                "MEAS:PPUL? CHAN1",
            ),
            ("measure.period.ch1", self.query_after_acquire, "MEAS:PER? CHAN1"),
            ("measure.pulse_width.ch1", self.query_after_acquire, "MEAS:PWID? CHAN1"),
            ("measure.vamplitude.ch1", self.query_after_acquire, "MEAS:VAMP? CHAN1"),
            (
                "measure.vaverage.cycle.ch1",
                self.query_after_acquire,
                "MEAS:VAV? CYCL,CHAN1",
            ),
            (
                "measure.vaverage.display.ch1",
                self.query_after_acquire,
                "MEAS:VAV? DISP,CHAN1",
            ),
            ("measure.vbase.ch1", self.query_after_acquire, "MEAS:VBAS? CHAN1"),
            ("measure.vtop.ch1", self.query_after_acquire, "MEAS:VTOP? CHAN1"),
            ("measure.vmax.ch1", self.query_after_acquire, "MEAS:VMAX? CHAN1"),
            ("measure.vmin.ch1", self.query_after_acquire, "MEAS:VMIN? CHAN1"),
            ("measure.vpp.ch1", self.query_after_acquire, "MEAS:VPP? CHAN1"),
            (
                "measure.vrms.dc.cycle.ch1",
                self.query_after_acquire,
                "MEAS:VRMS? CYCL,DC,CHAN1",
            ),
            (
                "measure.vrms.dc.display.ch1",
                self.query_after_acquire,
                "MEAS:VRMS? DISP,DC,CHAN1",
            ),
            (
                "measure.vrms.ac.cycle.ch1",
                self.query_after_acquire,
                "MEAS:VRMS? CYCL,AC,CHAN1",
            ),
            (
                "measure.vrms.ac.display.ch1",
                self.query_after_acquire,
                "MEAS:VRMS? DISP,AC,CHAN1",
            ),
            ("measure.xmax.ch1", self.query_after_acquire, "MEAS:XMAX? CHAN1"),
            ("measure.xmin.ch1", self.query_after_acquire, "MEAS:XMIN? CHAN1"),
            # Ch2 Measure
            ("measure.counter.ch2", self.query_after_acquire, "MEAS:COUN? CHAN2"),
            ("measure.duty.ch2", self.query_after_acquire, "MEAS:DUTY? CHAN2"),
            ("measure.rise_time.ch2", self.query_after_acquire, "MEAS:RIS? CHAN2"),
            ("measure.fall_time.ch2", self.query_after_acquire, "MEAS:FALL? CHAN2"),
            ("measure.frequency.ch2", self.query_after_acquire, "MEAS:FREQ? CHAN2"),
            (
                "measure.cnt_edge_rising.ch2",
                self.query_after_acquire,
                "MEAS:NEDG? CHAN2",
            ),
            (
                "measure.cnt_edge_falling.ch2",
                self.query_after_acquire,
                "MEAS:PEDG? CHAN2",
            ),
            (
                "measure.cnt_pulse_positive.ch2",
                self.query_after_acquire,
                "MEAS:NPUL? CHAN2",
            ),
            (
                "measure.cnt_pulse_negative.ch2",
                self.query_after_acquire,
                "MEAS:PPUL? CHAN2",
            ),
            ("measure.period.ch2", self.query_after_acquire, "MEAS:PER? CHAN2"),
            ("measure.pulse_width.ch2", self.query_after_acquire, "MEAS:PWID? CHAN2"),
            ("measure.vamplitude.ch2", self.query_after_acquire, "MEAS:VAMP? CHAN2"),
            (
                "measure.vaverage.cycle.ch2",
                self.query_after_acquire,
                "MEAS:VAV? CYCL,CHAN2",
            ),
            (
                "measure.vaverage.display.ch2",
                self.query_after_acquire,
                "MEAS:VAV? DISP,CHAN2",
            ),
            ("measure.vbase.ch2", self.query_after_acquire, "MEAS:VBAS? CHAN2"),
            ("measure.vtop.ch2", self.query_after_acquire, "MEAS:VTOP? CHAN2"),
            ("measure.vmax.ch2", self.query_after_acquire, "MEAS:VMAX? CHAN2"),
            ("measure.vmin.ch2", self.query_after_acquire, "MEAS:VMIN? CHAN2"),
            ("measure.vpp.ch2", self.query_after_acquire, "MEAS:VPP? CHAN2"),
            (
                "measure.vrms.dc.cycle.ch2",
                self.query_after_acquire,
                "MEAS:VRMS? CYCL,DC,CHAN2",
            ),
            (
                "measure.vrms.dc.display.ch2",
                self.query_after_acquire,
                "MEAS:VRMS? DISP,DC,CHAN2",
            ),
            (
                "measure.vrms.ac.cycle.ch2",
                self.query_after_acquire,
                "MEAS:VRMS? CYCL,AC,CHAN2",
            ),
            (
                "measure.vrms.ac.display.ch2",
                self.query_after_acquire,
                "MEAS:VRMS? DISP,AC,CHAN2",
            ),
            ("measure.xmax.ch2", self.query_after_acquire, "MEAS:XMAX? CHAN2"),
            ("measure.xmin.ch2", self.query_after_acquire, "MEAS:XMIN? CHAN2"),
            # Ch3 Measure
            ("measure.counter.ch3", self.query_after_acquire, "MEAS:COUN? CHAN3"),
            ("measure.duty.ch3", self.query_after_acquire, "MEAS:DUTY? CHAN3"),
            ("measure.fall_time.ch3", self.query_after_acquire, "MEAS:FALL? CHAN3"),
            ("measure.rise_time.ch3", self.query_after_acquire, "MEAS:RIS? CHAN3"),
            ("measure.frequency.ch3", self.query_after_acquire, "MEAS:FREQ? CHAN3"),
            (
                "measure.cnt_edge_rising.ch3",
                self.query_after_acquire,
                "MEAS:NEDG? CHAN3",
            ),
            (
                "measure.cnt_edge_falling.ch3",
                self.query_after_acquire,
                "MEAS:PEDG? CHAN3",
            ),
            (
                "measure.cnt_pulse_positive.ch3",
                self.query_after_acquire,
                "MEAS:NPUL? CHAN3",
            ),
            (
                "measure.cnt_pulse_negative.ch3",
                self.query_after_acquire,
                "MEAS:PPUL? CHAN3",
            ),
            ("measure.period.ch3", self.query_after_acquire, "MEAS:PER? CHAN3"),
            ("measure.pulse_width.ch3", self.query_after_acquire, "MEAS:PWID? CHAN3"),
            ("measure.vamplitude.ch3", self.query_after_acquire, "MEAS:VAMP? CHAN3"),
            (
                "measure.vaverage.cycle.ch3",
                self.query_after_acquire,
                "MEAS:VAV? CYCL,CHAN3",
            ),
            (
                "measure.vaverage.display.ch3",
                self.query_after_acquire,
                "MEAS:VAV? DISP,CHAN3",
            ),
            ("measure.vbase.ch3", self.query_after_acquire, "MEAS:VBAS? CHAN3"),
            ("measure.vtop.ch3", self.query_after_acquire, "MEAS:VTOP? CHAN3"),
            ("measure.vmax.ch3", self.query_after_acquire, "MEAS:VMAX? CHAN3"),
            ("measure.vmin.ch3", self.query_after_acquire, "MEAS:VMIN? CHAN3"),
            ("measure.vpp.ch3", self.query_after_acquire, "MEAS:VPP? CHAN3"),
            (
                "measure.vrms.dc.cycle.ch3",
                self.query_after_acquire,
                "MEAS:VRMS? CYCL,DC,CHAN3",
            ),
            (
                "measure.vrms.dc.display.ch3",
                self.query_after_acquire,
                "MEAS:VRMS? DISP,DC,CHAN3",
            ),
            (
                "measure.vrms.ac.cycle.ch3",
                self.query_after_acquire,
                "MEAS:VRMS? CYCL,AC,CHAN3",
            ),
            (
                "measure.vrms.ac.display.ch3",
                self.query_after_acquire,
                "MEAS:VRMS? DISP,AC,CHAN3",
            ),
            ("measure.xmax.ch3", self.query_after_acquire, "MEAS:XMAX? CHAN3"),
            ("measure.xmin.ch3", self.query_after_acquire, "MEAS:XMIN? CHAN3"),
            # Ch4 Measure
            ("measure.counter.ch4", self.query_after_acquire, "MEAS:COUN? CHAN4"),
            ("measure.duty.ch4", self.query_after_acquire, "MEAS:DUTY? CHAN4"),
            ("measure.fall_time.ch4", self.query_after_acquire, "MEAS:FALL? CHAN4"),
            ("measure.rise_time.ch4", self.query_after_acquire, "MEAS:RIS? CHAN4"),
            ("measure.frequency.ch4", self.query_after_acquire, "MEAS:FREQ? CHAN4"),
            (
                "measure.cnt_edge_rising.ch4",
                self.query_after_acquire,
                "MEAS:NEDG? CHAN4",
            ),
            (
                "measure.cnt_edge_falling.ch4",
                self.query_after_acquire,
                "MEAS:PEDG? CHAN4",
            ),
            (
                "measure.cnt_pulse_positive.ch4",
                self.query_after_acquire,
                "MEAS:NPUL? CHAN4",
            ),
            (
                "measure.cnt_pulse_negative.ch4",
                self.query_after_acquire,
                "MEAS:PPUL? CHAN4",
            ),
            ("measure.period.ch4", self.query_after_acquire, "MEAS:PER? CHAN4"),
            ("measure.pulse_width.ch4", self.query_after_acquire, "MEAS:PWID? CHAN4"),
            ("measure.vamplitude.ch4", self.query_after_acquire, "MEAS:VAMP? CHAN4"),
            (
                "measure.vaverage.cycle.ch4",
                self.query_after_acquire,
                "MEAS:VAV? CYCL,CHAN4",
            ),
            (
                "measure.vaverage.display.ch4",
                self.query_after_acquire,
                "MEAS:VAV? DISP,CHAN4",
            ),
            ("measure.vbase.ch4", self.query_after_acquire, "MEAS:VBAS? CHAN4"),
            ("measure.vtop.ch4", self.query_after_acquire, "MEAS:VTOP? CHAN4"),
            ("measure.vmax.ch4", self.query_after_acquire, "MEAS:VMAX? CHAN4"),
            ("measure.vmin.ch4", self.query_after_acquire, "MEAS:VMIN? CHAN4"),
            ("measure.vpp.ch4", self.query_after_acquire, "MEAS:VPP? CHAN4"),
            (
                "measure.vrms.dc.cycle.ch4",
                self.query_after_acquire,
                "MEAS:VRMS? CYCL,DC,CHAN4",
            ),
            (
                "measure.vrms.dc.display.ch4",
                self.query_after_acquire,
                "MEAS:VRMS? DISP,DC,CHAN4",
            ),
            (
                "measure.vrms.ac.cycle.ch4",
                self.query_after_acquire,
                "MEAS:VRMS? CYCL,AC,CHAN4",
            ),
            (
                "measure.vrms.ac.display.ch4",
                self.query_after_acquire,
                "MEAS:VRMS? DISP,AC,CHAN4",
            ),
            ("measure.xmax.ch4", self.query_after_acquire, "MEAS:XMAX? CHAN4"),
            ("measure.xmin.ch4", self.query_after_acquire, "MEAS:XMIN? CHAN4"),
            # Function Measure
            ("measure.duty.function", self.query_after_acquire, "MEAS:DUTY? FUNC"),
            ("measure.fall_time.function", self.query_after_acquire, "MEAS:FALL? FUNC"),
            ("measure.rise_time.function", self.query_after_acquire, "MEAS:RIS? FUNC"),
            ("measure.frequency.function", self.query_after_acquire, "MEAS:FREQ? FUNC"),
            (
                "measure.cnt_edge_rising.function",
                self.query_after_acquire,
                "MEAS:NEDG? FUNC",
            ),
            (
                "measure.cnt_edge_falling.function",
                self.query_after_acquire,
                "MEAS:PEDG? FUNC",
            ),
            (
                "measure.cnt_pulse_positive.function",
                self.query_after_acquire,
                "MEAS:NPUL? FUNC",
            ),
            (
                "measure.cnt_pulse_negative.function",
                self.query_after_acquire,
                "MEAS:PPUL? FUNC",
            ),
            ("measure.period.function", self.query_after_acquire, "MEAS:PER? FUNC"),
            (
                "measure.pulse_width.function",
                self.query_after_acquire,
                "MEAS:PWID? FUNC",
            ),
            (
                "measure.vamplitude.function",
                self.query_after_acquire,
                "MEAS:VAMP? FUNC",
            ),
            (
                "measure.vaverage.cycle.function",
                self.query_after_acquire,
                "MEAS:VAV? CYCL,FUNC",
            ),
            (
                "measure.vaverage.display.function",
                self.query_after_acquire,
                "MEAS:VAV? DISP,FUNC",
            ),
            ("measure.vbase.function", self.query_after_acquire, "MEAS:VBAS? FUNC"),
            ("measure.vtop.function", self.query_after_acquire, "MEAS:VTOP? FUNC"),
            ("measure.vmax.function", self.query_after_acquire, "MEAS:VMAX? FUNC"),
            ("measure.vmin.function", self.query_after_acquire, "MEAS:VMIN? FUNC"),
            ("measure.vpp.function", self.query_after_acquire, "MEAS:VPP? FUNC"),
            (
                "measure.vrms.dc.cycle.function",
                self.query_after_acquire,
                "MEAS:VRMS? CYCL,DC,FUNC",
            ),
            (
                "measure.vrms.dc.display.function",
                self.query_after_acquire,
                "MEAS:VRMS? DISP,DC,FUNC",
            ),
            (
                "measure.vrms.ac.cycle.function",
                self.query_after_acquire,
                "MEAS:VRMS? CYCL,AC,FUNC",
            ),
            (
                "measure.vrms.ac.display.function",
                self.query_after_acquire,
                "MEAS:VRMS? DISP,AC,FUNC",
            ),
            ("measure.xmax.function", self.query_after_acquire, "MEAS:XMAX? FUNC"),
            ("measure.xmin.function", self.query_after_acquire, "MEAS:XMIN? FUNC"),
            # MATH,Measure
            ("measure.duty.math", self.query_after_acquire, "MEAS:DUTY? MATH"),
            ("measure.fall_time.math", self.query_after_acquire, "MEAS:FALL? MATH"),
            ("measure.rise_time.math", self.query_after_acquire, "MEAS:RIS? MATH"),
            ("measure.frequency.math", self.query_after_acquire, "MEAS:FREQ? MATH"),
            (
                "measure.cnt_edge_rising.math",
                self.query_after_acquire,
                "MEAS:NEDG? MATH",
            ),
            (
                "measure.cnt_edge_falling.math",
                self.query_after_acquire,
                "MEAS:PEDG? MATH",
            ),
            (
                "measure.cnt_pulse_positive.math",
                self.query_after_acquire,
                "MEAS:NPUL? MATH",
            ),
            (
                "measure.cnt_pulse_negative.math",
                self.query_after_acquire,
                "MEAS:PPUL? MATH",
            ),
            ("measure.period.math", self.query_after_acquire, "MEAS:PER? MATH"),
            ("measure.pulse_width.math", self.query_after_acquire, "MEAS:PWID? MATH"),
            ("measure.vamplitude.math", self.query_after_acquire, "MEAS:VAMP? MATH"),
            (
                "measure.vaverage.cycle.math",
                self.query_after_acquire,
                "MEAS:VAV? CYCL,MATH",
            ),
            (
                "measure.vaverage.display.math",
                self.query_after_acquire,
                "MEAS:VAV? DISP,MATH",
            ),
            ("measure.vbase.math", self.query_after_acquire, "MEAS:VBAS? MATH"),
            ("measure.vtop.math", self.query_after_acquire, "MEAS:VTOP? MATH"),
            ("measure.vmax.math", self.query_after_acquire, "MEAS:VMAX? MATH"),
            ("measure.vmin.math", self.query_after_acquire, "MEAS:VMIN? MATH"),
            ("measure.vpp.math", self.query_after_acquire, "MEAS:VPP? MATH"),
            (
                "measure.vrms.dc.cycle.math",
                self.query_after_acquire,
                "MEAS:VRMS? CYCL,DC,MATH",
            ),
            (
                "measure.vrms.dc.display.math",
                self.query_after_acquire,
                "MEAS:VRMS? DISP,DC,MATH",
            ),
            (
                "measure.vrms.ac.cycle.math",
                self.query_after_acquire,
                "MEAS:VRMS? CYCL,AC,MATH",
            ),
            (
                "measure.vrms.ac.display.math",
                self.query_after_acquire,
                "MEAS:VRMS? DISP,AC,MATH",
            ),
            ("measure.xmax.math", self.query_after_acquire, "MEAS:XMAX? MATH"),
            ("measure.xmin.math", self.query_after_acquire, "MEAS:XMIN? MATH"),
        ]
        self.init_api()
        self.instrument.timeout = 1000

    def single(self):
        """
        Sets up the oscilliscope for a single shot triggered measurement
        Does multiple steps to ensure that at the end of this call that the oscilloscope is primed for a trigger
        1. Sets mode to stop to ensure that only one measurement will occur
        2. Clears the status registers
        3. Sets the mode to single
        4. Monitors the registers until the trigger is armed
        :return:
        """
        self._triggers_read = 0
        self._raise_if_error()  # Raises if any errors were made during setup
        # Stop
        # Clear status registers (CLS)
        # enable the trigger mask in the event register (SRE)
        # operation complete (OPC)
        self.instrument.query(":STOP;*CLS;*SRE 1;*OPC?")
        self._store["time_base_wait"] = (
            self.instrument.query_ascii_values(":TIM:RANG?")[0]
            + self.instrument.query_ascii_values(":TIM:POS?")[0]
        )
        # Enables the Event service request register (SRE)
        # Currently we're not using events. wait_on_trigger is polling. The current implementation
        # doesn't work when using a LAN connection to the instrument, so we will comment out for now
        # self.instrument.enable_event(visa.constants.EventType.service_request, visa.constants.VI_QUEUE)
        self.instrument.write(":SINGLE")
        while True:
            if self.instrument.query_ascii_values(":AER?")[0]:
                break
            time.sleep(0.1)

        self._mode = "SINGLE"
        self._wave_acquired = False

    def run(self):
        self._triggers_read = 0
        self.query(":STOP;*CLS;*SRE 1;*OPC?")
        # Currently we're not using events. wait_on_trigger is polling. The current implementation
        # doesn't work when using a LAN connection to the instrument, so we will comment out for now
        # self.instrument.enable_event(visa.constants.EventType.service_request, visa.constants.VI_QUEUE)
        self.instrument.write(":RUN")
        while True:
            if self.instrument.query_ascii_values(":AER?")[0]:
                break
            time.sleep(0.1)
        self._mode = "RUN"
        self._wave_acquired = False

    def stop(self):
        self._triggers_read = 0
        self.instrument.write(":STOP")
        self._mode = "STOP"
        self._wave_acquired = False

    def _write(self, value):
        self.instrument.write(value)

    def acquire(self, acquire_type="normal", averaging_samples=0):
        """
        :param channel
         string indicating the channel eg. 1, 2, 3, 4, FUNC,(FUNC,includes MATH,functions)
        :param acquire_type:
         "normal"
         "averaging"
         "hresolution" - High Resolution
         "peak" - Peak Detect
        :param averaging_samples:
         averaging_samples: number of samples used when acquire_type is set to averaging
        :return:
        """
        self.write("TIMebase:MODE MAIN")
        if acquire_type.lower() == "normal":
            self.write(":ACQuire:TYPE normal")
        elif acquire_type.lower() == "averaging":
            self.write(":ACQuire:TYPE average")
            self.write(":ACQuire:COUNt {}".format(averaging_samples))
        elif acquire_type.lower() == "hresolution":
            self.write(":ACQuire:TYPE hresolution")
        elif acquire_type.lower() == "peak":
            self.write(":ACQuire:TYPE peak")
        else:
            raise ValueError("Invalid acquire type {}".format(acquire_type))

    def waveform_preamble(self):
        values = self.query_ascii_values(":WAV:PRE?")
        wav_form_dict = {"0": "BYTE", "1": "WORD", "4": "ASCii"}
        acq_type_dict = {
            "0": "NORMAL",
            "1": "PEAK",
            "2": "AVERAGE",
            "3": "HIGH RESOLUTION",
        }
        labels = [
            "format",
            "acquire",
            "wav_points",
            "avg_cnt",
            "x_increment",
            "x_origin",
            "x_reference",
            "y_increment",
            "y_origin",
            "y_reference",
        ]
        preamble = {}
        for index, val in enumerate(values):
            if index == 0:
                preamble["format"] = wav_form_dict[str(int(values[0]))]
            elif index == 1:
                preamble["acquire"] = acq_type_dict[str(int(values[1]))]
            else:
                preamble[labels[index]] = val
        return preamble

    def waveform_values(self, signals, file_name="", file_type="csv"):
        """
        :param signals:
         The channel ie "1", "2", "3", "4", "MATH", "FUNC"
        :param file_name:
         If
        :param file_type:
        :return:
        """
        signals = self.digitize(signals)
        return_vals = {}
        for sig in signals:
            return_vals[sig] = []
            results = return_vals[sig]
            self.write(":WAV:SOUR {}".format(sig))
            self.write(":WAV:FORM BYTE")
            self.write(":WAV:POIN:MODE RAW")
            preamble = self.waveform_preamble()
            data = self.retrieve_waveform_data()
            for index, datum in enumerate(data):
                time_val = index * preamble["x_increment"]
                y_val = (
                    preamble["y_origin"]
                    + (datum - preamble["y_reference"]) * preamble["y_increment"]
                )
                results.append((time_val, y_val))
        if file_name and file_type == "csv":  # Needs work for multiple references
            with open(file_name, "w") as f:
                f.write("x,y")
                for label in sorted(preamble):
                    f.write(",{},{}".format(label, preamble[label]))
                f.write("\n")
                for time_val, y_val in enumerate(results):
                    f.write(
                        "{time_val},{voltage}\n".format(
                            time_val=time_val, voltage=y_val
                        )
                    )
        elif file_name and file_type == "bin":
            raise NotImplementedError("Binary Output not implemented")
        return results

    def retrieve_waveform_data(self):
        self.instrument.write(":WAV:DATA?")
        time.sleep(0.2)
        data = self.read_raw()[:-1]  # Strip \n
        if data[0:1] != "#".encode():
            raise InstrumentError("Pound Character missing in waveform data response")
        valid_bytes = data[int(data[1:2]) + 2 :]  # data[1] denotes length value digits
        values = struct.unpack("%dB" % len(valid_bytes), valid_bytes)
        return values

    def digitize(self, signals):
        signals = [self.validate_signal(sig) for sig in signals]
        self.write(":DIG {}".format(",".join(signals)))
        return signals

    def validate_signal(self, signal):
        """
        :param signal: String ie. "1", "2", "3", "4", "func", "math"
        :return:
        """
        try:
            if not (1 <= int(signal) <= 4):
                raise ValueError("Invalid source channel {}".format(signal))
            else:
                signal = "CHAN{}".format(int(signal))
        except ValueError:
            if signal.lower() not in ["func", "math"]:
                raise ValueError("Invalid source channel {}".format(signal))
            signal = signal.lower()
        return signal

    def reset(self):
        self.instrument.write("*CLS;*RST;:STOP")
        time.sleep(0.15)
        self._check_errors()

    def auto_scale(self):
        self.write(":AUT")

    def save_setup(self, file_name):
        self.instrument.timeout = 5000
        try:
            with open(file_name, "w") as f:
                setup = self.query(":SYSTem:SETup?")
                f.write(setup)
        finally:
            self.instrument.timeout = 1000

    def load_setup(self, file_name):
        self.instrument.timeout = 5000
        try:
            with open(file_name, "r") as f:
                setup = f.read()
            self.write(":SYSTem:SETup {}".format(setup))
        finally:
            self.instrument.timeout = 1000

    def query(self, value):
        try:
            response = self.instrument.query(value)
        finally:
            self._raise_if_error()
        return response

    def query_bool(self, value):
        return bool(self.query_ascii_value(value))

    def query_binary_values(self, value):
        response = self.instrument.query_binary_values(value)
        self._raise_if_error()
        return response

    def query_ascii_values(self, value):
        response = self.instrument.query_ascii_values(value)
        self._raise_if_error()
        return response

    def query_ascii_value(self, value):
        return self.query_ascii_values(value)[0]

    def query_value(self, base_str, *args, **kwargs):
        formatted_string = self._format_string(base_str, **kwargs)
        return self.query_ascii_value(formatted_string)

    def query_after_acquire(self, base_str, *args, **kwargs):
        self.wait_for_acquire()
        try:
            formatted_string = self._format_string(base_str, **kwargs)
            return self.instrument.query_ascii_values(formatted_string)[0]
        except:
            self.instrument.close()
            self.instrument.open()
            raise

    def wait_for_trigger(self, timeout):
        """
        Waits for trigger for a set amount of time.
        If no trigger occurs, cancel the current measurement request
        Two options available:
        self._trigger_event(timeout) # Uses PyVisa Events
        self._trigger_poll(timeout) # Polls :TER? register
        :param timeout: timeout in seconds waiting for a trigger
        Exception raised on timeout
        :return:
        """
        self._trigger_poll(timeout)
        # self._trigger_event(timeout)

    def _trigger_event(self, timeout):
        try:
            self.instrument.wait_on_event(
                pyvisa.constants.EventType.service_request, timeout * 1000
            )
            self._triggers_read += 1
        except pyvisa.VisaIOError:
            self.instrument.clear()
            raise
        finally:
            self.instrument.disable_event(
                pyvisa.constants.EventType.service_request, pyvisa.constants.VI_QUEUE
            )
            self.instrument.discard_events(
                pyvisa.constants.EventType.service_request, pyvisa.constants.VI_QUEUE
            )

    def _trigger_poll(self, timeout):
        start = time.time()
        while True:
            trigger = self.instrument.query_ascii_values(":TER?")[0]
            if trigger:
                break
            if time.time() - start > timeout:
                raise TimeoutError("Trigger didn't occur in {}s".format(timeout))
        self._triggers_read += 1

    def wait_for_acquire(self):
        if not self._triggers_read:
            self.wait_for_trigger(1)
        if self._wave_acquired:
            return

        elif self._mode == "SINGLE":
            # Wait for mode to change to stop
            start = time.time()
            timeout = self._store["time_base_wait"] * 1.2
            while int(self.instrument.query_ascii_values(":OPER:COND?")[0]) & 1 << 3:
                if time.time() - start > timeout:
                    raise TimeoutError("Waveform did not acquire in the specified time")
            self._wave_acquired = True
            return
        elif self._mode == "RUN":
            # Can't detect a complete acquire, just going to have to risk it
            self._wave_acquired = True
            return
        else:
            raise Exception(
                "Cannot acquire waveform in this mode: {}".format(self._mode)
            )

    def read_raw(self):
        data = self.instrument.read_raw()
        self._raise_if_error()
        return data

    def _check_errors(self):
        time.sleep(0.1)
        resp = self.instrument.query("SYST:ERR?")
        code, msg = resp.strip("\n").split(",")
        code = int(code)
        msg = msg.strip('"')
        return code, msg

    def _raise_if_error(self):
        errors = []
        while True:
            code, msg = self._check_errors()
            if code != 0:
                errors.append((code, msg))
            else:
                break
        if errors:
            raise InstrumentError(
                "Error(s) Returned from DSO\n"
                + "\n".join(
                    ["Code: {}\nMessage:{}".format(code, msg) for code, msg in errors]
                )
            )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.instrument.close()
        self.is_connected = False

    def write(self, base_str, *args, **kwargs):
        formatted_string = self._format_string(base_str, **kwargs)
        self._write(formatted_string)

    def _format_string(self, base_str, **kwargs):
        kwargs["self"] = self
        prev_string = base_str
        while True:
            cur_string = prev_string.format(**kwargs)
            if cur_string == prev_string:
                break
            prev_string = cur_string
        return cur_string

    def store(self, store_dict, *args, **kwargs):
        """
        Store a dictionary of values in TestClass
        :param kwargs:
        Dictionary containing the parameters to store
        :return:
        """
        new_dict = store_dict.copy()
        for k, v in store_dict.items():
            # I want the same function from write to set up the string before putting it in new_dict
            try:
                new_dict[k] = v.format(**kwargs)
            except:
                pass
        self._store.update(new_dict)

    def store_and_write(self, params, *args, **kwargs):
        base_str, store_dict = params
        self.store(store_dict)
        self.write(base_str, *args, **kwargs)

    def get_identity(self) -> str:
        """
        :return: AGILENT TECHNOLOGIES,<model>,<serial number>,X.XX.XX
                <model> ::= the model number of the instrument
                <serial number> ::= the serial number of the instrument
                <X.XX.XX> ::= the software revision of the instrument
        """
        return self.query("*IDN?").strip()
