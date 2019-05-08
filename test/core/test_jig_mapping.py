import time
import pytest
from unittest import TestCase
from unittest.mock import MagicMock

from fixate.core.jig_mapping import (
    VirtualAddressMap,
    AddressHandler,
    VirtualMux,
    JigDriver,
    MuxWarning,
)

try:
    # This try/except is temporary while moving tests to pytest. running
    # python -m unittest vs pytest ends up with different python path. In
    # time we will most likely move to using only pytest and when that happens
    # the except clause below can be removed.
    from . import map_data
except ImportError:
    import map_data


class TestVirtualAddressMap(TestCase):
    """

    """

    def setUp(self):
        self.v_map = VirtualAddressMap()

    def test_install_address_handler_valid(self):
        address_handler = MagicMock()
        address_handler.pin_list = ["1", "2", "3", "4"]
        self.v_map.install_address_handler(address_handler)

        self.assertEqual(self.v_map.address_handlers, [(4, address_handler)])
        self.assertEqual(self.v_map.virtual_pin_list, ["1", "2", "3", "4"])

        address_handler2 = MagicMock()
        address_handler2.pin_list = ["5", "6", "7", "8"]

        self.v_map.install_address_handler(address_handler2)

        self.assertEqual(
            self.v_map.address_handlers, [(4, address_handler), (8, address_handler2)]
        )
        self.assertEqual(
            self.v_map.virtual_pin_list, ["1", "2", "3", "4", "5", "6", "7", "8"]
        )

    def test_install_address_handler_invalid(self):
        address_handler = MagicMock()
        address_handler.pin_list = ["1", "2", "3", "4"]
        self.v_map.install_address_handler(address_handler)

        self.assertEqual(self.v_map.address_handlers, [(4, address_handler)])
        self.assertEqual(self.v_map.virtual_pin_list, ["1", "2", "3", "4"])

        address_handler2 = MagicMock()
        address_handler2.pin_list = ["4", "5", "6", "7"]

        # Duplicate pin identifier pin 4 should raise error
        self.assertRaises(
            ValueError, self.v_map.install_address_handler, address_handler2
        )

        # If the error occurs it should not map those pins
        self.assertEqual(self.v_map.address_handlers, [(4, address_handler)])
        self.assertEqual(self.v_map.virtual_pin_list, ["1", "2", "3", "4"])

    def test_install_multiplexer_valid(self):
        # Setup pin list
        self.v_map.virtual_pin_list = ["1", "2", "3", "4", "5", "6", "7", "8"]
        virtual_mux = MagicMock()
        virtual_mux.pin_list = ["2", "5", "7", "8"]
        self.v_map.install_multiplexer(virtual_mux)

        self.assertEqual(virtual_mux.pin_mask, [1, 4, 6, 7])
        self.assertEqual(virtual_mux.update_callback, self.v_map.update_pin_values)

        virtual_mux2 = MagicMock()
        virtual_mux2.pin_list = ["1", "3", "4"]
        self.v_map.install_multiplexer(virtual_mux2)
        self.assertEqual(virtual_mux2.pin_mask, [0, 2, 3])
        self.assertEqual(virtual_mux2.update_callback, self.v_map.update_pin_values)

    def test_update_defaults(self):
        address_handler = MagicMock()
        address_handler2 = MagicMock()

        self.v_map.install_address_handler(address_handler)
        self.v_map.install_address_handler(address_handler2)

        self.v_map.update_defaults()
        address_handler.defaults.assert_called_with()
        address_handler2.defaults.assert_called_with()

    def test_update_output(self):
        address_handler = MagicMock()
        address_handler2 = MagicMock()
        address_handler3 = MagicMock()
        address_handler.pin_list = ["0", "1", "2", "3", "4", "5", "6", "7"]
        address_handler2.pin_list = ["8", "9", "10", "11", "12", "13", "14", "15"]
        address_handler3.pin_list = ["16", "17", "18", "19", "20", "21", "22", "23"]
        self.v_map.install_address_handler(address_handler)
        self.v_map.install_address_handler(address_handler2)
        self.v_map.install_address_handler(address_handler3)

        self.v_map.update_output()
        address_handler.update_output.assert_called_with(0)
        address_handler2.update_output.assert_called_with(0)
        address_handler3.update_output.assert_called_with(0)

        self.v_map._virtual_pin_values = 0xFFFFFF
        self.v_map.update_output()
        address_handler.update_output.assert_called_with(0xFF)
        address_handler2.update_output.assert_called_with(0xFF)
        address_handler3.update_output.assert_called_with(0xFF)

        self.v_map._virtual_pin_values = 0xAABBCC
        self.v_map.update_output()
        address_handler.update_output.assert_called_with(0xCC)
        address_handler2.update_output.assert_called_with(0xBB)
        address_handler3.update_output.assert_called_with(0xAA)

    def test_update_input(self):
        address_handler = MagicMock()
        address_handler2 = MagicMock()
        address_handler3 = MagicMock()
        address_handler.pin_list = ["0", "1", "2", "3", "4", "5", "6", "7"]
        address_handler2.pin_list = ["8", "9", "10", "11", "12", "13", "14", "15"]
        address_handler3.pin_list = ["16", "17", "18", "19", "20", "21", "22", "23"]
        self.v_map.install_address_handler(address_handler)
        self.v_map.install_address_handler(address_handler2)
        self.v_map.install_address_handler(address_handler3)

        address_handler.update_input.return_value = 0xAA
        address_handler2.update_input.return_value = 0xBB
        address_handler3.update_input.return_value = 0xCC

        self.v_map.update_input()
        address_handler.update_input.assert_called_with()
        address_handler2.update_input.assert_called_with()
        address_handler3.update_input.assert_called_with()
        self.assertEqual(self.v_map._virtual_pin_values, 0xCCBBAA)

    def test_update_pin_values(self):
        self.v_map.update_output = MagicMock()
        self.assertEqual(self.v_map._virtual_pin_values, 0)
        self.v_map.update_pin_values([(0, 1), (5, 1)], trigger_update=False)
        self.assertEqual(self.v_map._virtual_pin_values, 0b100001)
        self.assertRaises(
            AssertionError, self.v_map.update_output.assert_called_once_with
        )
        self.v_map.update_pin_values(([(1, 1), (0, 0), (6, 1)]))
        self.assertEqual(self.v_map._virtual_pin_values, 0b1100010)
        self.v_map.update_output.assert_called_once_with()

    def test_get_pin_values(self):
        self.v_map.update_output = MagicMock()
        self.v_map._virtual_pin_values_active = 0b10110100
        self.v_map.virtual_pin_list = ["0", "1", "2", "3", "4", "5", "6", "7"]
        self.assertEqual(
            self.v_map.pin_values,
            [
                ("0", 0),
                ("1", 0),
                ("2", 1),
                ("3", 0),
                ("4", 1),
                ("5", 1),
                ("6", 0),
                ("7", 1),
            ],
        )

    def test_pin_on_duplicate_mux(self):
        with pytest.warns(MuxWarning):
            # Setup pin list
            self.v_map.virtual_pin_list = ["1", "2", "3", "4", "5", "6", "7", "8"]
            virtual_mux = MagicMock()
            virtual_mux.pin_list = ["2", "5", "7", "8"]
            self.v_map.install_multiplexer(virtual_mux)

            virtual_mux2 = MagicMock()
            virtual_mux2.pin_list = ["1", "3", "4", "8"]
            self.v_map.install_multiplexer(virtual_mux2)


