from __future__ import annotations

import time
from typing import Optional, Callable, Mapping, Sequence
from dataclasses import dataclass

Signal = str
PinName = str


@dataclass(frozen=True)
class PinSetState:
    off: set[PinName]
    on: set[PinName]


AddressHandlerUpdateCallback = Callable[[PinSetState, PinSetState, float, bool], None]


class VirtualMux:
    pin_list: Sequence[PinName] = []
    default_signal = ""
    clearing_time = 0.0

    def __init__(self, update_pins: Optional[AddressHandlerUpdateCallback] = None):
        # The last time this mux changed state. This is used in some jigs
        # to enforce a minimum settling time. Perhaps is would be nice to
        # deprecate this and add a `settle_at_least()` method?
        self.state_update_time = 0.0  # time.time()

        self._update_pins: AddressHandlerUpdateCallback
        if update_pins is None:
            self._update_pins = self._default_update_pins
        else:
            self._update_pins = update_pins

        # We force the pin_list to be an ordered sequence, because if the
        # mux is defined with a map_tree, we need the ordering. But after
        # initialisation, we only need set operations on the pin list, so
        # we convert here and keep a reference on the object for future use.
        self._pin_set = set(self.pin_list)

        self._state = ""

        self._signal_map: dict[Signal, set[PinName]] = self.map_signals()

        # If it wasn't already defined, define the implicit signal "" which
        # can be used for no pins to be set.
        if "" not in self._signal_map:
            self._signal_map[""] = set()

    def __call__(self, signal_output: Signal, trigger_update: bool = True) -> None:
        """
        Convenience to avoid having to type jig.mux.<MuxName>.multiplex.

        With this you can just type jig.mux.<MuxName> which is a small, but
        useful saving for the most common method call.
        """
        self.multiplex(signal_output, trigger_update)

    @staticmethod
    def _default_update_pins(
            setup: PinSetState,
            final: PinSetState,
            minimum_change_time: float = 0.0,
            trigger_update: bool = True
    ) -> None:
        """
        Output callback to effect a state change in the mux.

        This is a default implementation which simply prints the planned state change to.
        stdout. When instantiated as part of a jig driver, this will end up connected
        to an AddressHandler to do the actual pin changes in hardware.
        """
        print(setup, final, minimum_change_time, trigger_update)

    def multiplex(self, signal_output, trigger_update=True):
        """
        Update the multiplexer state to signal_output.

        The update is a two-step processes. By default, the change happens on
        the second step. This can be modified by subclassing and overriding the
        _calculate_pins method.

        If trigger_update is true, the output will update immediately. If false,
        multiple mux changes can be set and then when trigger_update is finally
        set to True all changes will happen at once.

        If the signal_output is different to the previous state,
        self.state_update_time is updated to the current time.
        """
        if signal_output not in self._signal_map:
            name = self.__class__.__name__
            raise ValueError(f"Signal '{signal_output}' not valid for multiplexer '{name}'")

        setup, final = self._calculate_pins(self._state, signal_output)
        self._update_pins(setup, final, self.clearing_time, trigger_update)
        if signal_output != self._state:
            self.state_update_time = time.time()
        self._state = signal_output

    def _calculate_pins(self, old_signal, new_signal) -> (PinSetState, PinSetState):
        """
        Calculate the pin sets for the two-step state change.

        The two-step state change allows us to implement break-before-make or
        make-before-break behaviour. By default, the first state changes
        no pins and the second state sets the pins required for new_signal.

        Subclasses can override this method to change the behaviour.
        """
        setup = PinSetState(set(), set())
        on_pins = self._signal_map[new_signal]
        final = PinSetState(self._pin_set - on_pins, on_pins)
        return setup, final

    def defaults(self):
        """
        Set the multiplexer to the default state.
        """
        self.multiplex(self.default_signal)

    def map_signals(self) -> dict[Signal, set[PinName]]:
        """
        Default implementation of the signal mapping

        We need to construct a dictionary mapping signals to a set of pins.
        In the case the self.map_list is set, the is pretty trival.
        If the mux is defined with self.map_tree we have more work to
        do...

        If subclassed, you can use any scheme to create the mapping that
        returns a suitable dictionary.
        """
        if hasattr(self, "map_tree"):
            raise NotImplementedError
        elif hasattr(self, "map_list"):
            return {sig: set(pins) for sig, *pins in self.map_list}
        else:
            raise ValueError("VirtualMux subclass must define either map_tree or map_list")

        #     try:
        #         self.map_list
        #     except AttributeError:
        #         pass
        #     else:
        #         for signal in self.map_list:
        #             self.map_single(*signal)
        # else:
        #     self._map_tree(map_tree, 0, 0)

    def _map_tree(self, branch, base_offset, base_bits):
        """recursively add nested signal lists to the signal map.
        branch: is the current sub branch to be added. At the first call
        level, this would be initialised with self.map_tree. It can be
        any sequence, possibly nested.

        base_offset: should be the integer value of the address
        where the branch enters into the top level multiplexer.

        base_bits: At each call level, this represents the number
        of less significant address bits that are used to represent
        multiplexers higher up the chain.

        example:
        This shows 10 signal, routed through a number of multiplexers.
        Mux B and Mux B' are distinct, but address of common control
        signals. Mux C and Mux B/B' are nested to various levels into
        the final multiplexer Mux A.

        The pin_list defines the control signals from least to most significant
        The map_tree defines the signals into each multipler. Nesting containers
        reflects the nesting of mux's.
                                          __________
        a0-------------------------------|          |
                              ________   |          |
        a1_b0----------------|        |--|  Mux A   |
        a1_b1----------------| Mux B  |  |   4:1    |
        a1_b2----------------|  4:1   |  |          |
                     (None)--|_x3__x2_|  |          |
                                         |          |
                              ________   |          |
        a2_b0----------------|        |  |          |
                   _______   |        |--|          |------ Output
        a2_b1_c0--| Mux C |--| Mux B' |  |          |
        a2_b1_c1--|  2:1  |  |  4:1   |  |          |
                  |___x4__|  |        |  |          |
                             |        |  |          |
        a2_b2----------------|        |  |          |
        a2_b3----------------|        |  |          |
                             |_x3__x2_|  |          |
                                         |          |
        a3-------------------------------|          |
                                         |__x1__x0__|

        class Mux(VirtualMux):
            pin_list = ("x0", "x1", "x2", "x3", "x4")
            map_tree = ("a0",
                        (#a1
                            "a1_b0",
                            "a1_b1",
                            "a1_b2",
                            None,
                        ),
                        (#a2
                            "a2_b0",
                            (#b1
                                "a2_b1_c0",
                                "a2_b1_c1",
                            ),
                            "a2_b2",
                            "a2_b3",
                        ),
                        "a3"
                    )

        Alternatively:

        class Mux(VirtualMux):
            pin_list = ("x0", "x1", "x2", "x3", "x4")

            mux_c = ("a2_b1_c0", "a2_b1_c1")
            mux_b1 = ("a1_b0", "a1_b1", "a1_b2", None)
            mux_b2 = ("a2_b0", mux_c, "a2_b2", "a2_b3")

            map_tree = ("a0", mux_b1, mux_b2, "a3")

        Final mapping:
        addr    signal
        --------------
        0       a0
        1       a1_b0
        2       a2_b0
        3       a3
        4
        5       a1_b1
        6       a2_b1_c0
        7
        8
        9       a1_b2
        10      a2_b2
        11
        12
        13      (None)
        14      a2_b3
        15
        16
        17
        18
        19
        20
        21
        22      a2_b1_c1
        23
        24
        25
        26
        27
        28
        29
        30
        31

        For Multiplexers that depend on separate control pins, try using the shift_nested function to help
        with sparse mapping
                                          __________
        a0-------------------------------|          |
                              ________   |          |
        a1_b0----------------|        |--|          |
        a1_b1----------------| Mux B  |  |          |
        a1_b2----------------|  4:1   |  |          |
                     (None)--| x3  x2 |  |          |
                             |________|  |          |
                                         |  Mux A   |
        a2-------------------------------|   4:1    |
                              ________   |          |
        a3_c0----------------|        |--|          |
        a3_c1----------------| Mux C  |  |          |
        a3_c2----------------|  4:1   |  |          |
                     (None)--| x5  x4 |  |          |
                             |________|  |          |
                                         |__x1__x0__|

        class Mux(VirtualMux):
            pin_list = ("x0", "x1", "x2", "x3", "x4")

            mux_c = ("a3_c0", "a3_c1", "a3_c2", None)
            mux_b = ("a1_b0", "a1_b1", "a1_b2", None)

            map_tree = (
            "a0",
            mux_b,
            shift_nested(mux_c, [2]),  # 2 in indicative on how many pins to skip. This case is (x2, x3) from mux_b
            "a3")

        """
        for i, signal in enumerate(branch):
            current_index = (i * 1 << base_bits) + base_offset

            if isinstance(signal, str):
                # Add signal to out mapping
                self._check_duplicates(current_index, signal)
                self.signal_map[signal] = current_index
            elif signal is None:
                pass
            else:
                # We have a nested signal definition, so we recurse.
                # number of addr bits needed for the current branch:
                current_bits = int(ceil(log(len(branch), 2)))
                self._map_tree(signal, current_index, base_bits + current_bits)

    def __repr__(self):
        return self.__class__.__name__


