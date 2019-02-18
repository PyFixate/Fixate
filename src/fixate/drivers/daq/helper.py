from abc import ABCMeta
import fixate.config


def open():
    """Open is the public api for the daq driver for discovering and opening a connection
    to a valid daq.
    At the moment opens just instantiates the DAQmx Driver
    :param restrictions:
    A dictionary containing the technical specifications of the required equipment
    :return:
    A instantiated class connected to a valid daq
    """
    for daq, cls in fixate.config.DRIVERS["DAQ"]:
        if daq == 'DaqMx':
            return cls()


class DAQ(metaclass=ABCMeta):
    REGEX_ID = None