class TestAddressHandler(TestCase):
    """

    """

    def setUp(self):
        self.address_handler = MagicMock(spec=AddressHandler)

    def test_address_handler_attributes(self):
        self.address_handler.update_output()
        self.address_handler.update_input()
        self.address_handler.defaults()
        self.address_handler.pin_list


class MockedMux(VirtualMux):
    pass


class TestVirtualMux(TestCase):
    """

    """

    def setUp(self):
        MockedMux.pin_list = ["{}".format(x) for x in range(16)]
        MockedMux.map_signals = MagicMock()
        self.virtual_mux = MockedMux()
        self.virtual_mux.update_callback = MagicMock()

    def test_defaults(self):
        virtual_mux = VirtualMux()
        self.assertEqual(virtual_mux.pin_list, [])
        self.assertEqual(virtual_mux.condensed_signal_map(), [])
        self.assertEqual(virtual_mux.signal_map, {})
        # Check that map signals is called on initialisation
        self.virtual_mux.map_signals.assert_called_with()

    def test_condensed_signal_mapping(self):
        self.assertEqual(self.virtual_mux.signal_map, {})
        self.assertEqual(self.virtual_mux.condensed_signal_map(), [])
        self.virtual_mux.signal_map["VirtualPin"] = 5
        self.assertEqual(
            self.virtual_mux.condensed_signal_map(),
            [("0b0000000000000101", "VirtualPin")],
        )
        # self.virtual_mux.signal_map[5] = None
        self.virtual_mux.signal_map["VirtualPin2"] = 0xFF
        self.assertEqual(
            self.virtual_mux.condensed_signal_map(),
            [
                ("0b0000000000000101", "VirtualPin"),
                ("0b0000000011111111", "VirtualPin2"),
            ],
        )
        del self.virtual_mux.signal_map["VirtualPin"]
        self.assertEqual(
            self.virtual_mux.condensed_signal_map(),
            [("0b0000000011111111", "VirtualPin2")],
        )
        del self.virtual_mux.signal_map["VirtualPin2"]
        self.assertEqual(self.virtual_mux.condensed_signal_map(), [])

    def test_map_shifted_zeroes(self):
        self.virtual_mux.map_shifted(
            0,
            0,
            [
                None,
                "SUPP_CT_CURRENT_IN_SPARE_8",
                "SPARE5",
                None,
                "SPARE7",
                "SUPP_100VAC_POS",
            ],
        )
        self.assertEqual(self.virtual_mux.signal_map["SUPP_CT_CURRENT_IN_SPARE_8"], 1)
        self.assertEqual(self.virtual_mux.signal_map["SPARE5"], 2)
        self.assertEqual(self.virtual_mux.signal_map["SPARE7"], 4)
        self.assertEqual(self.virtual_mux.signal_map["SUPP_100VAC_POS"], 5)

    def test_map_shifted_base(self):
        self.virtual_mux.map_shifted(
            3,
            0,
            [
                None,
                "SUPP_CT_CURRENT_IN_SPARE_8",
                "SPARE5",
                None,
                "SPARE7",
                "SUPP_100VAC_POS",
            ],
        )
        self.assertEqual(self.virtual_mux.signal_map["SUPP_CT_CURRENT_IN_SPARE_8"], 4)
        self.assertEqual(self.virtual_mux.signal_map["SPARE5"], 5)
        self.assertEqual(self.virtual_mux.signal_map["SPARE7"], 7)
        self.assertEqual(self.virtual_mux.signal_map["SUPP_100VAC_POS"], 8)

    def test_map_shifted_start_index(self):
        self.virtual_mux.map_shifted(
            0,
            3,
            [
                None,
                "SUPP_CT_CURRENT_IN_SPARE_8",
                "SPARE5",
                None,
                "SPARE7",
                "SUPP_100VAC_POS",
            ],
        )

        self.assertEqual(
            self.virtual_mux.signal_map["SUPP_CT_CURRENT_IN_SPARE_8"], 1 << 3
        )
        self.assertEqual(self.virtual_mux.signal_map["SPARE5"], 1 << 4)
        self.assertEqual(self.virtual_mux.signal_map["SPARE7"], 1 << 5)
        self.assertEqual(
            self.virtual_mux.signal_map["SUPP_100VAC_POS"], 1 << 5 | 1 << 3
        )

    def test_map_shifted_base_shift(self):
        self.virtual_mux.map_shifted(
            20,
            3,
            [
                None,
                "SUPP_CT_CURRENT_IN_SPARE_8",
                "SPARE5",
                None,
                "SPARE7",
                "SUPP_100VAC_POS",
            ],
        )

        self.assertEqual(
            self.virtual_mux.signal_map["SUPP_CT_CURRENT_IN_SPARE_8"], (1 << 3) + 20
        )
        self.assertEqual(self.virtual_mux.signal_map["SPARE5"], (1 << 4) + 20)
        self.assertEqual(self.virtual_mux.signal_map["SPARE7"], (1 << 5) + 20)
        self.assertEqual(
            self.virtual_mux.signal_map["SUPP_100VAC_POS"], (1 << 5 | 1 << 3) + 20
        )

    def test_multiplex(self):
        self.virtual_mux.map_shifted(
            20,
            3,
            [
                None,
                "SUPP_CT_CURRENT_IN_SPARE_8",
                "SPARE5",
                None,
                "SPARE7",
                "SUPP_100VAC_POS",
            ],
        )
        self.virtual_mux.pin_mask = [
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
        ]
        self.virtual_mux.multiplex("SPARE5")  # 0b0000000000100100
        self.virtual_mux.update_callback.assert_called_with(
            [
                (0, False),
                (1, False),
                (2, True),
                (3, False),
                (4, False),
                (5, True),
                (6, False),
                (7, False),
                (8, False),
                (9, False),
                (10, False),
                (11, False),
                (12, False),
                (13, False),
                (14, False),
                (15, False),
            ],
            True,
        )
        self.virtual_mux.multiplex("SUPP_100VAC_POS")  # 0b0000000000111100
        self.virtual_mux.update_callback.assert_called_with(
            [
                (0, False),
                (1, False),
                (2, True),
                (3, True),
                (4, True),
                (5, True),
                (6, False),
                (7, False),
                (8, False),
                (9, False),
                (10, False),
                (11, False),
                (12, False),
                (13, False),
                (14, False),
                (15, False),
            ],
            True,
        )

    def test_multiplex_reversed_pin_mask(self):
        self.virtual_mux.map_shifted(
            20,
            3,
            [
                None,
                "SUPP_CT_CURRENT_IN_SPARE_8",
                "SPARE5",
                None,
                "SPARE7",
                "SUPP_100VAC_POS",
            ],
        )
        self.virtual_mux.pin_mask = [
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
        ]
        self.virtual_mux.pin_mask.reverse()

        self.virtual_mux.multiplex("SPARE5")  # 0b0000000000100100
        self.virtual_mux.update_callback.assert_called_with(
            [
                (15, False),
                (14, False),
                (13, True),
                (12, False),
                (11, False),
                (10, True),
                (9, False),
                (8, False),
                (7, False),
                (6, False),
                (5, False),
                (4, False),
                (3, False),
                (2, False),
                (1, False),
                (0, False),
            ],
            True,
        )


