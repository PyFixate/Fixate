[![Tests](https://github.com/PyFixate/Fixate/actions/workflows/test.yml/badge.svg)](https://github.com/PyFixate/Fixate/actions/workflows/test.yml)
[![Docs](https://readthedocs.org/projects/fixate/badge/)](https://fixate.readthedocs.io/en/latest/?badge=latest)

# Fixate

Fixate is a Python library for testing real stuff.
Fixate provides a framework for writing scripts in Python to test hardware.
Providing drivers for equipment, support for switching, logging and a basic test runner UI.
While Fixate is fairly simple, it is already being used to test real electronics products in real factories.

## Getting Started

Fixate runs on Python 3.7 or greater.

### Installing

Clone the repository using git or download a zip file and unzip the source. Then run setup.py to install.
Alternatively, install from Pypi with 'pip install fixate'

### Run the example scripts

There are a number of examples under src/fixate/examples. For a minimal example try running tiny.py.
For a more complicated example using multi-level tests, try running multi_level_design.py.
The test runner is executed by calling the package as a script with the test script to execute passed in using the
'-p' command line argument, as well as the -c command line argument to specify the config file

#### Running on Windows:

If running from a pip installed version of fixate the path to the examples will be "path_to_python_installation"/Lib/site-packages/fixate/examples/ From this folder the following can be executed:

python -m fixate -p tiny.py

Alternatively the full path to tiny.py can be provided.

python -m fixate -p "path_to_python_installation"/Lib/site-packages/fixate/examples/tiny.py

#### Running on MacOS:

Running on Mac is the same as running on Windows with the exception of the path to the examples. The path will be: "path_to_python_installation"/lib/pythonX.Y/site-packages/fixate/examples/
Where X.Y is the version of python that is installed.

## Running the tests
In general, it is recommended to run the "core" set of tests.
The "drivers" test have a number of dependencies that are not required by default. Tests run using unittest.
Navigate to the test/core directory and execute "python -m unittest".

## Modifying the Qt GUI

The Qt GUI base file is created using Qt Designer under Mingw32.
If you'd like to make changes, use pyuic5 to build the layout file, with the command:

pyuic5 fixateGUI.ui -o layout.py


## Check out the docs

https://fixate.readthedocs.io

## Contributing

Contributions are welcome. Get in touch or create a new pull request.

## Authors

* **Ryan Parry-Jones** - *Original Developer* - [pazzarpj](https://github.com/pazzarpj)

See also the list of [contributors](https://github.com/PyFixate/Fixate/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details
