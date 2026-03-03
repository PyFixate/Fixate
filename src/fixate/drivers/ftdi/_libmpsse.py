""" Private wrapper for ftdi libmpsse driver. DLL on Windows, .so shared library on *nix.
This is wrapped privately so it can be ommitted from the documentation build.
"""

import ctypes
import sys
from importlib import resources

if sys.platform == "win32":
    try:
        with resources.path("fixate.drivers.ftdi.libs", "libmpsse.dll") as lib_path:
            libmpsse = ctypes.WinDLL(lib_path)
    except Exception as e:
        raise ImportError(
            "Unable to find libmpsse.dll.\nThis should have been included in the fixate package installation."
        ) from e

else:
    try:
        # this won't work at this stage since the .so file isn't included in the package yet.
        with resources.path("fixate.drivers.ftdi.libs", "libmpsse.so") as lib_path:
            libmpsse = ctypes.cdll.LoadLibrary(lib_path)
    except Exception as e:
        raise ImportError(
            "Unable to find libmpsse.so.\nThis should have been included in the fixate package installation."
        ) from e