class VirtualSwitch(VirtualMux):
    """
    A VirtualMux that controls a single pin.

    A virtual switch is a multiplexer with a single pin. The multiplex
    function can accept either boolean values or the strings 'TRUE' and
    'FALSE'. The virtual address used to switch can be defined as a list
    with the single element (as if it were a multiplexer) or by using the
    shorthand which is to define the pin_name attribute as a string.
    """

    pin_name = ""
    map_tree = ("FALSE", "TRUE")

    def multiplex(self, signal_output, trigger_update=True):
        if signal_output is True:
            signal = "TRUE"
        elif signal_output is False:
            signal = "FALSE"
        else:
            signal = signal_output
        super().multiplex(signal, trigger_update=trigger_update)

    def __init__(self, pin_name=None):
        if pin_name is None:
            pin_name = self.pin_name
        if not self.pin_list:
            self.pin_list = [pin_name]
        super().__init__()


class RelayMatrixMux(VirtualMux):
    clearing_time = 0.01

    def _calculate_pins(self, old_signal, new_signal) -> (PinSetState, PinSetState):
        """
        Override of _calculate_pins to implement break-before-make switching.
        """
        setup = PinSetState(off=self._pin_set, on=set())
        on_pins = self._signal_map[new_signal]
        final = PinSetState(off=self._pin_set - on_pins, on=on_pins)
        return setup, final


