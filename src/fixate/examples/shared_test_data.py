from fixate.core.ui import user_info
from fixate.core.common import TestClass, TestList
import fixate

__version__ = "2"

seq = fixate.config.RESOURCES["SEQUENCER"]


class TestListOuter(TestList):
    outer: int
    other_data: float

    def __init__(self, seq, *, outer: int = 5):
        super(TestListOuter, self).__init__(seq)
        self.outer = outer

    def enter(self):
        self.other_data = 0.5


class TestListInner(TestList):
    inner: int
    other_data: str

    def enter(self):
        self.inner = 10
        self.other_data = "Hello"


class TestListNotRun(TestList):
    other_data: int


class TestOuter(TestClass):
    def test(self, outer_list: TestListOuter):
        user_info(f"Outer.outer: {outer_list.outer}")
        user_info(f"Outer.other: {outer_list.other_data}")


class TestBoth(TestClass):
    def test(self, outer_list: TestListOuter, inner_list: TestListInner):
        user_info(f"Outer.outer: {outer_list.outer}")
        user_info(f"Outer.other: {outer_list.other_data}")
        user_info(f"Inner.inner: {inner_list.inner}")
        user_info(f"Inner.other: {inner_list.other_data}")


class TestOther(TestClass):
    def test(self, outer_list: TestListOuter, inner_list: TestListInner, not_run: TestListNotRun):
        user_info(f"Outer.outer: {outer_list.outer}")
        user_info(f"Outer.other: {outer_list.other_data}")
        user_info(f"Inner.inner: {inner_list.inner}")
        user_info(f"Inner.other: {inner_list.other_data}")


test_data = {
    "standard": TestList([TestListOuter([TestListInner([TestBoth()])])]),
    # Should fail as TestListNotRun in not run
    "test_not_run": TestList([TestListOuter([TestListInner([TestOther()])])]),
    # Should fail as TestBoth doesn't have TestListOuter in scope
    "list_out_of_scope": TestList([TestListOuter([TestOuter()]), TestListInner([TestBoth()])]),
    # Should use the inner most match to the test list. First TestOuter should print 10, second should print 20
    # Eg. 1.1 Outer.outer: 10, 1.2.1 Outer.outer: 20
    "used_multi_level": TestList([
        TestListOuter(
            [
                TestOuter(),
                TestListOuter([
                    TestOuter()
                ], outer=20),

            ],
            outer=10)
    ])
}
