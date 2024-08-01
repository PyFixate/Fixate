from fixate.core.common import TestClass, TestList
from fixate.core.ui import user_ok, user_info
from fixate.core.checks import *

__version__ = "1"


class SimpleTest(TestClass):
    """You *need* a description...?"""

    def setup(self):
        user_info("Tests can have setup")

    def teardown(self):
        user_info("Tests can have teardown")

    def test(self):
        user_info("Fingers crossed, this will pass")
        chk_true(True, "It is True!")


class MyTestList(TestList):
    """Tests lists make a good container for parameterised tests"""

    def enter(self):
        user_info("Entering the test list")

    def exit(self):
        user_info("Leaving the test list")


class ParameterisedTest(TestClass):
    """Another description"""

    def __init__(self, param, **kargs):
        """If you overide the __init__ to parameterise the test, make
        sure you call __init__ on super"""
        super().__init__(**kargs)
        self.param = param

    def test(self):
        user_ok("Testing param={}. Press Enter".format(self.param))


test_data = {
    "minimal": [SimpleTest()],
    "small": [SimpleTest(), MyTestList([ParameterisedTest(1), ParameterisedTest(2)])],
    "large": [SimpleTest(), MyTestList([ParameterisedTest(x) for x in range(50)])],
}
