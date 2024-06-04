"""
This file is just a test playground that shows how the update jig classes will
fit together.
"""
from dataclasses import dataclass, field
from fixate.core.switching import VirtualMux, JigDriver, MuxGroup, PinValueAddressHandler, VirtualSwitch


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

class MuxThree(VirtualMux):
    pin_list = ("x101", "x123")
    map_list = (("", "x101", "x123"),)

class Handler(PinValueAddressHandler):
    pin_list = ("x0", "x1", "x2", "x3", "x4", "x5")
    


# Problem!
# our existing scripts/jig driver, the name of the mux is the
# class of the virtual mux. This scheme below will not allow that
# to work.
# Assuming an existing script with a mux called NewVirtualMux
# 1. Update every reference in the script
#    dm.jig.mux.NewVirtualMux -> dm.jig.mux.new_virtual_mux
# 2. Change the class name, but keep the attribute name
#    @dataclass
#    class JigMuxGroup(MuxGroup):
#        NewVirtualMux: _NewVirtualMux
#    Then the references in the script stay this same.
#    jig.mux.NewVirtualMux
# 3. Change the attribute name on mux, like in the example below,
#    but add some compatibility code to MuxGroup base class so that
#    attribute lookups that match the Class of one of its attributes
#    get magically mapped to the correct attribute.
@dataclass
class JigMuxGroup(MuxGroup):
    mux_one: MuxOne = field(default_factory=MuxOne)
    mux_two: MuxTwo = field(default_factory=MuxTwo)
    mux_three: MuxThree = field(default_factory=MuxThree)

jig = JigDriver(JigMuxGroup, [Handler()])

jig.mux.mux_one("sig2", trigger_update=False)
jig.mux.mux_two("sig5")
