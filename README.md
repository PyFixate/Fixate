[![Tests](https://github.com/PyFixate/Fixate/actions/workflows/test.yml/badge.svg)](https://github.com/PyFixate/Fixate/actions/workflows/test.yml)
[![Docs](https://readthedocs.org/projects/fixate/badge/)](https://fixate.readthedocs.io/en/latest/?badge=latest)

# Fixate

Fixate is a Python library for testing real stuff.
Fixate provides a framework for writing scripts in Python to test hardware.
Providing drivers for equipment, support for switching, logging and a basic test runner UI.
While Fixate is fairly simple, it is already being used to test real electronics products in real factories.

## Getting Started

Fixate runs on Python 3.8 or greater.

### Installing

Clone the repository using git or download a zip file and unzip the source. Then run setup.py to install.
Alternatively, install from Pypi with 'pip install fixate'

### Run the example scripts

There are a number of examples under the examples folder.
You will need a clone fo the git repository to get the examples.
For a minimal example try running tiny.py.
For a more complicated example using multi-level tests, try running multi_level_design.py.
The test runner is executed by calling the `fixate` package and passing in the test script to execute using the '-p' command line argument.

The following commands are for Windows:

```sh
git clone https://github.com/PyFixate/Fixate.git
cd Fixate
py -m venv .venv
.venv\Scripts\activate
py -m pip install .
py -m fixate -p examples\tiny.py
```

#### Make a script directly executable

For easier development, test scripts can be setup to call the fixate main as their own with some default parameters, as in:

python examples/tiny.py

## Running the tests
In general, it is recommended to run the "core" set of tests.
The "drivers" tests have a number of dependencies that are not required by default.
Tests are run using pytest.
The easiest way to run the test is using tox.
To run the tests manually using pytest, excluding tests that required instruments, you can run `pytest -m "not drivertest"`. 


## Check out the docs

https://fixate.readthedocs.io

## Contributing

Contributions are welcome. Get in touch or create a new pull request.

Pull requests will need to pass code checks. You can run these most easily locally via [`pre-commit`](https://pre-commit.com/):

```
pip install pre-commit
pre-commit install --install-hooks 
pre-commit run --all-files # if not run before on your changes, otherwise leave off the flag
```


## Authors

* **Ryan Parry-Jones** - *Original Developer* - [pazzarpj](https://github.com/pazzarpj)

See also the list of [contributors](https://github.com/PyFixate/Fixate/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details
