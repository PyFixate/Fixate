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


# VirtualMuxes can be created with type annotations to provide the signal map
from typing_extensions import Annotated
from typing import Literal, Union


# fmt: off
MuxOneSigDef = Union[
    Annotated[Literal["sig_a1"], "a0", "a2"], 
    Annotated[Literal["sig_a2"], "a1"],
]

MuxTwoSigDef = Union[
    Annotated[Literal["sig_b1"], "b0", "b2"], 
    Annotated[Literal["sig_b2"], "b1"],
]

SingleSingleDef = Annotated[Literal["sig_c1"], "c0"], 
# fmt: on

# VirtualMuxes can now be created with type annotations to provide the signal map
muxa = VirtualMux[MuxOneSigDef]()

muxa("sig_a1")
muxa("sig_a2")

# using the wrong signal name will be caught at runtime and by the type checker
try:
    muxa("unknown signal name")  # type: ignore[arg-type]
except ValueError as e:
    print(f"An Exception would have occurred: {e}")
else:
    raise ValueError("Should have raised an exception")

# alternatively, the mux definition can be passed in while subclassing


class SubClassed(VirtualMux[MuxTwoSigDef]):
    """A mux definition used by a few scripts"""

    def extra_method(self) -> None:
        print("Extra method")


muxb = SubClassed()
muxb.multiplex("sig_b1")
muxb.multiplex("sig_b2")

# # further generic types can be created by subclassing from VirtualMux using a TypeVar
# # compared to the above way of subclassing, this way lets you reuse the class

# from typing import TypeVar

# S = TypeVar("S", bound=str)
# class MyGenericMux(VirtualMux[S]):
#     ...
#     def extra_method(self) -> None:
#         print("Extra method")

# generic_mux = MyGenericMux[MuxOneSigDef]()
# generic_mux("sig_a2")
# generic_mux("sig_a1")

# # RelayMatrixMux is an example of this
# rmm = RelayMatrixMux[MuxOneSigDef]()
# rmm("sig_a1")
# rmm("sig_a2")
