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
    Generic,
    Optional,
    Callable,
    Sequence,
    TypeVar,
    Generator,
    Union,
    Collection,
    Dict,
    FrozenSet,
    Iterable,
)
from dataclasses import dataclass
from functools import reduce
from operator import or_

Signal = str
Pin = str
PinList = Sequence[Pin]
PinSet = FrozenSet[Pin]
SignalMap = Dict[Signal, PinSet]
TreeDef = Sequence[Union[Signal, "TreeDef"]]


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
        self._last_update_time = time.monotonic()

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

        # Define the implicit signal "" which can be used to turn off all pins.
        # If the signal map already has this defined, raise an error. In the old
        # implementation, it allows the map to set this, but when switching the
        # behaviour was hard coded. Any mux that changed the definition would
        # have silently done the "wrong" thing. We can revisit this if we find
        # a good application to override, but for now, don't silently allow something
        # that probably isn't correct.
        if "" not in self._signal_map:
            self._signal_map[""] = frozenset()
        else:
            raise ValueError('The empty signal, "", should not be explicitly defined')

        if hasattr(self, "default_signal"):
            raise ValueError("'default_signal' should not be set on a VirtualMux")

    def __call__(self, signal: Signal, trigger_update: bool = True) -> None:
        """
        Convenience to avoid having to type jig.mux.<MuxName>.multiplex.

        With this you can just type jig.mux.<MuxName> which is a small, but
        useful saving for the most common method call.
        """
        self.multiplex(signal, trigger_update)

    def multiplex(self, signal: Signal, trigger_update: bool = True) -> None:
        """
        Update the multiplexer state to signal.

        The update is a two-step processes. By default, the change happens on
        the second step. This can be modified by subclassing and overriding the
        _calculate_pins method.

        If trigger_update is true, the output will update immediately. If false,
        multiple mux changes can be set and then when trigger_update is finally
        set to True all changes will happen at once.

        In general, subclasses should not override. (VirtualSwitch does, but then
        delegates the real work to this method to ensure consistent behaviour.)
        """
        if signal not in self._signal_map:
            name = self.__class__.__name__
            raise ValueError(f"Signal '{signal}' not valid for multiplexer '{name}'")

        setup, final = self._calculate_pins(self._state, signal)
        self._update_pins(PinUpdate(setup, final, self.clearing_time), trigger_update)
        if signal != self._state:
            self._last_update_time = time.monotonic()
        self._state = signal

    def all_signals(self) -> tuple[Signal, ...]:
        return tuple(self._signal_map.keys())

    def reset(self, trigger_update: bool = True) -> None:
        self.multiplex("", trigger_update)

    def wait_at_least(self, duration: float) -> None:
        """
        Ensure at least `duration` seconds have elapsed since the signal was switched.

        This can be used to ensure a minimum settling time has passed since
        a particular signal was enabled.
        """
        now = time.monotonic()
        wait_until = self._last_update_time + duration
        if wait_until > now:
            time.sleep(wait_until - now)

    def pins(self) -> frozenset[Pin]:
        """
        Return the set off all pins used by this mux
        """
        return self._pin_set

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

        Example:
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
            tree, _generate_bit_sets(pins_at_this_level)
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
    map_tree = ("Off", "On")

    def multiplex(
        self, signal: Union[Signal, bool], trigger_update: bool = True
    ) -> None:
        if signal is True:
            converted_signal = "On"
        elif signal is False:
            converted_signal = "Off"
        else:
            converted_signal = signal
        super().multiplex(converted_signal, trigger_update=trigger_update)

    def __call__(
        self, signal: Union[Signal, bool], trigger_update: bool = True
    ) -> None:
        """Override call to set the type on signal_output correctly."""
        self.multiplex(signal, trigger_update)

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

        # if the signal doesn't change, we don't want open then close again
        # so return the 'final' state for both setup and final.
        if old_signal == new_signal:
            return final, final
        return setup, final


