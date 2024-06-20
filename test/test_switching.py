from fixate._switching import (
    _generate_bit_sets,
    VirtualMux,
    _bit_generator,
    PinSetState,
    PinUpdate,
    VirtualSwitch,
    RelayMatrixMux,
    PinValueAddressHandler,
    generate_pin_group,
    generate_relay_matrix_pin_list,
    AddressHandler,
    VirtualAddressMap,
    MuxGroup,
    JigDriver,
)

import pytest

################################################################
# helper to generate data


def test_generate_bit_sets_empty():
    assert list(_generate_bit_sets([])) == []


def test_generate_bit_sets_one_bit():
    assert list(_generate_bit_sets(["b0"])) == [set(), {"b0"}]


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
    assert list(_generate_bit_sets(["b0", "b1", "b2"])) == expected


def test_bit_generator():
    """b1, b10, b100, b1000, ..."""
    bit_gen = _bit_generator()

    actual = [next(bit_gen) for _ in range(8)]
    expected = [1, 2, 4, 8, 16, 32, 64, 128]
    assert actual == expected


def test_generate_pin_group():
    assert list(generate_pin_group(3)) == (
        "3K1 3K2 3K3 3K4 3K5 3K6 3K7 3K8 3K9 3K10 3K11 3K12 3K13 3K14 3K15 3K16".split()
    )
    assert list(generate_pin_group(1, prefix="RM")) == (
        "RM1K1 RM1K2 RM1K3 RM1K4 RM1K5 RM1K6 RM1K7 RM1K8 RM1K9 RM1K10 RM1K11 RM1K12 RM1K13 RM1K14 RM1K15 RM1K16".split()
    )
    assert list(generate_pin_group(10, pin_count=8, prefix="U")) == (
        "U10K1 U10K2 U10K3 U10K4 U10K5 U10K6 U10K7 U10K8".split()
    )


# fmt:off
large_pin_list_example1 = [
    "RC1K1", "RC1K2", "RC1K3", "RC1K4", "RC1K5", "RC1K6", "RC1K7", "RC1K8","RC1K9", "RC1K10", "RC1K11", "RC1K12", "RC1K13", "RC1K14", "RC1K15", "RC1K16",
    "RC2K1", "RC2K2", "RC2K3", "RC2K4", "RC2K5", "RC2K6", "RC2K7", "RC2K8", "RC2K9", "RC2K10", "RC2K11", "RC2K12", "RC2K13", "RC2K14", "RC2K15", "RC2K16",
    "RA1K1", "RA1K2", "RA1K3", "RA1K4", "RA1K5", "RA1K6", "RA1K7", "RA1K8", "RA1K9", "RA1K10", "RA1K11", "RA1K12", "RA1K13", "RA1K14", "RA1K15", "RA1K16",
    "RA2K1", "RA2K2", "RA2K3", "RA2K4", "RA2K5", "RA2K6", "RA2K7", "RA2K8", "RA2K9", "RA2K10", "RA2K11", "RA2K12", "RA2K13", "RA2K14", "RA2K15", "RA2K16",
    "RA3K1", "RA3K2", "RA3K3", "RA3K4", "RA3K5", "RA3K6", "RA3K7", "RA3K8", "RA3K9", "RA3K10", "RA3K11", "RA3K12", "RA3K13", "RA3K14", "RA3K15", "RA3K16",
    "RP1K1", "RP1K2", "RP1K3", "RP1K4", "RP1K5", "RP1K6", "RP1K7", "RP1K8", "RP1K9", "RP1K10", "RP1K11", "RP1K12", "RP1K13", "RP1K14", "RP1K15", "RP1K16",
    "RP2K1", "RP2K2", "RP2K3", "RP2K4", "RP2K5", "RP2K6", "RP2K7", "RP2K8", "RP2K9", "RP2K10", "RP2K11", "RP2K12", "RP2K13", "RP2K14", "RP2K15", "RP2K16",
    "RH1K1", "RH1K2", "RH1K3", "RH1K4", "RH1K5", "RH1K6", "RH1K7", "RH1K8", "RH1K9", "RH1K10", "RH1K11", "RH1K12", "RH1K13", "RH1K14", "RH1K15", "RH1K16",
]

