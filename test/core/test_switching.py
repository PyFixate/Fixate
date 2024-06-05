from fixate.core.switching import (
    generate_bit_sets,
    VirtualMux,
    bit_generator,
    PinSetState,
    PinUpdate,
    _pins_for_one_relay_matrix,
)


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


################################################################
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
