# import unittest.mock
# import sys
# import os
# import ctypes
import pytest


def test_driver_files():
    import fixate.drivers.dmm
    import fixate.drivers.dso
    import fixate.drivers.funcgen
    import fixate.drivers.lcr
    import fixate.drivers.pps


# _files_path = os.path.join(os.path.dirname(__file__), "files")
#
# class MockDAQConfig(unittest.mock.MagicMock):
#     """Mock the daq config: add path to local .h and load .dll files"""
#
#     dot_h_file = os.path.join(_files_path, "NIDAQmx.h")
#
#     def get_lib(*args, **kwargs):
#         """Pass in local .dll to generate DAQ functions"""
#         sys.path.append(_files_path)
#         os.environ["PATH"] = _files_path + ";" + os.environ["PATH"]
#         dll = os.path.join(_files_path, "nicaiu.dll")
#         DAQlib = ctypes.WinDLL(dll)
#         DAQlib_variadic = ctypes.CDLL(dll)
#         return DAQlib, DAQlib_variadic
#
# def test_daq_driver_import():
#     # Mock the config - point to local .h and .dll
#     sys.modules["PyDAQmx.DAQmxConfig"] = MockDAQConfig()
#     import fixate.drivers.daq


# Loading Pydaqmx will fail with NotImplementedError if the .h file is not found
# and an OSError if loading the .dll fails
@pytest.mark.xfail(
    raises=(OSError, NotImplementedError), reason="Requires DAQ DLL and .h"
)
def test_daq_driver_import():
    import fixate.drivers.daq


# NOTE: our ftdi library raises an import error if loading .dll failes
# This is masking a good portion of what we are trying to test.
@pytest.mark.xfail(raises=ImportError, reason="Requires FTDI DLL")
def test_ftdi_driver_import():
    import fixate.drivers.ftdi
