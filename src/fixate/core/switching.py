"""
JigDriver is all about switching signals in a jig (and also input, but I'm
ignoring that for now...) At the script level, the key abstraction is a
`VirtualMux`, which switching between a number of `Signals`. Each signal is
defined by a number of `Pins`. When using a relay matrix, a Signal often
corresponds to a single Pin, but it doesn't have to.

Each VirtualMux connects to the VirtualAddressMap. When the multiplex is
called on a mux, the mux determines which pin must be set or cleared


              _____________    ______________________
    SIG_1 ---|       pin0 |   |  VirtualAddressMap  |   _____________________
    SIG_2 ---|  MUX  pin1 |---|                     |   | AddressHandler    |
    SIG_3 ---|            |   |              pin0   |---| pin0, pin1, pin2  |
    SIG_4 ---|____________|   |              pin1   |   |___________________|
                              |              pin2   |   ____________________
                              |                     |   | AddressHandler   |
              _____________   |              pin3   |---| pin3, pin4       |
    SIG_5 ---|       pin2 |   |              pin4   |   |__________________|
    SIG_6 ---|  MUX  pin3 |---|                     |    ___________________
    SIG_7 ---|       pin4 |   |              pin5   |---| AddressHandler   |
    SIG_8 ---|       pin5 |   |                     |   | pin5             |
             |____________|   |_____________________|   |__________________|
                            ^                         ^
                update_pins callback           AddressHandler.set_pins()
                VirtualAddressMap.add_update()
"""

from __future__ import annotations

import itertools
import time
from typing import (
    TYPE_CHECKING,
    Generic,
    Optional,
    Callable,
    Sequence,
    TypeVar,
    Generator,
    Union,
    Collection,
    Dict,
    Any,
    FrozenSet,
    Set,
)
from dataclasses import dataclass
from functools import reduce
from operator import or_

Signal = str
Pin = str
PinList = Sequence[Pin]
PinSet = FrozenSet[Pin]
SignalMap = Dict[Signal, PinSet]

if TYPE_CHECKING:
    # The self reference doesn't work at runtime, by mypy knows what it means.
    TreeDef = Sequence[Union[Signal, TreeDef]]
else:
    TreeDef = Sequence[Any]


@dataclass(frozen=True)
class PinSetState:
    off: PinSet = frozenset()
    on: PinSet = frozenset()

    def __or__(self, other: PinSetState) -> PinSetState:
        if isinstance(other, PinSetState):
            return PinSetState(self.off | other.off, self.on | other.on)
        return NotImplemented


@dataclass(frozen=True)
class PinUpdate:
    setup: PinSetState = PinSetState()
    final: PinSetState = PinSetState()
    minimum_change_time: float = 0.0

    def __or__(self, other: PinUpdate) -> PinUpdate:
        if isinstance(other, PinUpdate):
            return PinUpdate(
                setup=self.setup | other.setup,
                final=self.final | other.final,
                minimum_change_time=max(
                    self.minimum_change_time, other.minimum_change_time
                ),
            )
        return NotImplemented


PinUpdateCallback = Callable[[PinUpdate, bool], None]


