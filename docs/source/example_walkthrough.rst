-------------------
Learning By Example
-------------------

We will now follow through the examples provided with Fixate.
Examples can be found in the examples subfolder

*******
tiny.py
*******

For our first example we will be referencing tiny.py

First of all, lets try running it

.. code:: bash

  python -m fixate -p tiny.py

After we move through the test run we should have an output like::

    >>> Please enter serial number
    ***************************************************************************
    Test : The TestList is a container for TestClasses and TestLists to set up
    a test hierarchy.
    ---------------------------------------------------------------------------
    ***************************************************************************
    Test 1: You *need* a description...?
    ---------------------------------------------------------------------------
    Fingers crossed, this will pass

    Check 1: PASS: 1 : It is True!
    ---------------------------------------------------------------------------
    Checks passed: 1, Checks failed: 0
    Test 1: PASS
    ---------------------------------------------------------------------------
    ***************************************************************************
    Test 2: Tests lists make a good container for parameterised tests
    ---------------------------------------------------------------------------
    Entering the test list
    ***************************************************************************
    Test 2.1: Another description
    ---------------------------------------------------------------------------
    Testing param=1. Press Enter

    Press Enter to continue...
    ---------------------------------------------------------------------------
    Checks passed: 0, Checks failed: 0
    Test 2.1: PASS
    ---------------------------------------------------------------------------
    ***************************************************************************
    Test 2.2: Another description
    ---------------------------------------------------------------------------
    Testing param=2. Press Enter

    Press Enter to continue...
    ---------------------------------------------------------------------------
    Checks passed: 0, Checks failed: 0
    Test 2.2: PASS
    ---------------------------------------------------------------------------
    Leaving the test list
    ###########################################################################
    Sequence Finished
    ---------------------------------------------------------------------------
    Status: PASSED
    ###########################################################################
    Finished testing

    Press Enter to continue...

tiny.py contains a very minimal example of what you can build with Fixate.

TEST_SEQUENCE in this case is a list of all the tests to run.

.. code:: python

  TEST_SEQUENCE = [SimpleTest(), MyTestList([ParameterisedTest(1), ParameterisedTest(2)])]

You can see how this list corresponds to the output we had before.
Fixate will launch it by running the following implemented functions in this order

- SimpleTest.setup()
- SimpleTest.test()
- SimpleTest.teardown()
- MyTestList.enter()
- ParameterisedTest(1).test()
- ParameterisedTest(2).test()
- MyTestList.exit()

For more a more complex example on test hierarchy see multi_level_design.py in examples

SimpleTest
##########

Lets have a look at the simple test

.. code:: python

  class SimpleTest(TestClass):
      """You *need* a description...?"""

      def set_up(self):
          user_info("Tests can have setup")

      def tear_down(self):
          user_info("Tests can have teardown")

      def test(self):
          user_info("Fingers crossed, this will pass")
          chk_true(True, "It is True!")

The SimpleTest inherits from TestClass.

A TestClass is a class that is the core to all tests in Fixate.
If you are familiar with the unittest library then it operates similar to the unittest.TestCase

- setup happens before every test
- teardown happens after every test (even when an error occurs)
- test will contain the guts of the code that determine pass or failure.

The equivalent python code for a TestClass execution would be

.. code:: python

  x = SimpleTest()
  try:
      x.set_up()
      x.test()
  finally:
      x.tear_down()

As such it is important to make sure that the teardown function can run error free, even if the setup doesn't complete

Check Functions
###############

Check functions indicate to fixate whether a test passes or fails.

You can have multiple checks in a single test and each one will be individually tested and logged.

If any single check fails, the entire test is marked as failed.

In SimpleTest we have one of the the most basic checks

.. code:: python

  def test(self):
      user_info("Fingers crossed, this will pass")
      chk_true(True, "It is True!")

chk_true will check that the first parameter passed into it is True.

The second parameter is the description of the test for the user to see in the UI as well as the log to identify
the test.

All checks are prefixed by chk and can be found in fixate.checks

User Interaction
################

Most tests will require some user interaction, from just providing useful information to asking the user to perform
a task.

Fixate aims to keep the same API for the basic command line interface as well as the optional/pluginable GUI
versions.

For example

.. code:: python

  def test(self):
      user_info("Fingers crossed, this will pass")

Will show in the output as::

  Fingers crossed, this will pass

Another basic user interaction is

.. code:: python

    def test(self):
        user_ok("Testing param={}. Press Enter".format(self.param))

This will stop the sequence at this point and ask the user to do something::

    Testing param=1. Press Enter

There are more variety of user interaction APIs available that can be found in fixate.core.ui

Test Naming
###########
::

  Test 1: You *need* a description...?

Two things about this

- Notice how the first test in the sequence will automatically be numbered 1
- The test is automatically named by the docstring of SimpleTest.

The docstring is used to provide the test name where the first line will show up in the UI and the log as the test name
and the remaining lines will be logged under test_desc_long

If no docstring is present, then the class name will be used to name the test

Parameterised Tests
###################

Parameterised tests are the core of code reuse

.. code:: python

  class ParameterisedTest(TestClass):
      """Another description"""

      def __init__(self, param, **kargs):
          """If you overide the __init__ to parameterise the test, make
          sure you call __init__ on super"""
          super().__init__(**kargs)
          self.param = param

      def test(self):
          user_ok("Testing param={}. Press Enter".format(self.param))

A TestClass can be initialised with parameters by overriding the __init__ function and storing the parameters on the
instance. Make sure when overriding __init__ that you call super so that the rest of the TestClass functions as
expected.

You can then add them to the test sequence with arbitary parameters such as

.. code:: python

  TEST_SEQUENCE = [SimpleTest(), MyTestList([ParameterisedTest(1), ParameterisedTest(2)])]

TestLists
#########

A TestList is a container TestClasses. A standard python list can be used in place of this is many instances.

Reasons you might want to use a TestList over a python list

- Naming the test in logs or in the UI (Using Docstrings)
- Running a set of setup or teardown code before every test contained within it
- Running something when entering or exiting the test list

Lists or TestLists can be used to set the test hierarchy allowing you to group similar tests so they will show up as
1.1, 1.2, 1.3 instead of 1, 2, 3.

Note: Internally, all python standard lists are converted into standard TestLists before running.


 