class AddressHandler:
    """
    Controls the IO for a set of pins.

    For output, it is assumed that all the pins under the of a given
    AddressHandler are updated in one operation.

    An AddressHandler should lazily open any required hardware
    resource. Ideally, it should be possible to instantiate and
    inspect the AddressHandler without requiring hardware to
    be connected. When `set_pins` is called, the implementation
    should check for the required hardware connection and open
    that driver when first called.

    Further, calling close() may "uninitialize" the driver. The
    next time set_pins is called, the handler will re-open hardware.
    """

    def __init__(self, pins: Sequence[Pin]) -> None:
        # we convert the pin list to an immutable tuple, incase the
        # caller passing in a mutable sequence that gets modified...
        self.pin_list = tuple(pins)
        if hasattr(self, "pin_defaults"):
            raise ValueError("'pin_defaults' should not be set on a AddressHandler")

    def set_pins(self, pins: Collection[Pin]) -> None:
        """
        Called by the VirtualAddressMap to write out pin changes.

        If the underlying hardware required for the IO isn't open,
        open it.

        :param pins: is a collection of pins that should be made active. All other
            pins defined by the AddressHandler should be cleared.
        """
        raise NotImplementedError

    def close(self) -> None:
        """
        Optional close method to clean-up resources.

        This will be called automatically by the JigDriver for any
        address handlers passed into the JigDriver when it as created.
        """
        pass


class PinValueAddressHandler(AddressHandler):
    """Maps pins to bit values then combines the bit values for an update"""

    def __init__(self, pins: Sequence[Pin]) -> None:
        super().__init__(pins)
        self._pin_lookup = {
            pin: bit for pin, bit in zip(self.pin_list, _bit_generator())
        }

    def set_pins(self, pins: Collection[Pin]) -> None:
        value = sum(self._pin_lookup[pin] for pin in pins)
        self._update_output(value)

    def _update_output(self, value: int) -> None:
        bits = len(self.pin_list)
        print(f"0b{value:0{bits}b}")


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
                # Note that we might send an empty set here. We need to do that
                # so if there are pins to clear, they get cleared. This might
                # end up in redundant handler updates, but unless we track active_pins
                # per-handler I don't think we can avoid that.
                handler.set_pins(pin_set & self._active_pins)

    def active_pins(self) -> frozenset[Pin]:
        return frozenset(self._active_pins)

    def reset(self) -> None:
        """
        Sets all pins to be inactive.

        Note: this does not change the state of any VirtualMux's, so it is
        possible the state of each VirtualMux and its related pins will not
        be in sync.
        """
        self._dispatch_pin_state(PinSetState(off=self._all_pins))

    def update_input(self) -> None:
        """
        Currently not implemented. A few jigs implement digital input, but not many. It is the intention
        to implement this eventually, but for now, the old jig_mapping.py version can be used.
        """
        raise NotImplementedError