large_pin_list_example2 = [
        # RM19
        "RM19K1", "RM19K2", "RM19K3", "RM19K4", "RM19K5", "RM19K6", "RM19K7", "RM19K8",
        "RM19K9", "RM19K10", "RM19K11", "RM19K12", "RM19K13", "RM19K14", "RM19K15", "RM19K16",
        # RM18
        "RM18K1", "RM18K2", "RM18K3", "RM18K4", "RM18K5", "RM18K6", "RM18K7", "RM18K8",
        "RM18K9", "RM18K10", "RM18K11", "RM18K12", "RM18K13", "RM18K14", "RM18K15", "RM18K16",
        # RM17
        "RM17K1", "RM17K2", "RM17K3", "RM17K4", "RM17K5", "RM17K6", "RM17K7", "RM17K8",
        "RM17K9", "RM17K10", "RM17K11", "RM17K12", "RM17K13", "RM17K14", "RM17K15", "RM17K16",
        # RM16
        "RM16K1", "RM16K2", "RM16K3", "RM16K4", "RM16K5", "RM16K6", "RM16K7", "RM16K8",
        "RM16K9", "RM16K10", "RM16K11", "RM16K12", "RM16K13", "RM16K14", "RM16K15", "RM16K16",
        # RM15
        "RM15K1", "RM15K2", "RM15K3", "RM15K4", "RM15K5", "RM15K6", "RM15K7", "RM15K8",
        "RM15K9", "RM15K10", "RM15K11", "RM15K12", "RM15K13", "RM15K14", "RM15K15", "RM15K16",
        # RM14
        "RM14K1", "RM14K2", "RM14K3", "RM14K4", "RM14K5", "RM14K6", "RM14K7", "RM14K8",
        "RM14K9", "RM14K10", "RM14K11", "RM14K12", "RM14K13", "RM14K14", "RM14K15", "RM14K16",
        # RM13
        "RM13K1", "RM13K2", "RM13K3", "RM13K4", "RM13K5", "RM13K6", "RM13K7", "RM13K8",
        "RM13K9", "RM13K10", "RM13K11", "RM13K12", "RM13K13", "RM13K14", "RM13K15", "RM13K16",
        # RM10
        "RM10K1", "RM10K2", "RM10K3", "RM10K4", "RM10K5", "RM10K6", "RM10K7", "RM10K8",
        "RM10K9", "RM10K10", "RM10K11", "RM10K12", "RM10K13", "RM10K14", "RM10K15", "RM10K16",
        # RM11
        "RM11K1", "RM11K2", "RM11K3", "RM11K4", "RM11K5", "RM11K6", "RM11K7", "RM11K8",
        "RM11K9", "RM11K10", "RM11K11", "RM11K12", "RM11K13", "RM11K14", "RM11K15", "RM11K16",
        # RM12
        "RM12K1", "RM12K2", "RM12K3", "RM12K4", "RM12K5", "RM12K6", "RM12K7", "RM12K8",
        "RM12K9", "RM12K10", "RM12K11", "RM12K12", "RM12K13", "RM12K14", "RM12K15", "RM12K16",
        # RM1
        "RM1K1", "RM1K2", "RM1K3", "RM1K4", "RM1K5", "RM1K6", "RM1K7", "RM1K8",
        "RM1K9", "RM1K10", "RM1K11", "RM1K12", "RM1K13", "RM1K14", "RM1K15", "RM1K16",
        # RM2
        "RM2K1", "RM2K2", "RM2K3", "RM2K4", "RM2K5", "RM2K6", "RM2K7", "RM2K8",
        "RM2K9", "RM2K10", "RM2K11", "RM2K12", "RM2K13", "RM2K14", "RM2K15", "RM2K16",
        # RM3
        "RM3K1", "RM3K2", "RM3K3", "RM3K4", "RM3K5", "RM3K6", "RM3K7", "RM3K8",
        "RM3K9", "RM3K10", "RM3K11", "RM3K12", "RM3K13", "RM3K14", "RM3K15", "RM3K16",
        # RM4
        "RM4K1", "RM4K2", "RM4K3", "RM4K4", "RM4K5", "RM4K6", "RM4K7", "RM4K8",
        "RM4K9", "RM4K10", "RM4K11", "RM4K12", "RM4K13", "RM4K14", "RM4K15", "RM4K16",
        # RM5
        "RM5K1", "RM5K2", "RM5K3", "RM5K4", "RM5K5", "RM5K6", "RM5K7", "RM5K8",
        "RM5K9", "RM5K10", "RM5K11", "RM5K12", "RM5K13", "RM5K14", "RM5K15", "RM5K16",
        # RM6
        "RM6K1", "RM6K2", "RM6K3", "RM6K4", "RM6K5", "RM6K6", "RM6K7", "RM6K8",
        "RM6K9", "RM6K10", "RM6K11", "RM6K12", "RM6K13", "RM6K14", "RM6K15", "RM6K16",
        # RM7
        "RM7K1", "RM7K2", "RM7K3", "RM7K4", "RM7K5", "RM7K6", "RM7K7", "RM7K8",
        "RM7K9", "RM7K10", "RM7K11", "RM7K12", "RM7K13", "RM7K14", "RM7K15", "RM7K16",
        # RM8
        "RM8K1", "RM8K2", "RM8K3", "RM8K4", "RM8K5", "RM8K6", "RM8K7", "RM8K8",
        "RM8K9", "RM8K10", "RM8K11", "RM8K12", "RM8K13", "RM8K14", "RM8K15", "RM8K16",
        # RM9
        "RM9K1", "RM9K2", "RM9K3", "RM9K4", "RM9K5", "RM9K6", "RM9K7", "RM9K8",
        "RM9K9", "RM9K10", "RM9K11", "RM9K12", "RM9K13", "RM9K14", "RM9K15", "RM9K16",
        # U2
        "U2K1", "U2K3", "U2K4", "U2K5", "U2K6", "U2SC6", "U2SC7", "U2SC8",
]

