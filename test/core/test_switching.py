from fixate.core.switching import (
    generate_bit_sets,
    VirtualMux,
    bit_generator,
    PinSetState,
    PinUpdate,
    VirtualSwitch,
)

import pytest

################################################################
# generate_bit_sets


def test_generate_bit_sets_empty():
    assert list(generate_bit_sets([])) == []


def test_generate_bit_sets_one_bit():
    assert list(generate_bit_sets(["b0"])) == [set(), {"b0"}]


def test_generate_bit_sets_multiple_bits():
    expected = [
        set(),
        {"b0"},
        {"b1"},
        {"b1", "b0"},
        {"b2"},
        {"b2", "b0"},
        {"b2", "b1"},
        {"b2", "b1", "b0"},
    ]
    assert list(generate_bit_sets(["b0", "b1", "b2"])) == expected


def test_bit_generator():
    """b1, b10, b100, b1000, ..."""
    bit_gen = bit_generator()

    actual = [next(bit_gen) for _ in range(8)]
    expected = [1, 2, 4, 8, 16, 32, 64, 128]
    assert actual == expected


################################################################
# virtual mux definitions


def test_VirtualMux_simple_tree_map():
    class SimpleVirtualMux(VirtualMux):
        pin_list = ["b0"]
        map_tree = ["sig0", "sig1"]

    mux = SimpleVirtualMux()
    # the empty signal "" get automatically added
    assert mux._signal_map == {"": set(), "sig0": set(), "sig1": {"b0"}}


def test_VirtualMux_larger_tree_map():
    class LargerVirtualMux(VirtualMux):
        pin_list = ["b0", "b1", "b2"]
        map_tree = ["sig0", "sig1", "sig2", "sig3", "sig4", "sig5", "sig6", "sig7"]

    mux = LargerVirtualMux()
    # the empty signal "" get automatically added
    assert mux._signal_map == {
        "": set(),
        "sig0": set(),
        "sig1": {"b0"},
        "sig2": {"b1"},
        "sig3": {"b1", "b0"},
        "sig4": {"b2"},
        "sig5": {"b2", "b0"},
        "sig6": {"b2", "b1"},
        "sig7": {"b2", "b1", "b0"},
    }


def test_VirtualMux_nested_tree_map():
    class NestedVirtualMux(VirtualMux):
        # Final mapping:
        # addr    signal
        # --------------
        # 0       a0
        # 1       a1_b0
        # 2       a2_b0
        # 3       a3
        # 5       a1_b1
        # 6       a2_b1_c0
        # 9       a1_b2
        # 10      a2_b2
        # 14      a2_b3
        # 22      a2_b1_c1
        pin_list = ("x0", "x1", "x2", "x3", "x4")

        mux_c = ("a2_b1_c0", "a2_b1_c1")
        mux_b1 = ("a1_b0", "a1_b1", "a1_b2", None)
        mux_b2 = ("a2_b0", mux_c, "a2_b2", "a2_b3")

        map_tree = ("a0", mux_b1, mux_b2, "a3")

    mux = NestedVirtualMux()
    # the empty signal "" get automatically added
    assert mux._signal_map == {
        "": set(),
        "a0": set(),
        "a1_b0": {"x0"},
        "a2_b0": {"x1"},
        "a3": {"x1", "x0"},
        "a1_b1": {"x0", "x2"},
        "a2_b1_c0": {"x1", "x2"},
        "a1_b2": {"x0", "x3"},
        "a2_b2": {"x1", "x3"},
        "a2_b3": {"x1", "x2", "x3"},
        "a2_b1_c1": {"x1", "x2", "x4"},
    }


# ###############################################################
# VirtualMux Behaviour


class MuxA(VirtualMux):
    """A mux definitioned used by a few scripts"""

    pin_list = ("a0", "a1")
    map_list = (("sig_a1", "a0", "a1"), ("sig_a2", "a1"))


def test_virtual_mux_basic():
    updates = []
    mux_a = MuxA(lambda x, y: updates.append((x, y)))

    # test both the __call__ and multiplex methods trigger
    # the appropriate update callback.
    mux_a("sig_a1")
    mux_a.multiplex("sig_a2", trigger_update=False)
    mux_a("")

    clear = PinSetState(off=frozenset({"a0", "a1"}))
    a1 = PinSetState(on=frozenset({"a0", "a1"}))
    a2 = PinSetState(on=frozenset({"a1"}), off=frozenset({"a0"}))
    assert updates == [
        (PinUpdate(PinSetState(), a1), True),
        (PinUpdate(PinSetState(), a2), False),
        (PinUpdate(PinSetState(), clear), True),
    ]


def test_virtual_mux_reset():
    """Check that reset sends an update that sets all pins off"""

    updates = []
    mux_a = MuxA(lambda x, y: updates.append((x, y)))
    mux_a.reset()
    assert updates == [
        (PinUpdate(PinSetState(), PinSetState(off=frozenset({"a1", "a0"}))), True),
    ]


def test_virtual_mux_invalid_signal():
    """Check an invalid signal raises an error."""

    mux_a = MuxA()
    with pytest.raises(ValueError):
        mux_a("invalid signal")


def test_invalid_signal_map_raises():
    """A virtual mux needs one of tree_map or list_map defined"""

    class BadMux(VirtualMux):
        pass

    with pytest.raises(ValueError):
        bm = BadMux()

# ###############################################################
# VirtualSwitch Behaviour


def test_virtual_switch():
    class Sw(VirtualSwitch):
        pin_name = "x"
    updates = []
    sw = Sw(lambda x, y: updates.append((x, y)))

    sw(True)
    sw(False)
    sw("TRUE", trigger_update=False)
    sw("FALSE")
    sw("")

    on = PinSetState(on=frozenset("x"))
    off = PinSetState(off=frozenset("x"))

    assert updates == [
        (PinUpdate(PinSetState(), on), True),
        (PinUpdate(PinSetState(), off), True),
        (PinUpdate(PinSetState(), on), False),
        (PinUpdate(PinSetState(), off), True),
        (PinUpdate(PinSetState(), off), True),
    ]



# ###############################################################
# Helper dataclasses


def test_pin_set_state_or():
    a = PinSetState(frozenset("ab"), frozenset("xy"))
    b = PinSetState(frozenset("cd"), frozenset("x"))
    assert a | b == PinSetState(frozenset("abcd"), frozenset("xy"))


def test_pin_update_or():
    a = PinUpdate(
        PinSetState(frozenset("a"), frozenset("b")),
        PinSetState(frozenset(), frozenset("yz")),
        1.0,
    )
    b = PinUpdate(
        PinSetState(frozenset("x"), frozenset()),
        PinSetState(frozenset("c"), frozenset("d")),
        2.0,
    )
    expected = PinUpdate(
        PinSetState(frozenset("ax"), frozenset("b")),
        PinSetState(frozenset("c"), frozenset("yzd")),
        2.0,
    )
    assert expected == a | b