class TestVirtualMuxSignalTreeMap(TestCase):
    def test_multiplex_elv_dmm_mux(self):
        mux = map_data.MuxDmmInputHi()
        self.assertEqual(mux.condensed_signal_map(), map_data.MuxDmmInputHi_signal_map)

    def test_multiplex_elv_dmm_mux_tree(self):
        mux = map_data.MuxDmmInputHi_treedef()
        self.assertEqual(mux.condensed_signal_map(), map_data.MuxDmmInputHi_signal_map)

    def test_multiplex_elv_dmm_mux_tree_compact(self):
        mux = map_data.MuxDmmInputHi_treedef_compact()
        self.assertEqual(mux.condensed_signal_map(), map_data.MuxDmmInputHi_signal_map)


class TestVirtualMuxSignalListMap(TestCase):
    def test_multiplex_elv_led_mux(self):
        mux = map_data.MuxDisplayLEDs()
        self.assertEqual(mux.condensed_signal_map(), map_data.MuxDisplayLEDs_signal_map)

    def test_multiplex_elv_led_mux_tree(self):
        mux = map_data.MuxDisplayLEDs_listdef()
        self.assertEqual(mux.condensed_signal_map(), map_data.MuxDisplayLEDs_signal_map)


class TestDuplicateSignalNames(TestCase):
    def test_map_single(self):
        mux = map_data.TestMultipleDefsFails()
        self.assertRaisesRegex(
            ValueError, "Test3 is a duplicate of Test1", mux.map_singles
        )

    def test_map_tree(self):
        mux = map_data.TestMultipleDefsFails()
        self.assertRaisesRegex(
            ValueError, "Test5 is a duplicate of Test4", mux.map_trees
        )

    def test_map_shifted(self):
        mux = map_data.TestMultipleDefsFails()
        self.assertRaisesRegex(
            ValueError, "Test5 is a duplicate of Test4", mux.map_shifteds
        )

    def test_map_combo(self):
        mux = map_data.TestMultipleDefsFails()
        self.assertRaisesRegex(
            ValueError, "Test5 is a duplicate of Test4", mux.map_combo
        )


