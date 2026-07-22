from fixate import (
    user_gif,
    user_image,
    user_image_clear,
    user_info,
    user_info_important,
    user_input,
    user_input_float,
    user_ok,
    user_post_sequence_info,
    user_post_sequence_info_fail,
    user_post_sequence_info_pass,
    user_yes_no,
)
from fixate.core.checks import chk_fails, chk_passes
from fixate.core.common import TestClass


# This manual test just uses one UI element after the other, ensure they display and take input as they should.
# Logical checks on the data aren't required because these are tested in the unit tests, this is just to check the UI elements are working as expected.
# The test sequence will need to be run twice per UI type to test the post sequence info elements, as they only show on pass
# or fail of the sequence.
class TestsPassing(TestClass):
    def test(self):
        gui_display = False
        user_info("This test will show all the different UI elements.")

        resp = user_yes_no("Is this test running in the GUI?")
        if resp == "YES":
            gui_display = True

        disp_str = "This is an info message, this bit of text is to make the message a bit longer to check text wrapping, check that the wrapping is behaving correctly"
        if gui_display:
            user_info(disp_str + " in both the main view and history view.")
        else:
            user_info(disp_str)

        disp_str = "This is an important info message, this bit of text is to make the message a bit longer to check text wrapping, check that the wrapping is behaving correctly"
        if gui_display:
            user_info_important(disp_str + " in both the main view and history view.")
            user_ok("Only the Continue button should be visible.")
            user_yes_no("Are only the Yes and No buttons visible?")
        else:
            user_info_important(disp_str)
            user_ok("You should see a Press Enter to continue message below.")
            user_yes_no("Are only the Yes and No options visible?")

        user_image("ui_manual_test.jpg")
        if gui_display:
            user_ok("You should see the image in the image view")
        else:
            user_ok(
                "You should see a warning that the image could not be displayed and the name of the file"
            )

        user_gif("ui_manual_test.gif")
        if gui_display:
            user_ok("You should see the GIF in the image view")
        else:
            user_ok(
                "You should see a warning that the GIF could not be displayed and the name of the file"
            )

        user_image_clear()

        user_input("Please enter some text:")
        user_input_float("Please enter a float:")

        user_post_sequence_info(
            "This is post sequence info, it should always show in the active and history window."
        )
        user_post_sequence_info_pass(
            "This is post sequence info that should only show if the sequence passes"
        )
        user_post_sequence_info_fail("This should not show, as the sequence is passing")


class TestsFailing(TestClass):
    def test(self):
        user_info(
            "This test will only test the post sequence info elements that show on fail"
        )
        user_post_sequence_info_pass("This should not show, as the sequence is failing")
        user_post_sequence_info_fail(
            "This is post sequence info that should only show if the sequence fails"
        )
        chk_fails("You will need to select FAIL or ABORT for this test to work.")


PASSING_TESTS = [TestsPassing()]
FAILING_TESTS = [TestsFailing()]

test_data = {
    "PASSING": PASSING_TESTS,
    "FAILING": FAILING_TESTS,
}

if __name__ == "__main__":
    import sys

    import fixate

    # call with -q to perform these tests in the GUI.
    # pass in -i PASSING or -i FAILING to run the specified test sequence, run each one with -q and without.
    extra_args = sys.argv[1:]

    argv = ["-p", __file__, "--serial_number", "1234567890"] + extra_args
    fixate.run(__file__, argv)
