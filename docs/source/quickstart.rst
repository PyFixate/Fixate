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

If you are planning on using the included GUI you will also need PyQT5

.. code:: bash

  pip install PyQt5

We recommend installing and running fixate in an isolated environment such as virtualenv or pipenv.

-------
Running
-------

Fixate can be run by activating the virtual environment and then

.. code:: bash

  python -m fixate -p <path_to_test_script>

There are some example test scripts in fixate.examples

.. code:: bash

  python -m fixate -p examples/test_script.py

Or to run with the GUI

.. code:: bash

  python -m fixate -p examples/test_script.py -q

