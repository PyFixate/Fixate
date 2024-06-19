"""
This file is just a test playground that shows how the update jig classes will
fit together.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from fixate.core._switching import VirtualMux, JigDriver, MuxGroup, PinValueAddressHandler, VirtualSwitch, Signal, Pin

from typing import TypeVar, Generic, Union, Annotated, Literal

S = TypeVar("S")


class VirtualMux(Generic[S]):
    def __init__(self):
        self._signal_map: dict[Signal, set[Pin]] = {}

    def __call__(self, signal: S, trigger_update: bool = False) -> None:
        self.multiplex(signal, trigger_update)

    def multiplex(self, signal: S, trigger_update: bool = False) -> None:
        print(self._signal_map[signal])


MuxOneSigDef = Union[
    Annotated[Literal["sig1"], ("x0",)],
    Annotated[Literal["sig2"], ("x1",)],
    Annotated[Literal["sig3"], ("x0", "x1")],
]

class MuxOne(VirtualMux[MuxOneSigDef]):
    pass

@dataclass
class JigMuxGroup(MuxGroup):
    mux_one: MuxOne = field(default_factory=MuxOne)


class MuxOne(VirtualMux[MuxOneSigDef]):
    pass


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


class Handler(PinValueAddressHandler):
    pin_list = ("x0", "x1", "x2", "x3", "x4", "x5", "x101")


# Note!
# our existing scripts/jig driver, the name of the mux is the
# class of the virtual mux. This scheme below will not allow that
# to work. Instead, define an attribute name on the MuxGroup
@dataclass
class JigMuxGroup(MuxGroup):
    mux_one: MuxOne = field(default_factory=MuxOne)
    mux_two: MuxTwo = field(default_factory=MuxTwo)
    mux_three: MuxThree = field(default_factory=MuxThree)


jig = JigDriver(JigMuxGroup, [Handler()])

jig.mux.mux_one("sig2", trigger_update=False)
jig.mux.mux_two("sig5")
jig.mux.mux_three("On")
jig.mux.mux_three(False)