class JigMeta(type):
    """
    usage:
    Metaclass for Jig Driver
    Dynamically adds multiplexers and multiplexer groups to the Jig Class definition
    """

    def __new__(mcs, clsname, bases, dct):
        muxes = dct.get("multiplexers", None)
        if muxes is not None:
            mux_dct = {mux.__class__.__name__: mux for mux in muxes}
            dct["mux"] = type("MuxController", (), mux_dct)
        return super().__new__(mcs, clsname, bases, dct)


class JigDriver(metaclass=JigMeta):
    """
    :attribute address_handlers: Iterable of Address Handlers
    [<Address_Handler_Instance1>,...
    "<Address_Handler_InstanceX>"]

    :attribute multiplexers: Iterable Virtual Muxes
    {<Mux_Instance1>,...
    "<Mux_InstanceX>}

    :attribute defaults: Iterable of the default pins to set high on driver reset
    """

    multiplexers = ()
    address_handlers = ()
    defaults = ()

    def __init__(self):
        super().__init__()
        self.virtual_map = VirtualAddressMap()
        for addr_hand in self.address_handlers:
            self.virtual_map.install_address_handler(addr_hand)
        for mux in self.multiplexers:
            self.virtual_map.install_multiplexer(mux)

    def __setitem__(self, key, value):
        self.virtual_map.update_pin_by_name(key, value)

    def __getitem__(self, item):
        return self.virtual_map[item]

    def active_pins(self):
        return self.virtual_map.active_pins()

    def reset(self):
        """
        Reset the multiplexers to the default values
        Raises exception if failed
        :return: None
        """
        self.virtual_map.update_defaults()  # TODO Test if this is required
        for _, mux in self.mux.__dict__.items():
            if isinstance(mux, VirtualMux):
                mux.defaults()

    def iterate_all_mux_paths(self):
        for _, mux in self.mux.__dict__.items():
            if isinstance(mux, VirtualMux):
                yield from self.iterate_mux_paths(mux)

    def iterate_mux_paths(self, mux):
        """
        :param mux: Multiplexer as an object
        :return: Generator of multiplexer signal paths
        """
        for pth in mux.signal_map:
            if pth is not None:
                mux(pth)
                yield "{}: {}".format(mux.__class__.__name__, pth)
        mux.defaults()