==================================
Release Notes
==================================
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
