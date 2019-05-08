from fixate.core.common import TestClass, TestList
from fixate.core.ui import user_ok, user_info, user_image, user_image_clear
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
        user_image("base_test.jpg")
        user_ok("Press OK to continue")
        chk_true(True, "It is True!")
        user_image_clear()


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
        user_image("base_test.jpg")
        user_ok("Testing param={}. Press Enter".format(self.param))
        user_image("base_test.jpg")
        user_image("overlay_test.png")
        user_ok("The overlay should be on screen. Press OK to continue")
        user_image("base_test.jpg")
        user_image("overlay_test.png")
        user_image("overlay_test_2.png")
        user_ok("The second overlay should be on screen. Press OK to continue")
        user_image("base_test_2.jpg")
        user_ok("The second base image should be on screen. Press OK to continue")
        user_image("base_test_2.jpg")
        user_image("overlay_test.png")
        user_ok(
            "The overlay should be on screen. It doesn't match the new base image. Press OK to continue"
        )
        user_image("base_test_2.jpg")
        user_ok("The overlay should be cleared, leaving the base. Press OK to continue")
        user_ok("The screen should be clear. Press OK to continue")
        user_image("base_test_2.jpg")
        user_image_clear()
        user_ok("The screen should also be clear. Press OK to continue")
        user_image("Invalid_Image.abc")
        user_ok("There should have been a warning box. Press OK to continue")


TEST_SEQUENCE = [SimpleTest(), MyTestList([ParameterisedTest(1)])]
