""" Private wrapper for ftdi driver. DLL on Windows, .so shared library on *nix.
This is wrapped privately so it can be ommitted from the documentation build.
"""

import ctypes
import sys

if sys.platform == "win32":
    try:
        ftdI2xx = ctypes.WinDLL("FTD2XX.dll")
    except Exception as e:
        raise ImportError(
            "Unable to find FTD2XX.dll.\nPlugging in an FTDI device will install the DLL."
        ) from e

else:
    try:
        ftdI2xx = ctypes.cdll.LoadLibrary("/usr/local/lib/libftd2xx.so")
    except Exception as e:
        raise ImportError(
            "Unable to find libftd2xx.so.\nInstall as per https://www.ftdichip.com/Drivers/D2XX/Linux/ReadMe-linux.txt"
        ) from e