class MuxGroup:
    """
    Group multiple VirtualMux's, for use in a single Jig Driver.

    If a test script, it is expected that MuxGroup will be subclassed, with attributes
    being each required VirtualMux subclass. This can be done using a dataclass::

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
        # keep a reference to handlers so that we can close them if required.
        self._handlers = handlers
        self.virtual_map = VirtualAddressMap(handlers)

        self.mux = mux_group_factory()
        for mux in self.mux.get_multiplexers():
            # Perhaps we should instantiate the virtual mux here
            # and pass in the virtual_map.add_update. But we'd have to do some
            # magic in the MuxGroup call to pass add_update to each VirtualMux
            # constructor, and I was hoping to just use a dataclass...
            mux._update_pins = self.virtual_map.add_update

        self._validate()

    def close(self) -> None:
        for handler in self._handlers:
            handler.close()

    def active_pins(self) -> frozenset[Pin]:
        return self.virtual_map.active_pins()

    def debug_set_pin(self, pin: Pin, value: bool) -> None:
        # pin is a str, which is iterable... so we can't just throw it into
        # frozen set, or we end up with frozenset deconstructing it! so
        # wrap it into another single element list first
        if value:
            update = PinSetState(on=frozenset([pin]))
        else:
            update = PinSetState(off=frozenset([pin]))
        self.virtual_map.add_update(PinUpdate(final=update))

    def debug_set_pins(
        self, on: Collection[Pin] = frozenset(), off: Collection[Pin] = frozenset()
    ) -> None:
        update = PinSetState(on=frozenset(on), off=frozenset(off))
        self.virtual_map.add_update(PinUpdate(final=update))

    def all_mux_signals(self) -> tuple[tuple[VirtualMux, tuple[Signal, ...]], ...]:
        return tuple(((mux, mux.all_signals()) for mux in self.mux.get_multiplexers()))

    def reset(self) -> None:
        """
        Reset all VirtualMux's to the default signal "" (all pins off)
        """
        self.mux.reset()

    def _validate(self) -> None:
        """
        Do some basic sanity checks on the jig definition.

        - Ensure all pins that are used in muxes are defined by
          some address handler.

        Note: It is O.K. for there to be AddressHandler pins that
            are not used anywhere. Eventually we might choose to
            warn about them. This it is necessary to define some jigs.
        """
        all_handler_pins: set[Pin] = reduce(
            or_, (set(handler.pin_list) for handler in self._handlers), set()
        )
        mux_missing_pins = []

        for mux in self.mux.get_multiplexers():
            if unknown_pins := mux.pins() - all_handler_pins:
                mux_missing_pins.append((mux, unknown_pins))

        if mux_missing_pins:
            raise ValueError(
                f"One or more VirtualMux uses unknown pins:\n{mux_missing_pins}"
            )


_T = TypeVar("_T")


def _generate_bit_sets(bits: Sequence[_T]) -> Generator[set[_T], None, None]:
    """
    Create subsets of bits, representing bits of a list of integers

    This is easier to explain with an example
    list(generate_bit_set(["x0", "x1"])) -> [set(), {'x0'}, {'x1'}, {'x0', 'x1'}]
    """
    int_list = range(1 << len(bits)) if len(bits) != 0 else range(0)
    return (
        {bit for i, bit in enumerate(bits) if (1 << i) & index} for index in int_list
    )


def _bit_generator() -> Generator[int, None, None]:
    """b1, b10, b100, b1000, ..."""
    return (1 << counter for counter in itertools.count())


def generate_pin_group(
    group_designator: int, *, pin_count: int = 16, prefix: str = "", sep: str = ""
) -> tuple[Pin, ...]:
    """
    A helper to create pin names groups of pins, especially relay matrices.

    By default, returns 16 pin names, suitable for a 16 relay matrix.
    Changing the default values for pin_count and prefix can be used to generate
    alternate naming schemes.

    generate_pin_group(1) -> ("1K1", "1K2", "1K3", ..., "1K16")
    generate_pin_group(3, prefix="RM") -> ("RM1K1", "RM1K2", "RM1K3", ..., "RM1K16")
    generate_pin_group(5, pin_count=8, prefix="U") -> ("U3K1", "U3K2, "U3K3", ..., "U3K8")
    """
    return tuple(
        f"{prefix}{group_designator}{sep}K{relay}" for relay in range(1, pin_count + 1)
    )


def generate_relay_matrix_pin_list(
    designators: Iterable[int], *, prefix: str = "", sep: str = ""
) -> tuple[Pin, ...]:
    """
    Create a pin list for multiple relay matrix modules.

    Each module is allocated 16 pins. For example::

        generate_relay_matrix_pin_list([1,2,3]) ->
            ("1K1", "1K2", ..., "1K16", "2K1", ..., "2K16", "3K1", ..., "3K16")

    You can add a prefix. For example, we ofter use 'RM' for Relay Matrix::

        generate_relay_matrix_pin_list([2,3,1], prefix="RM") ->
            ("RM2K1", "RM2K2", ..., "RM2K16", "RM3K1", ..., "RM3K16", "RM1K1", ..., "RM1K16")

    Combination generate_relay_matrix_pin_list and generate_pin_group to create pins
    as needed for a specific jig configuration.
    """
    return tuple(
        itertools.chain.from_iterable(
            generate_pin_group(rm_number, prefix=prefix, sep=sep)
            for rm_number in designators
        )
    )
