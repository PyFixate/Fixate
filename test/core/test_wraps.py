import unittest
from fixate.core.common import deprecated

TEST_NAME = "test_function_depreciated"
NAME_WITHOUT_WRAPS = "inner"


class TestWrapsClass:
    def __init__(self):
        pass

    @deprecated
    def test_function_depreciated(self, input):
        """
        returns __name__ if input is true, else returns input
        """
        name = __name__
        if input is True:
            return name
        else:
            return input


class TestDepreciatedExists(unittest.TestCase):
    """
    Test the test, check the function exits
    """
    attempts = 1

    def setUp(self):
        self.test_class = TestWrapsClass()
        self.num = 1

    def test(self):
        self.assertEqual(self.test_class.test_function_depreciated(self.num), self.num)


class TestDepreciatedName(unittest.TestCase):
    """
    Check the function name
    """
    attempts = 1
    name = TEST_NAME

    def setUp(self):
        self.test_class = TestWrapsClass()

    def test(self):
        name = self.test_class.test_function_depreciated.__name__
        self.assertEqual(TEST_NAME, name)


class TestDepreciatedNameInternal(unittest.TestCase):
    """
    Check the function name as seen inside the function
    """
    attempts = 1

    def setUp(self):
        self.test_class = TestWrapsClass()
        self.num = 1

    def test(self):
        self.assertNotEqual(NAME_WITHOUT_WRAPS, self.test_class.test_function_depreciated(True))


if __name__ == '__main__':
    unittest.main()
