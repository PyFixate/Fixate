import unittest
from fixate.core.common import unit_scale, unit_convert, UNITS
from fixate.core.exceptions import InvalidScalarQuantityError


class TestUnitScale(unittest.TestCase):
    def test_milli_scale(self):
        self.assertAlmostEqual(unit_scale("10mV", ["V"]), 10e-3)

    def test_mega_scale(self):
        self.assertAlmostEqual(unit_scale("10MV", ["V"]), 10e6)

    def test_kilo_scale(self):
        self.assertAlmostEqual(unit_scale("10kV", ["V"]), 10e3)

    def test_micro_scale(self):
        self.assertAlmostEqual(unit_scale("10uV", ["V"]), 10e-6)

    def test_nano_scale(self):
        self.assertAlmostEqual(unit_scale("10nV", ["V"]), 10e-9)

    def test_pico_scale(self):
        self.assertAlmostEqual(unit_scale("10pV", ["V"]), 10e-12)

    def test_giga_scale(self):
        self.assertAlmostEqual(unit_scale("10GV", ["V"]), 10e9)

    def test_no_scale(self):
        self.assertEqual(unit_scale("10V", ["V"]), 10)

    def test_negative_value(self):
        self.assertAlmostEqual(unit_scale("-12mV", UNITS), -12e-3)

    def test_milli_scale_no_units(self):
        self.assertAlmostEqual(unit_scale("10m", ["V"]), 10e-3)

    def test_mega_scale_no_units(self):
        self.assertAlmostEqual(unit_scale("10M", ["V"]), 10e6)

    def test_kilo_scale_no_units(self):
        self.assertAlmostEqual(unit_scale("10k", ["V"]), 10e3)

    def test_micro_scale_no_units(self):
        self.assertAlmostEqual(unit_scale("10u", ["V"]), 10e-6)

    def test_nano_scale_no_units(self):
        self.assertAlmostEqual(unit_scale("10n", ["V"]), 10e-9)

    def test_pico_scale_no_units(self):
        self.assertAlmostEqual(unit_scale("10p", ["V"]), 10e-12)

    def test_giga_scale_no_units(self):
        self.assertAlmostEqual(unit_scale("10G", ["V"]), 10e9)

    def test_no_scale_no_units(self):
        self.assertEqual(unit_scale("10", ["V"]), 10e0)

    def test_negative_no_scale(self):
        self.assertAlmostEqual(unit_scale("-10V", UNITS), -10)

    def test_negative_no_units(self):
        self.assertAlmostEqual(unit_scale("-10m", UNITS), -10e-3)

    def test_space_before_units(self):
        self.assertAlmostEqual(unit_scale("-10 mHz", UNITS), -10e-3)

    def test_multiple_spaces_before_units(self):
        self.assertAlmostEqual(unit_scale("-10  mV", UNITS), -10e-3)

    def test_space_between_units(self):
        self.assertAlmostEqual(unit_scale("-10 k V", UNITS), -10e3)

    def test_leading_spaces(self):
        self.assertAlmostEqual(unit_scale(" -10 mV ", UNITS), -10e-3)

    def test_number_invalid_suffix(self):
        with self.assertRaises(InvalidScalarQuantityError):
            self.assertEqual(unit_scale("10 abcd", ["V"]), 10e0)

    def test_number_invalid_unit(self):
        with self.assertRaises(InvalidScalarQuantityError):
            self.assertEqual(unit_scale("10kHz", ["V"]), 10e3)

    def test_number_in_unit_set(self):
        self.assertEqual(unit_scale("10kHz", ["V", "Hz"]), 10e3)

    def test_invalid_string(self):
        with self.assertRaises(InvalidScalarQuantityError):
            self.assertEqual(unit_scale("blah 4 uAsd", ["V"]), 10e0)

    def test_none(self):
        self.assertEqual(unit_scale(None), None)


class TestUnitConvert(unittest.TestCase):
    """Use of unit_convert:  unit_convert(100e6, 1, 999)"""

    def test_no_scale(self):
        self.assertEqual(unit_convert(10.1, 1, 999), "10.1")

    def test_no_scale_int(self):
        self.assertEqual(unit_convert(10.9, 1, 999, as_int=True), "10")

    def test_round_down(self):
        self.assertEqual(unit_convert(10.83, 1, 999), "10.8")

    # NOTE: unpredictable behaviour with rounding of floats, i.e.:
    #   unit_convert(10.95, 1) = '10.9'
    #   unit_convert(10.05, 1) = '10.1'

    def test_milli_scale(self):
        self.assertEqual(unit_convert(10e-3, 1, 999), "10m")

    def test_mega_scale(self):
        self.assertEqual(unit_convert(10e6, 1, 999), "10M")

    def test_kilo_scale(self):
        self.assertEqual(unit_convert(10e3, 1, 999), "10k")

    def test_micro_scale(self):
        self.assertEqual(unit_convert(10e-6, 1, 999), "10u")

    def test_nano_scale(self):
        self.assertEqual(unit_convert(10e-9, 1, 999), "10n")

    def test_pico_scale(self):
        self.assertEqual(unit_convert(10e-12, 1, 999), "10p")

    def test_giga_scale(self):
        self.assertEqual(unit_convert(10e9, 1, 999), "10G")

    def test_smaller_base(self):
        self.assertEqual(unit_convert(100e-6, 0.1, 99), "0.1m")

    def test_smaller_base2(self):
        self.assertEqual(unit_convert(19.8e-6, 0.01, 99), "0.0198m")

    def test_smaller_base3(self):
        self.assertEqual(unit_convert(9.8e-6, 0.001, 9), "0.0098m")

    def test_negative_value(self):
        self.assertEqual(unit_convert(-10e-3, 1, 999), "-10m")

    def test_out_of_range(self):
        """Change in future if exception raised instead"""
        self.assertEqual(unit_convert(10e12, 1, 999), "10000000000000.0")

    def test_none(self):
        with self.assertRaises(TypeError):
            unit_convert(None, None)

    def test_string_input_invalid(self):
        with self.assertRaises(TypeError):
            unit_convert("10", 1, 99)
