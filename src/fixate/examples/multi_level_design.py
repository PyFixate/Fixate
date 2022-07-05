from fixate.core.ui import user_info
from fixate.core.common import TestClass, TestList
from fixate import global_sequencer

__version__ = "2"

# Standard expected output
"""
1: list enter
1: setup 1
1: test 1
1: teardown 1
2: list enter
2.1: list setup
2.1: setup 2
2.1: test 2
2.1: teardown 2
2.1: list teardown
2.2: list enter
2.2.1: list setup
2.2.1: list setup
2.2.1: setup 3
2.2.1: test 3
2.2.1: teardown 3
2.2.1: list teardown
2.2.1: list teardown
2.2.2: list setup
2.2.2: list setup
2.2.2: setup 4
2.2.2: test 4
2.2.2: teardown 4
2.2.2: list teardown
2.2.2: list teardown
2.2: list exit
2: list exit
3: list enter
3.1: list enter
3.1.1: list setup
3.1.1: list setup
3.1.1: setup 5
3.1.1: test 5
3.1.1: teardown 5
3.1.1: list teardown
3.1.1: list teardown
3.1.2: list setup
3.1.2: list setup
3.1.2: setup 6
3.1.2: test 6
3.1.2: teardown 6
3.1.2: list teardown
3.1.2: list teardown
3.1: list exit
3.2: list setup
3.2: setup 7
3.2: test 7
3.2: teardown 7
3.2: list teardown
3: list exit
4: setup 10
i'm a subclass
4: teardown 10
: list exit
"""

class Test(TestClass):
    """
    Dummy Test Class
    """

    def set_up(self):
        print("{}: setup {}".format(global_sequencer.levels(), self.num))

    def tear_down(self):
        print("{}: teardown {}".format(global_sequencer.levels(), self.num))

    def test(self):
        print("{}: test {}".format(global_sequencer.levels(), self.num))

    def __init__(self, num):
        super().__init__()
        self.num = num


class FailTest(TestClass):
    """
    Dummy Test Class
    """

    def set_up(self):
        print("{}: setup {}".format(global_sequencer.levels(), self.num))

    def tear_down(self):
        print("{}: teardown {}".format(global_sequencer.levels(), self.num))

    def test(self):
        raise Exception("Purpose fail {}: test {}".format(global_sequencer.levels(), self.num))
        # print("{}: test {}".format(seq.levels(), self.num))

    def __init__(self, num):
        super().__init__()
        self.num = num


class TestSubclass(Test):
    """
    Dummy Test SubClass
    """

    def test(self):
        print("i'm a subclass")


class Lst(TestList):
    """
    Dummy Test List
    """

    def set_up(self):
        print("{}: list setup".format(global_sequencer.levels()))

    def tear_down(self):
        print("{}: list teardown".format(global_sequencer.levels()))

    def enter(self):
        print("{}: list enter".format(global_sequencer.levels()))

    def exit(self):
        print("{}: list exit".format(global_sequencer.levels()))


class FailSetup(TestList):
    """
    Dummy Test List
    """

    def set_up(self):
        print("{}: list setup".format(global_sequencer.levels()))
        raise Exception("Raise exception in {}: list setup".format(global_sequencer.levels()))

    def tear_down(self):
        print("{}: list teardown".format(global_sequencer.levels()))

    def enter(self):
        print("{}: list enter".format(global_sequencer.levels()))

    def exit(self):
        print("{}: list exit".format(global_sequencer.levels()))


class FailEnter(TestList):
    """
    Dummy Test List
    """

    def set_up(self):
        print("{}: list setup".format(global_sequencer.levels()))

    def tear_down(self):
        print("{}: list teardown".format(global_sequencer.levels()))

    def enter(self):
        print("{}: list enter".format(global_sequencer.levels()))
        raise Exception("Raise exception in Enter")

    def exit(self):
        print("{}: list exit".format(global_sequencer.levels()))


class Foo(TestClass):
    """
    Foo
    """

    def set_up(self):
        user_info("Foo Setup")

    def tear_down(self):
        user_info("Foo TearDown")

    def test(self):
        pass


tests = Lst(
    [
        Test(1),
        Lst([Test(2), Lst([Test(3), Test(4)])]),
        Lst([Lst([Test(5), Test(6)]), Test(7)]),
        TestSubclass(10),
    ]
)

tests_no_test_list = [
    Test(1),
    [Test(2), [Test(3), Test(4)], [[Test(5), Test(6)], Test(7)], TestSubclass(10)],
]

tests_list_enter_fail = Lst(
    [
        Test(1),
        Lst([Test(2), Lst([Test(3), Test(4)])]),
        FailEnter([Lst([Test(5), Test(6)]), Test(7)]),
        TestSubclass(10),
    ]
)

test_deep_test_fail = Lst(
    [
        Test(1),
        Lst([Test(2), Lst([Test(3), Test(4)])]),
        Lst([Lst([Test(5), FailTest(6)]), Test(7)]),
        TestSubclass(10),
    ]
)
test_list_setup_fail = Lst(
    [
        Test(1),
        Lst([Test(2), Lst([Test(3), Test(4)])]),
        FailSetup([Lst([Test(5), Test(6)]), Test(7)]),
        TestSubclass(10),
    ]
)
TEST_SEQUENCE = tests

test_data = {
    "standard": tests,
    "no_test_list": tests_no_test_list,
    "list_enter_fail": tests_list_enter_fail,
    "deep_test_fail": test_deep_test_fail,
    "list_setup_fail": test_list_setup_fail,
}
