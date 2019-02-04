import inspect
import os
import sys
import time
import re

from pyvisa.constants import VI_ERROR_TMO
from visa import VisaIOError
import serial.tools.list_ports
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
        # importlib.machinery.SourceFileLoader(module, path_to_module).load_module()
    except Exception as e:
        pass
        # print(e)
        # print("Import Error: {}".format(module))
    else:
        mod = sys.modules[module]
        return inspect.getmembers(mod, inspect.isclass)
    return []


def _visa_find_instruments_from_serial_number(resources, serial_numbers):
    resp_set = set([])
    for resource in resources:
        for serial_number in serial_numbers:
            if serial_number in resource:
                resp_set.add(resource)
    return resp_set


def open_visa_instrument(instr_type, restrictions=None):
    """open_visa_instrument implements the  public api for each of the drivers for discovering and opening a connection
    :param instr_type:
    The abstract base class to implement
    :param restrictions:
    A dictionary containing the technical specifications of the required equipment
    :return:
    A instantiated class connected to a valid dmm
    """
    # All config values for implemented instruments should be called
    instruments = fixate.config.INSTRUMENTS.get("visa", None)
    discover_called = False
    if not instruments:
        # All discovery methods for implemented instruments should be called
        discover_visa()
        discover_called = True
    instruments = filter_connected(fixate.config.INSTRUMENTS, fixate.config.DRIVERS.get(instr_type, {}))
    # This is where the restrictions would come in
    if instruments:
        for instr in instruments:
            return instruments[instr]
    elif discover_called is False:
        discover_visa()
        instruments = filter_connected(fixate.config.INSTRUMENTS, fixate.config.DRIVERS.get(instr_type, {}))
        for instr in instruments:
            return instruments[instr]

    raise InstrumentNotConnected("No valid {} found".format(instr_type))


filters = {"serial_numbers": _visa_find_instruments_from_serial_number}


def _visa_get_instruments(queries):
    """
    Returns all instruments that satisfy the filter criteria
    If none provided then all instruments are returned
    :param resource_manager:
        Visa Resource Manager
    :param filters:
        Dictionary of values used to find instrument based on information provided
        eg.
        Filters instruments detected by serial numbers in the set
        {"serial_numbers":{'DG1D141301277', 'DG1D141401373'}}
        Filters instruments detected by model number from the Identification Call to the Instrument "*IDN?"
        {"model": "DG1022"}
        Filters instruments detected by brand from the Identification Call to the Instrument "*IDN?"
        {"brand": "RIGOL"}
        Returns first instrument detected by alias
        {"alias": "COM1"}
        Returns first instrument by Instr_Interface
        {"interface_type": "Instr_Interface.USB"}
    :return:
    set of items identified by resource that fit the filter
    """
    resources = set(fixate.config.RESOURCES["VISA_RESOURCE_MANAGER"].list_resources())
    for query in queries:
        filter_handler = filters.get(query, None)
        if filter_handler:
            filtered_results = filter_handler(resources.copy(), queries[query])
            resources = resources.intersection(filtered_results)
    return list(resources)


def _visa_get_instrument(queries):
    """
    :param resource_manager:
    :param queries:
        queries based on filter_instruments parameters
    :return:
    """
    resources = _visa_get_instruments(queries)
    if len(resources) == 1:
        return resources
    if len(resources) == 0:
        return None
    if len(resources) > 1:
        raise Exception("Too many resources discovered based on queries")


def _visa_id_query(instrument):
    instr = fixate.config.RESOURCES["VISA_RESOURCE_MANAGER"].open_resource(instrument, query_delay=0.1)
    try:
        instr.timeout = 100
        instr.clear()
        resp = instr.query("*IDN?")

        if resp:
            instr.close()
            del instr
            return [resp, instrument]

        instr.read_termination = '\n'
        instr.write_termination = '\n'

        resp = instr.query("*IDN?")

        if resp:
            instr.close()
            del instr
            return [resp, instrument]
        return [False, instrument]

    except VisaIOError as e:
        if e.error_code != VI_ERROR_TMO:
            """
            Visa timeout errors on id query are usually instruments in use or device such as FTDI that are not valid
            Visa instruments yet pyvisa seems to think that they are
            """
            # TODO Should be logged
            # print(e)
        return [False, instrument]


def discover_visa():
    """
    Not implemented
    :return:
    """
    rm = fixate.config.RESOURCES["VISA_RESOURCE_MANAGER"]
    # BUG - multi processing causes the visa library to give a busy signal when discovering for a second time.
    # related to https://github.com/hgrecco/pyvisa/issues/74
    # Issue has been resolved for threading in the git version. Don't use threading or multiprocessing until pyvisa 1.6
    # Using threadpool works but invokes a warning. Only use if discovery is too slow
    # UserWarning: Warning filter not found removefilter(action, message, category, module, lineno, append)
    # p = Pool(10)
    # named_resources = p.map(_visa_id_query, rm.list_resources())
    # TODO Wrap in exception handling
    visa_resources = []
    for resource in rm.list_resources():
        if "ASRL" in resource:
            # We don't want to autodiscover serial devices as random data on some serial lines can cause problems
            continue
        ident = _visa_id_query(resource)
        if ident[0]:
            visa_resources.append(ident)
    if fixate.config.INSTRUMENTS.get("visa", []):
        for inst in visa_resources:
            if inst not in fixate.config.INSTRUMENTS["visa"]:
                fixate.config.INSTRUMENTS["visa"].append(inst)
    else:
        fixate.config.INSTRUMENTS["visa"] = visa_resources
    return visa_resources


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
