from fixate.core.common import TestClass
from fixate.core.ui import user_ok, user_info
from fixate.core.checks import *

__version__ = "1"


class SimpleTest(TestClass):
    """Simple passing test"""

    def test(self):
        chk_true(True, "It is True!")


TEST_SEQUENCE = [SimpleTest()]