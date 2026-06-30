"""
This file is just a test playground that shows how the update jig classes will
fit together.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from fixate import (
    VirtualMux,
    JigDriver,
    MuxGroup,
    PinValueAddressHandler,
    VirtualSwitch,
    RelayMatrixMux,
)


class MuxOne(VirtualMux):
    pin_list = ("x0", "x1", "x2")
    map_list = (
        ("sig1", "x0"),
        ("sig2", "x1"),
        ("sig3", "x2"),
    )


class MuxTwo(VirtualMux):
    pin_list = ("x3", "x4", "x5")
    map_tree = (
        "sig4",
        "sig5",
        "sig6",
        (
            "sig7",
            "sig8",
        ),
    )


class MuxThree(VirtualSwitch):
    pin_name = "x101"


# Note!
# our existing scripts/jig driver, the name of the mux is the
# class of the virtual mux. This scheme below will not allow that
# to work. Instead, define an attribute name on the MuxGroup
@dataclass
class JigMuxGroup(MuxGroup):
    mux_one: MuxOne = field(default_factory=MuxOne)
    mux_two: MuxTwo = field(default_factory=MuxTwo)
    mux_three: MuxThree = field(default_factory=MuxThree)


jig = JigDriver(
    JigMuxGroup, [PinValueAddressHandler(("x0", "x1", "x2", "x3", "x4", "x5", "x101"))]
)

jig.mux.mux_one("sig2", trigger_update=False)
jig.mux.mux_two("sig5")
jig.mux.mux_three("On")
jig.mux.mux_three(False)


# VirtualMuxes can be made generic
from typing import Literal

# note: the type keyword can't be used inside functions!
# generally we want to use type to avoid confusion around the type system
# this makes it clear we are creating something for typehinting
# e.g type MyInt = int - won't work in functions
# variable = int - is not obvious what the intent is and can behave differently depending on its scope

# the type keyword can be used to create reusable definitions
# otherwise Literal can be used directly
type MyTypedMuxSignals = Literal["signal_1", "signal_2"]


def do_some_stuff():
    # otherwise the mux is created as normal
    class MyTypedMux(VirtualMux[MyTypedMuxSignals]):
        pin_list = ("x0", "x1")
        map_list = (
            ("signal_1", "x0"),
            ("signal_2", "x1"),
        )

    mymux = MyTypedMux()

    # signal names will appear in the autocompletion options (including the empty signal "")
    mymux.multiplex("")
    mymux.multiplex("signal_1")
    mymux.multiplex("signal_2")

    # anything that isn't a signal will be flagged
    try:
        mymux.multiplex("not_a_signal")
    except ValueError as e:
        print(e)

    # the annotations can also be used directly with Literal
    class MyDirectlyTypedMux(VirtualMux[Literal["Sig_1", "Sig_2"]]):
        pin_list = ("x0", "x1")
        # Note neither definition currently point out the incorrect signal mapping below!
        # it is still up to the user to set up muxes correctly
        map_list = (
            ("signal_1", "x0"),
            ("signal_2", "x1"),
        )

    # suggestions will work as normal
    myothermux = MyDirectlyTypedMux()

    myothermux.multiplex("")
    myothermux.multiplex("Sig_1")
    myothermux.multiplex("Sig_2")

    try:
        myothermux.multiplex("not_a_signal")
    except ValueError as e:
        print(e)

    # general subclasses and RelayMatrixMux also work with this
    # currently VirtualSwitch doesn't, it creates its own signal names doesn't really benefit from this
    class MyTypedRelay(RelayMatrixMux[MyTypedMuxSignals]):
        pin_list = ("x3", "x4")
        map_list = (
            ("signal_1", "x3"),
            ("signal_2", "x4"),
        )

    myrelay = MyTypedRelay()
    myrelay.multiplex("")
    myrelay.multiplex("signal_1")
    myrelay.multiplex("signal_2")


do_some_stuff()
