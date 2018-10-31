=================
Quick start guide
=================

This document should talk you through everything you need to get started with
Fixate.

------------
Installation
------------

Fixate is available on `PyPI <https://pypi.org/project/fixate/>`_

This can be installed using pip

.. code:: bash

  pip install fixate

If you are planning on using the GUI you will also need PyQT5

.. code:: bash

  pip install PyQt5
  

-------------------
Learning By Example
-------------------

We will now follow through the examples provided with Fixate.
Examples can be found in fixate/examples

tiny.py
*******

For our first example we will be referencing tiny.py

.. code:: python

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

The core of Fixate can be seen with these first three import statments

.. code:: python

  from fixate.core.common import TestClass, TestList
  
The TestList we will look at further on in this example.

The TestClass is the base class used throughout your test scripts to encapsulate a single test's logic.

.. autoclass:: fixate.core.common.TestClass
 :members:
 
 
 
 
 
 
The TestList can be used to contain multiple TestLists and/or TestClasses in order to structure your tests.

.. autoclass:: fixate.core.common.TestList
 :members: set_up, tear_down, enter, exit

 

.. automodule:: fixate.examples.tiny
 :members:
 
 
