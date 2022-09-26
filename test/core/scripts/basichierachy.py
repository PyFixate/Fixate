from fixate.core.common import TestClass, TestList
from fixate.core.checks import chk_true
import fixate


class Test(TestClass):
    """
    Dummy Test Class
    """

    def set_up(self):
        chk_true(self.fail_flag != "test_setup", "Failure in the test setup")
        assert self.raise_flag != "test_setup", "Exception in the test setup"

    def tear_down(self):
        chk_true(self.fail_flag != "test_teardown", "Failure in the test tear down")
        assert self.raise_flag != "test_teardown", "Exception in the test tear down"

    def test(self):
        chk_true(self.fail_flag != "test_test", "Failure in the test test")
        assert self.raise_flag != "test_test", "Exception in the test test"

    def __init__(self, fail_flag=None, raise_flag=None):
        super().__init__()
        self.fail_flag = fail_flag
        self.raise_flag = raise_flag


class Lst(TestList):
    """
    Dummy Test List
    """

    def set_up(self):
        chk_true(self.fail_flag != "list_setup", "Failure in the test list setup")
        assert self.raise_flag != "list_setup", "Exception in the test list setup"

    def tear_down(self):
        chk_true(
            self.fail_flag != "list_teardown", "Failure in the test list tear down"
        )
        assert (
            self.raise_flag != "list_teardown"
        ), "Exception in the test list tear down"

    def enter(self):
        chk_true(self.fail_flag != "list_enter", "Failure in the test list enter")
        assert self.raise_flag != "list_enter", "Exception in the test list enter"

    def exit(self):
        chk_true(self.fail_flag != "list_exit", "Failure in the test list exit")
        assert self.raise_flag != "list_exit", "Exception in the test list exit"

    def __init__(self, seq=[], fail_flag=None, raise_flag=None):
        super().__init__(seq)
        self.fail_flag = fail_flag
        self.raise_flag = raise_flag


# When called as a test, use the --script-params flag to pass in values for
# fail_flag and raise_flag. Possible values to set those flags to are:  -
#   - "test_setup"
#   - "test_teardown"
#   - "test_test"
#   - "list_setup"
#   - "list_teardown"
#   - "list_enter"
#   - "list_exit"

context_data = fixate.global_sequencer.context_data

TEST_SEQUENCE = [
    Lst(
        [
            Test(
                fail_flag=context_data["fail_flag"],
                raise_flag=context_data["raise_flag"],
            )
        ],
        fail_flag=context_data["fail_flag"],
        raise_flag=context_data["raise_flag"],
    )
]
