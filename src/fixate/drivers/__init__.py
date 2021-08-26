try:
    from typing import Protocol
except ImportError:
    # Protocol added in python 3.8
    from typing_extensions import Protocol

import pubsub.pub


class InstrumentNotFoundError(Exception):
    pass


class DriverProtocol(Protocol):
    REGEX_ID: str

    def get_identity(self) -> str:
        """Query the instrument for it identity.

        For visa instruments, this is generally the results of the idn? command.
        For other drivers, it can be any meaningful id. Where possible it should
        include a unique identifier like a serial number.
        """
        ...


def log_instrument_open(instrument: DriverProtocol) -> None:
    """"""
    instrument_name = type(instrument).__name__
    pubsub.pub.sendMessage(
        "driver_open",
        instr_type=instrument_name,
        identity=instrument.get_identity(),
    )


#######################################################################################
# Pretty sure that nothing below here is actually used...
from inspect import isfunction  # noqa
from functools import wraps, partial  # noqa


def _ensure_connected(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if not self.is_connected:
            self.connect()
        return f(self, *args, **kwargs)

    return wrapper


class DriverMeta(type):
    def __new__(mcs, clsname, bases, dct):
        for name, attr in dct.items():
            if isfunction(attr):
                if (
                    name.startswith("_")
                    or name in ("connect", "disconnect")
                    or name in dct.get("_connect_ignore", [])
                ):
                    # Don't wrap these functions with _ensure_connected
                    continue
                dct[name] = _ensure_connected(attr)
        return super().__new__(mcs, clsname, bases, dct)


class Driver(metaclass=DriverMeta):
    """
    Driver base class for creating self connecting drivers.
    connect is called whenever a public method api call is made and is_connected = False
    ie.
    def _my_func(self):
        pass
    will not call connect as it is a private function by convention whereas
    def my_func(self):
        pass
    will.
    Exceptions to this rule are connect, disconnect and function strings as can be defined by creating a list called
    _connect_ignore on class definition
    """

    is_connected = False

    # _connect_ignore = ['ignored_func1','ignored_func2'] # Set this parameter in derived class definition if required
    def connect(self):
        """
        Override connect function but ensure that self.is_connected is set if connected or an exception occurs if
        connection could not be established
        :return:
        """
        print("Connected to {}".format(self.__class__.__name__))
        self.is_connected = True

    def disconnect(self):
        """
        Override disconnect function but ensure that self.is_connect is set to False
        :return:
        """
        print("Disconnected from {}".format(self.__class__.__name__))
        self.is_connected = False


class DriverManager:
    """
    Driver manager allows for multiple drivers to be collated and managed from a central location.
    Drivers must be either derived from the driver class or must implement a the functions
    def connect(self): # No Parameters
    def disconnect(self): # No Parameters
    and have an attribute
    is_connected (Boolean)
    """

    def __init__(self, **kwargs):
        self.drivers = {}
        self._cleanup = []
        self.add_drivers(**kwargs)

    def add_drivers(self, **kwargs):
        """
        :param kwargs: kwargs of <id>=<driver>.
        Eg.
        >>>class MyDmm(Driver):
        >>>    def hello(self):
        >>>        print("World")
        >>>dm = DriverManager(dmm=MyDmm())
        >>>dm.dmm.hello()
        World
        :return:
        """
        self.drivers.update(kwargs)

    def remove_drivers(self, *ids):
        """
        :param ids: Drivers to be removed
        eg.
        >>>class MyDmm(Driver):
        >>>    def hello(self):
        >>>        print("Hello World")
        >>>dm = DriverManager(dmm=MyDmm(), dmm2=MyDmm())
        >>>dm.dmm.hello()
        Hello World
        >>>dm.remove_drivers('dmm', 'dmm2')
        >>>dm.dmm.hello()
        AttributeError: 'DriverManager' object has no attribute 'dmm'
        :return:
        """
        for id in ids:
            drv = self.drivers.get(id)
            if drv:
                drv.disconnect()
                del self.drivers[id]

    def register_initialisation(self, id, init_funcs):
        # TODO Needed? Should this just be done on instantiation of the driver class?
        pass

    def cleanup_register(self, func, *args, **kwargs):
        """
        Registers a cleanup function to be executed on cleanup_execute call.
        The registered functions are executed in the order they are added via this function.
        Use the cleanup_clear to remove all the registered cleanup functions
        :param func: function as directly refrenced. eg. dm.dmm.disconnect
        :param args: The arguments that should be called with the func
        :param kwargs: The keyword arguments that should be called with the func
        :return: None
        """
        self._cleanup.append(partial(func, *args, **kwargs))

    def cleanup_execute(self):
        for partial_func in self._cleanup:
            partial_func()

    def cleanup_clear(self):
        self._cleanup.clear()

    def __getattr__(self, attr):
        driver = self.drivers.get(attr)
        if driver is None:
            return self.__getattribute__(attr)  # Should Raise Attribute Error
        return driver


if __name__ == "__main__":

    class MyDmm(Driver):
        def __init__(self):
            self.subcls = OtherClass()

        def hello(self):
            """
            Doc for hello
            :return:
            """
            print("Hello World")

        def _unconnected_hell(self):
            print("Goodbye Cruel World")

    class OtherClass:
        def another_func(self):
            print("Other func")

    dm = DriverManager(dmm=MyDmm())
    print("Driver Manager Instantiated")
    dm.dmm.hello()
    dm.dmm.disconnect()
    dm.dmm._unconnected_hell()
    dm.dmm.subcls.another_func()
    dm.dmm.hello()
    dm.dmm.disconnect()
    dm.dmm.hello()
    dm.dmm.hello()
    help(dm.dmm.hello)
    dm.dmm.disconnect()
    "World"
    # dm.remove_drivers(['dmm'])
    # dm.dmm.hello()
