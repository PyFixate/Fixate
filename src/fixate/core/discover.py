import inspect
import os
import sys
import re

from visa import VisaIOError
import fixate.config
from fixate.drivers import ftdi
from fixate.core.exceptions import InstrumentNotConnected

pkgname = 'fixate'


def discover_classes():
    # Broken if pkgname occurs with other characters in the same step in path
    path = os.path.realpath(__file__).split(pkgname)

    if len(path) > 2:
        new_path = ''
        for pth in path:
            if pth:
                new_path += os.path.join(pth, pkgname)
        path = new_path
    elif len(path) == 2:
        pass
    else:
        raise OSError("Cannot Find Parent Package {}".format(pkgname))

    path = os.path.join(path[0], pkgname)
    pkg_cnt = 0
    for root, dirs, files in os.walk(path):
        for _file in files:
            if _file.endswith('.py'):
                _file.replace('.py', '')
                module_path = root.split(path)[1].split('\\')
                module_path[0] = pkgname
                module_path.append(_file.replace('.py', ''))
                module_path = '.'.join(module_path)
                for cls in _classes_in_module(module_path, os.path.join(root, _file)):
                    # print(cls)
                    yield cls
        pkg_cnt += 1


def discover_sub_classes(sub_class_match):
    for cls in fixate.config.CLASS_LIST:
        if issubclass(cls[1], sub_class_match):
            # getmro looks for the inheritance.
            # The leftmost mro return is the actual class. If it is the search class then we don't want it
            if inspect.getmro(cls[1])[0] != sub_class_match:
                yield cls


def _classes_in_module(module, path_to_module):
    try:
        __import__(module)
    except Exception as e:
        return []
    mod = sys.modules[module]
    return inspect.getmembers(mod, inspect.isclass)


def open_visa_instrument(instr_type, restrictions=None):
    """open_visa_instrument implements the  public api for each of the drivers for discovering and opening a connection
    :param instr_type:
    The abstract base class to implement
    :param restrictions:
    A dictionary containing the technical specifications of the required equipment
    :return:
    A instantiated class connected to a valid dmm
    """
    instruments = filter_connected(fixate.config.INSTRUMENTS, fixate.config.DRIVERS.get(instr_type, {}))
    if instruments:
        for instr in instruments:
            return instruments[instr]
    raise InstrumentNotConnected("No valid {} found".format(instr_type))


def discover_ftdi():
    ftdi.create_device_info_list()
    devices = ftdi.get_device_info_list()
    ftdi_resources = []
    for dev in devices:
        ftdi_resources.append(dev)
    return ftdi_resources


def filter_connected(instruments, classes):
    """Iterates through a list of connected equipment and attempts to detect if they are matched to the given classes
    :return:
    """
    rm = fixate.config.RESOURCES["VISA_RESOURCE_MANAGER"]
    result = {}
    for cls_name, cls in classes:
        if cls.INSTR_TYPE == 'VISA':
            for instr_id, instr_interface in instruments.get("visa", []):
                # In future make it a proper regex search rather than a straight string search
                if re.search(cls.REGEX_ID, instr_id):
                    try:
                        result[cls_name] = cls(rm.open_resource(instr_interface))
                    except VisaIOError:
                        pass
        if cls.INSTR_TYPE == 'SERIAL':
            for com_port, info in instruments.get("serial", {}).items():
                instr_id, baud_rate = info
                if re.search(cls.REGEX_ID, instr_id):
                    try:
                        result[cls_name] = cls(com_port)
                        result[cls_name].baud_rate = baud_rate
                    except Exception as e:
                        pass
    return result
