from fixate.core.common import TestClass
from fixate.core.checks import *


class CheckCoverage(TestClass):
    """Test containing all check types"""

    def test(self):
        chk_true(True, "It is True!")
        chk_passes(description="test abc description")
        chk_log_value(123, fmt=".2f")
        chk_in_range(10, 1, 100)
        chk_in_tolerance(10.1, 10, 2)
        chk_in_range_equal(13, 10, 15)
        chk_in_range_equal_min(12, 12, 15)
        chk_in_range_equal_max(1e3, 12, 1e3)
        chk_outside_range(1.1e3, 12, 1e3)
        chk_outside_range_equal(1e3, 12, 1e3)
        chk_outside_range_equal_min(12, 12, 1e3)
        chk_outside_range_equal_max(7e4, 12, 7e4)
        chk_smaller_or_equal(23, 23)
        chk_greater_or_equal(-1e2, -1e3)
        chk_smaller(123456, 123457)
        chk_greater(10, 9)
        chk_true(1 == 1)
        chk_false(1 < 1)
        chk_in_tolerance_equal(12345.6, 12300, 1)
        chk_in_deviation_equal(60, 50, 10)
        chk_equal(1e5, 1e5)


TEST_SEQUENCE = [CheckCoverage()]
