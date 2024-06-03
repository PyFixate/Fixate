
from dataclasses import dataclass, field
from fixate.core.switching import VirtualMux, JigDriver, MuxGroup, PinValueAddressHandler

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

class Handler(PinValueAddressHandler):
    pin_list = ("x0", "x1", "x2", "x3", "x4", "x5")
    


@dataclass
class JigMuxGroup(MuxGroup):
    mux_one: MuxOne = field(default_factory=MuxOne)
    mux_two: MuxTwo = field(default_factory=MuxTwo)

jig = JigDriver(JigMuxGroup, [Handler()])

