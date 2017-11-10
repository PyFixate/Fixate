import unittest
from fixate.core.common import unit_scale
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

    def test_giga_scale(self):
        self.assertAlmostEqual(unit_scale("10GV", ["V"]), 10e9)

    def test_no_scale(self):
        self.assertEqual(unit_scale("10V", ["V"]), 10)

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

    def test_giga_scale_no_units(self):
        self.assertAlmostEqual(unit_scale("10G", ["V"]), 10e9)

    def test_no_scale_no_units(self):
        self.assertEqual(unit_scale("10", ["V"]), 10e0)

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