class AddrHand(AddressHandler):
    pin_list = ["K{}".format(x) for x in range(1, 11)]

    def __init__(self, update_mock, **kwargs):
        super().__init__(**kwargs)
        self.update_mock = update_mock

    def update_output(self, value):
        self.update_mock.update_output(value, time.time())


class Mux1(VirtualMux):
    clearing_time = 0.2
    pin_list = ["K1", "K2", "K3"]
    map_list = [("1", "K1"), ("2", "K2"), ("3", "K3"), ("13", "K1", "K3")]

    def clear_callback(self):
        virtual_address = self.signal_map.get(self.default_signal, 0b0)
        values = self._build_values_update(virtual_address)
        self._clear_callback(values, self.clearing_time)


class Mux2(VirtualMux):
    pin_list = ["K4", "K5", "K6"]
    map_list = [("4", "K4"), ("5", "K5"), ("6", "K6"), ("46", "K4", "K6")]


class Mux3(VirtualMux):
    clearing_time = 0.5
    pin_list = ["K7", "K8", "K9"]
    map_list = [("7", "K7"), ("8", "K8"), ("9", "K9"), ("79", "K7", "K9")]

    def clear_callback(self):
        virtual_address = self.signal_map.get(self.default_signal, 0b0)
        values = self._build_values_update(virtual_address)
        self._clear_callback(values, self.clearing_time)


class MuxDuplicate(VirtualMux):
    pin_list = ["K7", "K8", "K9"]


class TestRelayMuxClearingTime(TestCase):
    start = time.time()

    def setUp(self):
        self.handler_mock = MagicMock()

        class TestJig(JigDriver):
            multiplexers = (Mux1(), Mux2(), Mux3())
            address_handlers = (AddrHand(self.handler_mock),)

        self.jig = TestJig()

    def test_duplicate_muxes(self):
        class TestJig(JigDriver):
            multiplexers = (Mux1(), Mux1(), Mux3())
            address_handlers = (AddrHand(self.handler_mock),)

        with pytest.warns(MuxWarning):
            TestJig()

    def test_no_update(self):
        self.jig.mux.Mux1("")
        self.jig.mux.Mux2("")
        self.jig.mux.Mux3("")
        self.assertEquals(None, self.handler_mock.update_output.assert_not_called())
