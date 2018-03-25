# Fixate

Fixate is a Python library for testing real stuff. Fixate provides a framework for writing scripts in Python to test hardware. Providing drivers for equipment, support for switching, logging and a basic test runner UI. While Fixate is fairly simple, it is already being used to test real electronics products in real factories.

## Getting Started

Fixate runs on Python 3.4 or greater.

### Installing

Clone the repository using git or download a zip file and unzip the source. Then run setup.py to install. For the moment, there is no package on PyPI.

### Run the example scripts

There are a number of examples under src/fixate/examples. For a minimal example try running tiny.py. For a more complicated example using multi-level tests, try running multi_level_design.py. The test runner is executed by calling the package as a script with the test script to execute passed in using the -p command line argument:

python -m fixate -p tiny.py

## Running the tests
In general, it is recommended to run the "core" set of tests. The "drivers" test have a number of dependencies that are not required by default. Tests run using unittest. Navigate to the test/core directory and execute "python -m unittest".

## Contributing

Contributions are welcome. Get in touch or create a new pull request.

## Authors

* **Ryan Parry-Jones** - *Original Developer* - [pazzarpj](https://github.com/pazzarpj)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
