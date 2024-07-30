==================================
Release Notes
==================================
*************
Version 0.6.3
*************
Release Date xx/xx/xx

New Features
############
- API docs are not auto generated. However, work is still ongoing to update
  them and to clarify public APIs vs internal implementation details.
- A new jig switching manager is added. Similar to fixate.core.jig_mapping, but
  easier to use and much improved implementation details.
- ``--diagnostic-log-dir`` cli argument control the log file location, instead of
  always using the platform default
- A new function, ``fixate.run()``, which can be used to make a script self executing.


Improvements
############
- Test now run on MacOS
- Developer workflow improvements by adding pre-commit tool

*************
Version 0.6.2
*************
Release Date 05/06/24

New Features
############

Improvements
############
- Add logging of computer name to log file.
- Update DMM driver with optional measurement delay to improve DMM model compatibility.


*************
Version 0.6.1
*************
Release Date 22/05/2023

New Features
############
- New DMM driver added for Keithley 6500 DMM. 
- Add optional formatting argument ('fmt') to check functions to improve ui display and logging of test values.
- Add logging of FTDI instruments on connection. Allow regex matching of the ftdi description.

Improvements
############
- Fix bug where sequencer would return success if terminated during startup.
- Failure to open a drivers pyvisa resource will now raise a more informative InstrumentOpenError exception from the pyvisa error.
- Remove unused error_cleanup function and flags in fluke DMM driver.
- Remove temperature, ftemperature, analog filter and digital filter from DMM drivers.
- Add _voltage_range to frequency and period measurement modes.
- Fix initial serial number check to properly raise exception on incorrect entry.

*************
Version 0.6.0
*************
Release Date 21/10/2022

Major Changes
################
Relocation of configuration files:

- Logs now located in platformdirs.user_log_dir("Fixate")
- Instrument config file renamed from local_config.json -> instruments.json and located in platformdirs.site_config_dir("Fixate")
- fixate.yml also moved to platformdirs.site_config_dir("Fixate")

New Features
############
- Added gif support for the gui. Try user_gif("<path to .gif>")
- Clearing the gui image scene will now create a new instance to reset auto-scaling.

Improvements
############
- Updated siglent PPS driver to support parsing of error strings in the latest firmware

*************
Version 0.5.7
*************
Release Date 12/07/2022

Fix to pyvisa imports

*************
Version 0.5.6
*************
Release Date 18/05/2022

Minor packaging changes only

*************
Version 0.5.5
*************
Release Date 18/05/2022

New Features
############
- Add some extra measurement functions to the scope driver.
- Dependencies for use of the GUI are now declared as an extra so it is
  possible to install using "pip install fixate[gui]"

Improvements
############
- Switch to github actions for CI.
- Fix broken tests & update the build system.
- Change how driver imports work.
- Remove some unused functions from fixate.core.control.

*************
Version 0.5.4
*************
Release Date 20/08/2020

New Features
############
- Driver can now report an identify string, which is logged when the driver is loaded.

Improvements
############
- Fixes made to the daqmx TwoEdgeSeparation to fix the issue introduced from the previous release.
- fxconfig updated to use the latest version of cmd2
- Fix some tests that were failing due to updated dependencies.

*************
Version 0.5.3
*************
Release Date 03/07/2019

Breaking Changes
################
- daqmx driver's TwoEdgeSeparation function is likely broken or less robust. The changes made to ExcThread need to be tested against that hardware.

New Features
############
- Operation logging is now enabled. "fixate.log" will be written to the working directory on each invocation. Logging can be disabled with the --disable-log command line argument.

Improvements
############
- Previously the sequencer was called from an async event loop, even though async was not used anywhere. This has been removed, simplifying __main__.py significantly.
- ExcThread changed so it doesn't try to force re-raise exceptions in the main thread.
- GUI code cleaned up to make distinction between different execution contexts clearer.
- Fixed some thread safety issues in the GUI where widgets were getting updating outside of the main thread.

*************
Version 0.5.2
*************
Release Date 24/05/2019

Breaking Changes
################
- Test script UI functions user_retry_abort, user_retry_auto, user_pass_fail, user_choices, user_retry have been removed.

New Features
############
- None

Improvements
############
- Fix dependency cmd2 that was missing when installing using pip.
- Fix a bug where user_action calls didn't work correctly.
- Many source level improvements.

*************
Version 0.5.1
*************
Release Date 14/05/2019

Breaking Changes
################
- None

New Features
############

- None

Improvements
############

- Source code has been reformated using `Black <https://github.com/python/black>`_.

*************
Version 0.5.0
*************

Release Date 03/05/2019

Breaking Changes
################

- Instruments config is no longer automatic. fxconfig utility must be used to add or change the instrument config. moving away from "auto config" makes instrument recovery much more reliable after errors and prevents some undesirable side effects of write out serial commands to port with unknown equipment (which would happen previously).
- The "measure"  method has been deleted from the Fluke 8846A driver.

New Features
############

- Instrument configuration tool, fxconfig
- Virtual mux can now have make-before-break switching as well as break-before-make
- The Jig meta class now installed "active_pins" method which is useful while debugging test scripts.

Improvements
############

- Updates to README.md
- CI Build configuration improvements
- Improvements to the sphinx docs including a quick start guide and walk through example
- New tiny-variants.py example script.
- Many small code improvements with dead code removed
- VirtualMux definitions will now warn when a pin name is used twice.
- The Fluke 8846A driver now uses auto trigger. In general this will make using the DMM faster and more reliable.
- The Fluke 8846A no longer does error queries after each command. This makes the driver faster. The old behaviour can be reinstated using by setting self.legacy_mode = True.
- Change the DMM driver base class to raise NotImplementedError, rather than silently pass on methods that aren't overridden.
- The Agilent/Keysight DSO driver updated to significantly improve acquisition & measurement reliability
- The FTDI driver now support 64-bit python as well as 32-bit python.
- Command line UI now works on Windows and Linux (test on a Rpi running Ubuntu)