large_pin_list_example3 = [
    "RM1_K1", "RM1_K2", "RM1_K3", "RM1_K4", "RM1_K5", "RM1_K6", "RM1_K7", "RM1_K8",
    "RM1_K9", "RM1_K10", "RM1_K11", "RM1_K12", "RM1_K13", "RM1_K14", "RM1_K15", "RM1_K16",
    "RM2_K1", "RM2_K2", "RM2_K3", "RM2_K4", "RM2_K5", "RM2_K6", "RM2_K7", "RM2_K8",
    "RM2_K9", "RM2_K10", "RM2_K11", "RM2_K12", "RM2_K13", "RM2_K14", "RM2_K15", "RM2_K16",
]
# fmt:on


def test_generate_relay_matrix_pin_list():
    pin_list = list(
        generate_relay_matrix_pin_list([1, 2], prefix="RC")
        + generate_relay_matrix_pin_list([1, 2, 3], prefix="RA")
        + generate_relay_matrix_pin_list([1, 2], prefix="RP")
        + generate_relay_matrix_pin_list([1], prefix="RH")
    )
    assert pin_list == large_pin_list_example1

    pin_list = list(
        generate_relay_matrix_pin_list(
            [19, 18, 17, 16, 15, 14, 13, 10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            prefix="RM",
        )
        + ("U2K1", "U2K3", "U2K4", "U2K5", "U2K6", "U2SC6", "U2SC7", "U2SC8")
    )
    assert pin_list == large_pin_list_example2

    pin_list = list(generate_relay_matrix_pin_list([1, 2], prefix="RM", sep="_"))
    assert pin_list == large_pin_list_example3

    assert "U5_K1 U5_K2 U5_K3".split() == list(
        generate_pin_group(5, pin_count=3, prefix="U", sep="_")
    )


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


def test_empty_signal_should_not_be_defined():
    class BadMux1(VirtualMux):
        pin_list = ["x"]
        map_list = [["", "x"]]

    class BadMux2(VirtualMux):
        pin_list = ["x"]
        # Even though this is the "correct" definition, it is still
        # not allowed
        map_list = [[""]]

    with pytest.raises(ValueError):
        BadMux1()

    with pytest.raises(ValueError):
        BadMux2()


def test_default_signal_on_mux_raises():
    class BadMux(VirtualMux):
        pin_list = ["x"]
        map_list = [["sig1", "x"]]
        default_signal = "sig1"

    with pytest.raises(ValueError):
        BadMux()


# ###############################################################
# VirtualMux Behaviour


class MuxA(VirtualMux):
    """A mux definition used by a few tests"""

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
    sw("On", trigger_update=False)
    sw("Off")
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
# RelayMatrixMux Behaviour


def test_relay_matrix_mux():
    class RMMux(RelayMatrixMux):
        pin_list = ("a", "b")
        map_list = (
            ("sig1", "a"),
            ("sig2", "b"),
        )

    sig1 = PinSetState(off=frozenset("b"), on=frozenset("a"))
    sig2 = PinSetState(off=frozenset("a"), on=frozenset("b"))
    off = PinSetState(off=frozenset("ab"))

    updates = []
    rm = RMMux(lambda x, y: updates.append((x, y)))
    rm("sig1")
    rm("sig2")

    # compared to the standard mux, the setup of the PinUpdate
    # sets all pins off. The standard mux does nothing for the
    # setup phase.
    assert updates == [
        (PinUpdate(off, sig1, 0.01), True),
        (PinUpdate(off, sig2, 0.01), True),
    ]


def test_relay_matrix_mux_no_signal_change():
    """If the new signal is as-per previous, don't open & close again"""

    class RMMux(RelayMatrixMux):
        pin_list = ("a", "b")
        map_list = (
            ("sig1", "a"),
            ("sig2", "b"),
        )

    sig1 = PinSetState(off=frozenset("b"), on=frozenset("a"))
    off = PinSetState(off=frozenset("ab"))

    updates = []
    rm = RMMux(lambda x, y: updates.append((x, y)))
    rm("sig1")
    rm("sig1")

    # we don't care about the first update, that just ensure the mux in
    # in the right initial state. Note that there is a bit of implementation
    # detail leaking here. We could also test that no pins a added to the
    # pin update. I will keep as is for now, but if we change the implementation
    # it is reasonable to update this test.
    assert len(updates) == 2
    assert updates[1] == (PinUpdate(sig1, sig1, 0.01), True)


# ###############################################################
# AddressHandler


def test_pin_default_on_address_handler_raise():
    class BadHandler(PinValueAddressHandler):
        pin_defaults = ("x",)

    with pytest.raises(ValueError):
        BadHandler(("x", "y"))


# ###############################################################
# VirtualAddressMap


class TestHandler(AddressHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.updates = []

    def set_pins(self, pins):
        self.updates.append(pins)


def HandlerXY():
    return TestHandler("xy")


def HandlerAB():
    return TestHandler("ab")


def test_virtual_address_map_init_no_active_pins():
    vam = VirtualAddressMap([HandlerAB()])
    assert vam.active_pins() == frozenset()


def test_virtual_address_map_single_handler():
    """
    Go through some basic address map operations with a single handler
    - set pins on, check it was sent to the handler
    - do a reset and check it was sent to the handler
    - ensure active_pins is as expected at each step
    """
    ab = HandlerAB()
    vam = VirtualAddressMap([ab])
    vam.add_update(PinUpdate(final=PinSetState(on=frozenset("ab"))))
    assert ab.updates[0] == frozenset("ab")
    assert vam.active_pins() == frozenset("ab")
    vam.reset()
    assert ab.updates[1] == frozenset()
    assert vam.active_pins() == frozenset()


def test_virtual_address_map_single_handler_delay_trigger():
    """
    Go through some basic address map operations with a single handler,
    but this time, we split the operation up into steps using
    trigger_update = False.
    """
    ab = HandlerAB()
    vam = VirtualAddressMap([ab])
    vam.add_update(
        PinUpdate(final=PinSetState(on=frozenset("a"))), trigger_update=False
    )
    assert len(ab.updates) == 0
    vam.add_update(PinUpdate(final=PinSetState(on=frozenset("b"))), trigger_update=True)
    assert len(ab.updates) == 1
    assert ab.updates[0] == frozenset("ab")


def test_virtual_address_map_setup_then_final():
    """
    Go through some basic address map operations with a single handler,
    but this time, we split the operation up into steps using
    trigger_update = False.
    """
    ab = HandlerAB()
    vam = VirtualAddressMap([ab])
    vam.add_update(
        PinUpdate(
            setup=PinSetState(on=frozenset("b")),
            final=PinSetState(on=frozenset("a")),  # note we are not turning b off here
        )
    )
    assert len(ab.updates) == 2
    assert ab.updates[0] == frozenset("b")
    assert ab.updates[1] == frozenset("ab")


def test_virtual_address_map_multiple_handlers():
    ab = HandlerAB()
    xy = HandlerXY()
    vam = VirtualAddressMap([ab, xy])
    vam.add_update(
        PinUpdate(
            setup=PinSetState(on=frozenset("b")),
            final=PinSetState(on=frozenset("ay")),
        ),
    )
    assert len(ab.updates) == 2
    assert len(xy.updates) == 2
    assert ab.updates[0] == frozenset("b")
    assert ab.updates[1] == frozenset("ab")
    assert xy.updates[0] == frozenset()
    assert xy.updates[1] == frozenset("y")

    vam.add_update(
        PinUpdate(
            final=PinSetState(off=frozenset("ay"), on=frozenset("x")),
        ),
    )
    assert len(ab.updates) == 3
    assert len(xy.updates) == 3
    assert ab.updates[2] == frozenset("b")
    assert xy.updates[2] == frozenset("x")


# ###############################################################
# Jig Driver


def test_jig_driver_with_unknown_pins():
    handler1 = AddressHandler(("x0",))
    handler2 = AddressHandler(("x2",))
    handler3 = AddressHandler(("x1",))

    class Mux(VirtualMux):
        pin_list = ("x0", "x1")  # "x1" isn't in either handler
        map_list = ("sig1", "x1")

    class Group(MuxGroup):
        def __init__(self):
            self.mux = Mux()

    # This is O.K., because all the pins are included
    JigDriver(Group, [handler1, handler2, handler3])

    with pytest.raises(ValueError):
        # This should raise, because no handler implements "x1"
        JigDriver(Group, [handler1, handler2])


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