class VirtualMux:
    pin_list: PinList = ()
    clearing_time: float = 0.0

    ###########################################################################
    # These methods are the public API for the class

    def __init__(self, update_pins: Optional[PinUpdateCallback] = None):
        # The last time this mux changed state. This is used in some jigs
        # to enforce a minimum settling time. Perhaps is would be nice to
        # deprecate this and add a `settle_at_least()` method?
        self.state_update_time = 0.0  # time.time()

        self._update_pins: PinUpdateCallback
        if update_pins is None:
            self._update_pins = self._default_update_pins
        else:
            self._update_pins = update_pins

        # We annotate the pin_list to be an ordered sequence, because if the
        # mux is defined with a map_tree, we need the ordering. But after
        # initialisation, we only need set operations on the pin list, so
        # we convert here and keep a reference to the set for future use.
        self._pin_set = frozenset(self.pin_list)

        self._state = ""

        self._signal_map: SignalMap = self._map_signals()

        # If it wasn't already defined, define the implicit signal "" which
        # can be used to signify no pins active.
        if "" not in self._signal_map:
            self._signal_map[""] = frozenset()

    def __call__(self, signal_output: Signal, trigger_update: bool = True) -> None:
        """
        Convenience to avoid having to type jig.mux.<MuxName>.multiplex.

        With this you can just type jig.mux.<MuxName> which is a small, but
        useful saving for the most common method call.
        """
        self.multiplex(signal_output, trigger_update)

    def multiplex(self, signal_output: Signal, trigger_update: bool = True) -> None:
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

        In general, subclasses should not override. (VirtualSwitch does, but then
        delegates the real work to this method to ensure consistent behaviour.)
        """
        if signal_output not in self._signal_map:
            name = self.__class__.__name__
            raise ValueError(
                f"Signal '{signal_output}' not valid for multiplexer '{name}'"
            )

        setup, final = self._calculate_pins(self._state, signal_output)
        self._update_pins(PinUpdate(setup, final, self.clearing_time), trigger_update)
        if signal_output != self._state:
            self.state_update_time = time.time()
        self._state = signal_output

    def switch_through_all_signals(self) -> Generator[str, None, None]:
        # not sure if we should keep this.
        # probably better to have a method that returns all
        # signals and use that in a helper somewhere else that loops and
        # switches. I don't like state changes and printing
        # buried in a generator.
        # This was iterate_mux_paths on the JigDriver, but then it had
        # to used internal implementation details. Better to have this
        # as a method on VirtualMux
        for signal in self._signal_map:
            if signal is not None:
                self.multiplex(signal)
                yield f"{self.__class__.__name__}: {signal}"

    def reset(self, trigger_update: bool = True) -> None:
        self.multiplex("", trigger_update)

    ###########################################################################
    # The following methods are potential candidates to override in a subclass

    def _calculate_pins(
        self, old_signal: Signal, new_signal: Signal
    ) -> tuple[PinSetState, PinSetState]:
        """
        Calculate the pin sets for the two-step state change.

        The two-step state change allows us to implement break-before-make or
        make-before-break behaviour. By default, the first state changes
        no pins and the second state sets the pins required for new_signal.

        Subclasses can override this method to change the behaviour. It is
        marked as private to discourage use, but it is intended to be subclassed.
        For example, RelayMatrix overrides this to implement break-before-make
        switching.

        old_signal isn't currently used, but it is provided in case a future
        subclass needs to it calculate the update. In particular, it could be
        useful for make-before-break behaviour.
        """
        setup = PinSetState()
        on_pins = self._signal_map[new_signal]
        final = PinSetState(self._pin_set - on_pins, on_pins)
        return setup, final

    ###########################################################################
    # The following methods are intended as implementation detail and
    # subclasses should avoid overriding.

    def _map_signals(self) -> SignalMap:
        """
        Default implementation of the signal mapping

        We need to construct a dictionary mapping signals to a set of pins.
        In the case that self.map_list is set, the is pretty trival.
        If the mux is defined with self.map_tree we have more work to
        do, which is recursively delegated to _map_tree

        Avoid subclassing. Consider creating helper functions to build
        map_tree or map_list.
        """
        if hasattr(self, "map_tree"):
            return self._map_tree(self.map_tree, self.pin_list, fixed_pins=frozenset())
        elif hasattr(self, "map_list"):
            return {sig: frozenset(pins) for sig, *pins in self.map_list}
        else:
            raise ValueError(
                "VirtualMux subclass must define either map_tree or map_list"
            )

    def _map_tree(self, tree: TreeDef, pins: PinList, fixed_pins: PinSet) -> SignalMap:
        """recursively add nested signal lists to the signal map.
        tree: is the current sub-branch to be added. At the first call
        level, this would be initialised with self.map_tree. It can be
        any sequence, possibly nested.

        pins: The list of pins, taken as LSB to MSB that are assigned
        to the signals in order.

        fixed_pins: At each call level, this represents the pins that
        must be set for each signal in at this level. In the example
        below, these are the bits for a given input to Mux A, when
        mapping all the nested Mux B signals.

        example:
        This shows 10 signals, routed through a number of multiplexers.
        Mux B and Mux B' are distinct, but addressed with common control
        signals. Mux C and Mux B/B' are nested to various levels into
        the final multiplexer Mux A.

        The pin_list defines the control signals from least to most significant
        The map_tree defines the signals into each multiplexer. Nesting containers
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
        with sparse mapping. Note that shift_nested() hasn't been copied over from jig_mapping.

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
            pin_list = ("x0", "x1", "x2", "x3", "x4", "x5")

            mux_c = ("a3_c0", "a3_c1", "a3_c2", None)
            mux_b = ("a1_b0", "a1_b1", "a1_b2", None)

            map_tree = (
                "a0",
                mux_b,
                "a2",
                shift_nested(mux_c, [2]),  # 2 in indicative on how many pins to skip. This case is (x2, x3) from mux_b
            )

        Note:
            If shift_nested is needed, I think I'd re-implement something like TreeMap that
            can be used to define the mux.

        class TreeMap:
            signals: Sequence[pin | TreeMap]
            pins: PinSet

        class Mux(VirtualMux):
            mux_c = TreeMap(("a3_c0", "a3_c1", "a3_c2", None), ("x4", "x5"))
            mux_b = TreeMap(("a1_b0", "a1_b1", "a1_b2", None), ("x2", "x3"))
            map_tree = TreeMap(("a0", mux_b, "a2", mux_c), ("x1", "x0"))
        """
        signal_map: SignalMap = dict()

        bits_at_this_level = (len(tree) - 1).bit_length()
        pins_at_this_level = pins[:bits_at_this_level]

        for signal_or_tree, pins_for_signal in zip(
            tree, generate_bit_sets(pins_at_this_level)
        ):
            if signal_or_tree is None:
                continue
            if isinstance(signal_or_tree, Signal):
                signal_map[signal_or_tree] = frozenset(pins_for_signal) | fixed_pins
            else:
                signal_map.update(
                    self._map_tree(
                        tree=signal_or_tree,
                        pins=pins[bits_at_this_level:],
                        fixed_pins=frozenset(pins_for_signal) | fixed_pins,
                    )
                )

        return signal_map

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self._state}')"

    @staticmethod
    def _default_update_pins(
        pin_updates: PinUpdate, trigger_update: bool = True
    ) -> None:
        """
        Output callback to effect a state change in the mux.

        This is a default implementation which simply prints the planned state change to.
        stdout. When instantiated as part of a jig driver, this will end up connected
        to an AddressHandler to do the actual pin changes in hardware.

        In general, this method shouldn't be overridden in a subclass. An alternative
        can be provided to __init__.
        """
        print(pin_updates, trigger_update)


class VirtualSwitch(VirtualMux):
    """
    A VirtualMux that controls a single pin.

    A virtual switch is a multiplexer with a single pin. The multiplex
    function can accept either boolean values or the strings 'TRUE' and
    'FALSE'. The virtual address used to switch can be defined as a list
    with the single element (as if it were a multiplexer) or by using the
    shorthand which is to define the pin_name attribute as a string.
    """

    pin_name: Pin = ""
    map_tree = ("FALSE", "TRUE")

    def multiplex(
        self, signal_output: Union[Signal, bool], trigger_update: bool = True
    ) -> None:
        if signal_output is True:
            signal = "TRUE"
        elif signal_output is False:
            signal = "FALSE"
        else:
            signal = signal_output
        super().multiplex(signal, trigger_update=trigger_update)

    def __init__(
        self,
        update_pins: Optional[PinUpdateCallback] = None,
    ):
        if not self.pin_list:
            self.pin_list = [self.pin_name]
        super().__init__(update_pins)


class RelayMatrixMux(VirtualMux):
    clearing_time = 0.01

    def _calculate_pins(
        self, old_signal: Signal, new_signal: Signal
    ) -> tuple[PinSetState, PinSetState]:
        """
        Override of _calculate_pins to implement break-before-make switching.
        """
        setup = PinSetState(off=self._pin_set, on=frozenset())
        on_pins = self._signal_map[new_signal]
        final = PinSetState(off=self._pin_set - on_pins, on=on_pins)
        return setup, final


class AddressHandler:
    """
    Controls the IO for a set of pins.

    For output, it is assumed that all the pins under the of a given
    AddressHandler are updated in one operation.

    This base class doesn't give you much. You need to create a subclass
    that implement a set_pins() method.

    :param pin_list: Sequence of pins
    """

    pin_list: Sequence[Pin] = ()

    def set_pins(self, pins: Collection[Pin]) -> None:
        """
        Called by the VirtualAddressMap to write out pin changes.

        : param pins: is a collection of pins that should be made active. All other
        pins defined by the AddressHandler should be cleared.
        """
        raise NotImplementedError


class PinValueAddressHandler(AddressHandler):
    """Maps pins to bit values then combines the bit values for an update"""

    def __init__(self) -> None:
        super().__init__()
        self._pin_lookup = {
            pin: bit for pin, bit in zip(self.pin_list, bit_generator())
        }

    def set_pins(self, pins: Collection[Pin]) -> None:
        value = sum(self._pin_lookup[pin] for pin in pins)
        self._update_output(value)

    def _update_output(self, value: int) -> None:
        # perhaps it's easy to compose by passing the output
        # function into __init__, like what we did with the VirtualMux?
        bits = len(self.pin_list)
        print(f"0b{value:0{bits}b}")


class FTDIAddressHandler(PinValueAddressHandler):
    """
    An address handler which uses the ftdi driver to control pins.

    We create this concrete address handler because we use it most
    often. FT232 is used to bit-bang to shift register that are control
    the switching in a jig.
    """

    def _update_output(self, value: int) -> None:
        raise NotImplementedError


class VirtualAddressMap:
    """
    The supervisor loops through the attached virtual multiplexers each time a mux update is triggered.
    """

    def __init__(self, handlers: Sequence[AddressHandler]):
        # used to work out which pins get routed to which address handler
        self._handler_pin_sets: list[tuple[PinSet, AddressHandler]] = []
        for handler in handlers:
            self._handler_pin_sets.append((frozenset(handler.pin_list), handler))
        self._all_pins = frozenset(
            itertools.chain.from_iterable(handler.pin_list for handler in handlers)
        )

        # a list of updates that haven't been sent to address handlers yet. This
        # allows a few mux changes to get updated at the same time.
        self._pending_updates: list[PinUpdate] = []
        self._active_pins: set[Pin] = set()

    def add_update(self, pin_update: PinUpdate, trigger_update: bool = True) -> None:
        """This method should be registered with each virtual mux to route pin changes."""
        self._pending_updates.append(pin_update)

        if trigger_update:
            self._do_pending_updates()

    def _do_pending_updates(self) -> None:
        """
        Collate pending updates and send pins to respective address handlers.

        1.  For each pending update, combine pins to clear and pins to set.
        2.  Find the longest `minimum_change_time` of all the updates
        3.  Find the AddressHandler required to set each pin.
        4.  Check if there is actually anything to change. Only write out
            changes that are required.
        5.  Do the setup phase
        6.  Wait the required change time
        7.  Do the final phase
        """
        collated = reduce(or_, self._pending_updates, PinUpdate())
        self._pending_updates = []

        if in_both := collated.setup.on & collated.setup.off:
            raise ValueError(f"The following pins need to be on and off {in_both}")

        if in_both := collated.final.on & collated.final.off:
            raise ValueError(f"The following pins need to be on and off {in_both}")

        self._dispatch_pin_state(collated.setup)
        time.sleep(collated.minimum_change_time)
        self._dispatch_pin_state(collated.final)

    def _dispatch_pin_state(self, new_state: PinSetState) -> None:
        # check all pins actually have an address handler to send to
        if unknown_pins := (new_state.on | new_state.off) - self._all_pins:
            raise ValueError(f"Can't switch unknown pin(s) {', '.join(unknown_pins)}.")

        new_active_pins = (self._active_pins | new_state.on) - new_state.off
        if new_active_pins != self._active_pins:
            self._active_pins = new_active_pins
            for pin_set, handler in self._handler_pin_sets:
                handler.set_pins(pin_set & self._active_pins)

    def active_pins(self) -> Set[Pin]:
        return self._active_pins

    def reset(self) -> None:
        """
        Sets all pins to be inactive.
        """
        self._dispatch_pin_state(PinSetState(off=self._all_pins))

    def update_input(self) -> None:
        """
        Iterates through the address_handlers and reads the values back to update the pin values for the digital inputs
        :return:
        """
        raise NotImplementedError

    # used in a few scripts
    def update_pin_by_name(
        self, name: Pin, value: bool, trigger_update: bool = True
    ) -> None:
        raise NotImplementedError

    # not used in any scripts
    def update_pins_by_name(
        self, pins: Collection[Pin], trigger_update: bool = True
    ) -> None:
        raise NotImplementedError

    def __getitem__(self, item: Pin) -> bool:
        """Get the value of a pin. (only inputs? or state of outputs also?)"""
        raise NotImplementedError

    def __setitem__(self, key: Pin, value: bool) -> None:
        """Set a pin"""
        raise NotImplementedError


class MuxGroup:
    """
    Group multiple VirtualMux's, for use in a single Jig Driver.

    If a test script, it is expected that MuxGroup will be subclassed, with attributes
    being each required VirtualMux subclass. This can be done using a dataclass:

    @dataclass
    class JigMuxGroup(MuxGroup):
        mux_one: MuxOne = field(default_factory=MuxOne)
        mux_two: MuxTwo = field(default_factory=MuxTwo)
    """

    def get_multiplexers(self) -> list[VirtualMux]:
        return [attr for attr in self.__dict__.values() if isinstance(attr, VirtualMux)]

    def reset(self) -> None:
        mux_list = self.get_multiplexers()
        if len(mux_list) == 0:
            return

        for mux in mux_list[:-1]:
            mux.reset(trigger_update=False)
        mux_list[-1].reset(trigger_update=True)

    def active_signals(self) -> list[str]:
        return [str(mux) for mux in self.get_multiplexers()]


JigSpecificMuxGroup = TypeVar("JigSpecificMuxGroup", bound=MuxGroup)


class JigDriver(Generic[JigSpecificMuxGroup]):
    """
    Combine multiple VirtualMux's and multiple AddressHandler's.

    The jig driver joins muxes to handlers by matching up pin definitions.
    """

    def __init__(
        self,
        mux_group_factory: Callable[[], JigSpecificMuxGroup],
        handlers: Sequence[AddressHandler],
    ):
        self.virtual_map = VirtualAddressMap(handlers)

        self.mux = mux_group_factory()
        for mux in self.mux.get_multiplexers():
            # Perhaps we should instantiate the virtual mux here
            # and pass in the virtual_map.add_update. But we'd have to do some
            # magic in the MuxGroup call to pass add_update to each VirtualMux
            # constructor, and I was hoping to just use a dataclass...
            mux._update_pins = self.virtual_map.add_update

    def __setitem__(self, key: Pin, value: bool) -> None:
        self.virtual_map.update_pin_by_name(key, value)

    def __getitem__(self, item: Pin) -> bool:
        return self.virtual_map[item]

    def active_pins(self) -> Set[Pin]:
        return self.virtual_map.active_pins()

    def reset(self) -> None:
        """
        Reset all pins

        This leaves multiplexers in the current state, which may not
        match up with the real pin state. To reset all the multiplexers,
        use JigDriver.mux.reset() instead.
        """
        self.virtual_map.reset()

    def iterate_all_mux_paths(self) -> Generator[str, None, None]:
        for _, mux in self.mux.__dict__.items():
            if isinstance(mux, VirtualMux):
                yield from mux.switch_through_all_signals()


T = TypeVar("T")


def generate_bit_sets(bits: Sequence[T]) -> Generator[set[T], None, None]:
    """
    Create subsets of bits, representing bits of a list of integers

    This is easier to explain with an example
    list(generate_bit_set(["x0", "x1"])) -> [set(), {'x0'}, {'x1'}, {'x0', 'x1'}]
    """
    int_list = range(1 << len(bits)) if len(bits) != 0 else range(0)
    return (
        {bit for i, bit in enumerate(bits) if (1 << i) & index} for index in int_list
    )


def bit_generator() -> Generator[int, None, None]:
    """b1, b10, b100, b1000, ..."""
    return (1 << counter for counter in itertools.count())
