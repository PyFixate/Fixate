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


from typing_extensions import Annotated

from typing import Literal, Union

# maybe we can create aliases to make it easier to understand how to create a MuxDef
SignalName = Literal
SignalName.__repr__ = lambda self: f"SignalName"
Signal = Annotated
Signal.__repr__ = lambda self: f"Signal{self.__args__}"
MuxDef = Union

# fmt off
MuxOneSigDef = MuxDef[
    Signal[SignalName["sig_a1"], "a0", "a2"], Signal[SignalName["sig_a2"], "a1"]
]


class MuxA(VirtualMux[MuxOneSigDef]):
    """A mux definition used by a few scripts"""


muxa = MuxA(update_pins=print)

muxa("sig_a2")
muxa("sig_a1")

muxb = VirtualMux[MuxOneSigDef](update_pins=print)

muxb.multiplex("sig_a2")
muxb.multiplex("sig_a1")
try:
    muxb.multiplex("1")
except ValueError:
    ...
else:
    raise ValueError("muxb.multiplex('1') should have raised a ValueError")

# an example of generic subclasses of VirtualMux
rmm = RelayMatrixMux[MuxOneSigDef]()

rmm("sig_a1")

try:
    rmm("sig")
except ValueError:
    ...
else:
    raise ValueError("rmm('sig') should have raised a ValueError")
