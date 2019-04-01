==================================
Release Notes
==================================
*************
Version 0.5.0
*************

Release Date xx/xx/xx

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
- The Fluke 8846A no longer does error queries after each command. This makes the driver faster. The old behaviour can be reinstated using by setting self.legacy_mode = False.
- Change the DMM driver base class to rasise NotImplementedError, rather than silently pass on method that aren't overridden.
- The Agilent/Keysight DSO driver updated to significantly improve acquisition & measurement reliability
- The FTDI driver now support 64-bit python as well as 32-bit python.
- Command line UI now works on Windows and Linux (test on a Rpi running Ubuntu)
