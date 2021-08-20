import time
import sys
import warnings
from math import ceil, log
from fixate.core.common import bits, deprecated


class MuxWarning(Warning):
    pass


class VirtualAddressMap:
    """
    The supervisor loops through the attached virtual multiplexers each time a mux update is triggered.
    """

    def __init__(self):
        self.address_handlers = []
        self.virtual_pin_list = []
        self._virtual_pin_values = 0b0
        self._virtual_pin_values_active = 0b0
        self._virtual_pin_values_clear = 0b0
        self.mux_assigned_pins = {}
        self._clearing_time = 0

    @property
    def pin_values(self):
        return list(
            zip(
                self.virtual_pin_list,
                bits(
                    self._virtual_pin_values_active,
                    num_bits=len(self.virtual_pin_list),
                    order="LSB",
                ),
            )
        )

    def active_pins(self):
        return [
            (
                self.virtual_pin_list[pin],
                self.mux_assigned_pins[self.virtual_pin_list[pin]],
            )
            for pin, value in enumerate(
                bits(
                    self._virtual_pin_values_active,
                    num_bits=len(self.virtual_pin_list),
                    order="LSB",
                )
            )
            if value
        ]

    def install_address_handler(self, handler):
        """
        :param handler
        An address handler class that has:
        the pin outs defined as obj.pin_values as a list of identifiers for the outputs.
        the update method that accepts a binary number to update the pins as obj.update(<int>)
        the defaults method that updates the pins into the default state as obj.defaults().
        """
        # Checks
        common_elements = set(handler.pin_list).intersection(set(self.virtual_pin_list))
        if common_elements:
            raise ValueError(
                "Duplicate pin identifiers not allowed\n{}".format(
                    ", ".join(common_elements)
                )
            )

        self.virtual_pin_list.extend(handler.pin_list)
        self.address_handlers.append((len(self.virtual_pin_list), handler))

    def install_multiplexer(self, mux):
        """
        All address handlers that are relevant to the multiplexer must be defined before calling this function.
        :param mux:
        A multiplexer with a list of identifiers that should be found in the virtual pin list.
        These identifiers are then converted into a mask to use in the virtual address map.
        The update callback function is then added to the object so that the object can trigger an update routine on
        the virtual address map
        """
        mux.pin_mask = []
        for itm in mux.pin_list:
            if itm in self.mux_assigned_pins:
                warnings.warn(
                    "Pin {} in {} already assigned in {}".format(
                        itm, mux, self.mux_assigned_pins[itm]
                    ),
                    MuxWarning,
                )
            try:
                mux.pin_mask.append(self.virtual_pin_list.index(itm))
            except ValueError as e:
                raise ValueError(
                    "Multiplexer pin {} not found in Virtual Address Map".format(itm)
                ) from e
            self.mux_assigned_pins[itm] = mux
        mux.update_callback = self.update_pin_values
        mux._clear_callback = self.update_clearing_pin_values

    def update_defaults(self):
        """
        Writes the initialisation values to the address handlers as the default values set in the handlers
        """
        pin_values = []
        self._virtual_pin_values = 0
        for _, handler in self.address_handlers:
            pin_values.extend(handler.defaults())
        self.update_pins_by_name(pin_values)

    def update_output(self):
        """
        Iterates through the address_handlers and send a bit shifted and masked value of the _virtual_pin_values
        relevant to the address handlers update function.
        :return:
        """
        start_addr = 0x00
        for addr, handler in self.address_handlers:
            shifted = self._virtual_pin_values >> start_addr
            mask = (1 << (addr - start_addr)) - 1
            handler.update_output(shifted & mask)
            start_addr = addr

    def update_clearing_output(self):
        start_addr = 0x00
        for addr, handler in self.address_handlers:
            shifted = self._virtual_pin_values_clear >> start_addr
            mask = (1 << (addr - start_addr)) - 1
            handler.update_output(shifted & mask)
            start_addr = addr

    def update_input(self):
        """
        Iterates through the address_handlers and reads the values back to update the pin values for the digital inputs
        :return:
        """
        start_addr = 0x00
        for addr, handler in self.address_handlers:
            values = handler.update_input()
            if values is not None:  # Handler can return valid input values
                pin_values = []
                for index, b in enumerate(
                    bits(values, num_bits=len(handler.pin_list), order="LSB")
                ):
                    pin_values.append((index + start_addr, b))
                self.update_pin_values(pin_values, trigger_update=False)
            start_addr = addr

    def update_pin_values(self, values, trigger_update=True):
        """
        :param values: is a list of (index, value) tuples
        Takes the values list and sets the individual bits in _virtual_pin_values that correspond to the index, value
        pairs. Then calls the update_output function.
        """
        for index, value in values:
            # Get the mask
            mask = 1 << index
            # Clear bit
            self._virtual_pin_values &= ~mask
            if value:
                # Set bit
                self._virtual_pin_values |= mask
        if trigger_update:
            if self._virtual_pin_values_active == self._virtual_pin_values:
                pass  # No change in pins
            elif self._virtual_pin_values_clear == self._virtual_pin_values_active:
                # No clearing values required
                self.update_output()
            else:
                # Do clearing output before desired signals
                self.update_clearing_output()
                self._virtual_pin_values_active = self._virtual_pin_values_clear
                time.sleep(self._clearing_time)
                self.update_output()
            # As a trigger has occurred reset our values to match the virtual values and clearing time back to 0
            self._clearing_time = 0
            self._virtual_pin_values_active = self._virtual_pin_values
            self._virtual_pin_values_clear = self._virtual_pin_values

    def update_clearing_pin_values(self, values, clearing_time):
        """
        :param values: is a list of (index, value) tuples
        Takes the values list and sets the individual bits in _virtual_pin_values_clear that correspond to the
        index, value pairs. These values are then called using the logic
        1. Update clearing pin values
        2. Sleep for clearing time
        3. Update the new output
        This can be used for break before make logic in individual multiplexers
        :return:
        """
        self._clearing_time = max(self._clearing_time, clearing_time)
        for index, value in values:
            # Get the mask
            mask = 1 << index
            # Clear bit
            self._virtual_pin_values_clear &= ~mask
            if value:
                # Set bit
                self._virtual_pin_values_clear |= mask

    def update_pin_by_name(self, name, value, trigger_update=True):
        index = self.virtual_pin_list.index(name)
        self.update_pin_values([(index, value)], trigger_update)

    def update_pins_by_name(self, pins, trigger_update=True):
        pin_values = [
            (self.virtual_pin_list.index(name), value) for name, value in pins
        ]
        self.update_pin_values(pin_values, trigger_update)

    def __getitem__(self, item):
        self.update_input()
        return bool((1 << self.virtual_pin_list.index(item)) & self._virtual_pin_values)

    def __setitem__(self, key, value):
        index = self.virtual_pin_list.index(key)
        self.update_pin_values([(index, value)])


class AddressHandler:
    """
    :param pin_list: Iterable of pins (type string) that the AddressHandler handles
    :param defaults: Iterable of pins (type string subset of pin_list) that should default to high logic on reset
    """

    pin_list = ()
    pin_defaults = ()

    def update_output(self, value):
        pass

    def update_input(self):
        pass

    def defaults(self):
        """
        :return: [(<pin_name>, True),...] corresponding to the default pins that should be set high on reset
        """
        return [(pin, True) for pin in self.pin_defaults]


class VirtualMux:
    pin_list = []
    default_signal = ""
    state = ""
    state_update_time = time.time()
    clearing_time = 0

    def __call__(self, signal_output, trigger_update=True):
        self.multiplex(signal_output, trigger_update)

    def __init__(self):
        """
        :param pin_list:
         A list containing the virtual pins that need to be exercised by the address handlers.
         First element in the list is MSB and last element is LSB
         [MSB, x, y, z, LSB] of the address space.
        :return:
        """
        if self.pin_list is None:
            self.pin_list = []
        self.pin_mask = []
        self.signal_map = {}
        self._reserved_addr = set([])
        self.map_signals()

    def multiplex(self, signal_output, trigger_update=True):
        """
        Converts a desired signal into an address to parse to the VirtualAddressMap
        Updates the virtual address map with the values
        """
        if signal_output == "":
            virtual_address = 0
        else:
            try:
                virtual_address = self.signal_map[signal_output]
            except ValueError as e:
                raise ValueError(
                    "signal_output {} not found in multiplexer".format(signal_output)
                ) from e

        values = self._build_values_update(virtual_address)
        self.clear_callback()
        self.update_callback(values, trigger_update)
        if signal_output != self.state:
            self.state_update_time = time.time()
        self.state = signal_output

    def _build_values_update(self, virtual_address):
        values = []
        for index, b in enumerate(
            bits(virtual_address, num_bits=len(self.pin_list), order="LSB")
        ):
            try:
                values.append((self.pin_mask[index], b))
            except IndexError:
                # Should only ever happen in development
                sys.stderr("SIGNAL: {}".format(virtual_address))
                sys.stderr("PIN MASK: {}".format(self.pin_mask))
                sys.stderr("PIN LIST: {}".format(self.pin_list))
                raise
        return values

    def _clear_callback(self, values, clearing_time):
        """
        Callback function for setting the state the mux has during the clearing of relays Overridden by the the virtual
        address map.
        :return:
        """
        raise NotImplementedError(
            "Callback not set. Consider installing virtual mux into a virtual address map"
        )

    def clear_callback(self):
        """
        Callback function for setting the state the mux has during the clearing of relays
        Override this function to set up custom behaviors during the clearing of relays.
        For example. Setting all signals to off and then the new signal will cause the mux to act with a break before
        make multiplexer with a clearing time that is set at the JigDriver or VirtualAddressMap level.
        Must call to self._clear_callback to have any affect on the clearing state.
        The clearing_time sets the minimum time that the mux stays in the clearing state before moving to the desired
        signal state
        Usage:
        For setting all states to 0

        def clear_callback(self):
            values = self._build_values_update(0b0)
            self._clear_callback(values, self.clearing_time)

        For setting all states to a signal called "default"

        def clear_callback(self):
            virtual_address = self.signal_map["default"]
            values = self._build_values_update(virtual_address)
            self._clear_callback(values, self.clearing_time)

        :return:
        """

    def update_callback(self, values, trigger_update):
        raise NotImplementedError(
            "Callback not set. Consider installing virtual mux into a virtual address map"
        )

    def _check_duplicates(self, addr, value):
        if addr in self._reserved_addr:
            dup = "UNKNOWN"
            for k, v in self.signal_map.items():
                if addr == v:
                    dup = k
                    break
            raise ValueError(
                "Address 0b{:b} already in use\n{} is a duplicate of {}".format(
                    addr, value, dup
                )
            )
        self._reserved_addr.add(addr)

    def map_shifted(self, base_index, start_index, values):
        """
        Shifts the values for the sparse mapping of the signal map.
        :param base_index number to add to the index after the shifting. eg the default state of the values
        :param start_index the initial index that needs to be shifted
        """
        for index, value in enumerate(values):
            if value is None:
                continue
            addr = (index << start_index) + base_index
            self._check_duplicates(addr, value)
            self.signal_map[value] = addr

    def defaults(self):
        """
        Sets the default state of the multiplexer
        :return:
        """
        self.multiplex(self.default_signal)

    def map_single(self, value, *pin_names):
        """
        Maps a single value based on the pin names by bitwise OR on the shifted pins
        """
        if value is None:
            raise ValueError("map_single cannot be called with value as None")
        addr = 0
        for name in pin_names:
            try:
                addr |= 1 << self.pin_list.index(name)
            except ValueError as e:
                raise Exception(
                    'pin "{}" was not found in pin_list of VirtualMux {}'.format(
                        name, self.__class__
                    )
                ) from e
        self._check_duplicates(addr, value)
        self.signal_map[value] = addr

    def condensed_signal_map(self):
        binary_length = "0b{:0" + "{}".format(len(self.pin_list)) + "b}"
        return sorted(
            [(binary_length.format(ind), val) for val, ind in self.signal_map.items()]
        )

    def map_signals(self):
        """
        Override this method to map the signals in the signal map on initialisation
        """
        try:
            map_tree = self.map_tree
        except AttributeError:
            try:
                self.map_list
            except AttributeError:
                pass
            else:
                for signal in self.map_list:
                    self.map_single(*signal)
        else:
            self._map_tree(map_tree, 0, 0)

    def _map_tree(self, branch, base_offset, base_bits):
        """recursively add nested signal lists to the signal map.
        branch: is the current sub branch to be added. At the first call
        level, this would be initialised with self.map_tree. It can be
        any sequence, possibly nested.

        base_offset: should be the integer value of the address
        where the branch enters into the top level multiplexer.

        base_bits: At each call level, this represents the number
        of less significant address bits that are used to represent
        multiplexers higher up the chain.

        example:
        This shows 10 signal, routed through a number of multiplexers.
        Mux B and Mux B' are distinct, but address of common control
        signals. Mux C and Mux B/B' are nested to various levels into
        the final multiplexer Mux A.

        The pin_list defines the control signals from least to most significant
        The map_tree defines the signals into each multipler. Nesting containers
        reflects the nesting of mux's.
                                          __________
        a0-------------------------------|          |
                              ________   |          |
        a1_b0----------------|        |--|  Mux A   |
        a1_b1----------------| Mux B  |  |   4:1    |
        a1_b2----------------|  4:1   |  |          |
                     (None)--|_x3__x2_|  |          |
                                         |          |
                              ________   |          |
        a2_b0----------------|        |  |          |
                   _______   |        |--|          |------ Output
        a2_b1_c0--| Mux C |--| Mux B' |  |          |
        a2_b1_c1--|  2:1  |  |  4:1   |  |          |
                  |___x4__|  |        |  |          |
                             |        |  |          |
        a2_b2----------------|        |  |          |
        a2_b3----------------|        |  |          |
                             |_x3__x2_|  |          |
                                         |          |
        a3-------------------------------|          |
                                         |__x1__x0__|

        class Mux(VirtualMux):
            pin_list = ("x0", "x1", "x2", "x3", "x4")
            map_tree = ("a0",
                        (#a1
                            "a1_b0",
                            "a1_b1",
                            "a1_b2",
                            None,
                        ),
                        (#a2
                            "a2_b0",
                            (#b1
                                "a2_b1_c0",
                                "a2_b1_c1",
                            ),
                            "a2_b2",
                            "a2_b3",
                        ),
                        "a3"
                    )

        Alternatively:

        class Mux(VirtualMux):
            pin_list = ("x0", "x1", "x2", "x3", "x4")

            mux_c = ("a2_b1_c0", "a2_b1_c1")
            mux_b1 = ("a1_b0", "a1_b1", "a1_b2", None)
            mux_b2 = ("a2_b0", mux_c, "a2_b2", "a2_b3")

            map_tree = ("a0", mux_b1, mux_b2, "a3")

        Final mapping:
        addr    signal
        --------------
        0       a0
        1       a1_b0
        2       a2_b0
        3       a3
        4
        5       a1_b1
        6       a2_b1_c0
        7
        8
        9       a1_b2
        10      a2_b2
        11
        12
        13      (None)
        14      a2_b3
        15
        16
        17
        18
        19
        20
        21
        22      a2_b1_c1
        23
        24
        25
        26
        27
        28
        29
        30
        31

        For Multiplexers that depend on separate control pins, try using the shift_nested function to help
        with sparse mapping
                                          __________
        a0-------------------------------|          |
                              ________   |          |
        a1_b0----------------|        |--|          |
        a1_b1----------------| Mux B  |  |          |
        a1_b2----------------|  4:1   |  |          |
                     (None)--| x3  x2 |  |          |
                             |________|  |          |
                                         |  Mux A   |
        a2-------------------------------|   4:1    |
                              ________   |          |
        a3_c0----------------|        |--|          |
        a3_c1----------------| Mux C  |  |          |
        a3_c2----------------|  4:1   |  |          |
                     (None)--| x5  x4 |  |          |
                             |________|  |          |
                                         |__x1__x0__|

        class Mux(VirtualMux):
            pin_list = ("x0", "x1", "x2", "x3", "x4")

            mux_c = ("a3_c0", "a3_c1", "a3_c2", None)
            mux_b = ("a1_b0", "a1_b1", "a1_b2", None)

            map_tree = (
            "a0",
            mux_b,
            shift_nested(mux_c, [2]),  # 2 in indicative on how many pins to skip. This case is (x2, x3) from mux_b
            "a3")

        """
        for i, signal in enumerate(branch):
            current_index = (i * 1 << base_bits) + base_offset

            if isinstance(signal, str):
                # Add signal to out mapping
                self._check_duplicates(current_index, signal)
                self.signal_map[signal] = current_index
            elif signal is None:
                pass
            else:
                # We have a nested signal definition, so we recurse.
                # number of addr bits needed for the current branch:
                current_bits = int(ceil(log(len(branch), 2)))
                self._map_tree(signal, current_index, base_bits + current_bits)

    def __repr__(self):
        return self.__class__.__name__


def shift_nested(values, shift_arr):
    """
    :param values:
    The list/tuple of values that are desired in the nested list
    :param shift_arr:
    The list/tuple of the multiplexing values (eg 1 << value) to nest the list
    :return:
    Nested list with the values.

    :usage
    >>>shift_nested([1, 2, 3, 4, 5, 6, 7, 8], [3, 2])
    [[[1, 2, 3, 4, 5, 6, 7, 8], None, None, None], None, None, None, None, None, None, None]
    >>>shift_nested([1, 2, 3, 4, 5, 6, 7, 8], [2, 3])
    [[[1, 2, 3, 4, 5, 6, 7, 8], None, None, None, None, None, None, None], None, None, None]

    """
    ret_lst = values
    ret_type = "list"
    if isinstance(values, tuple):
        ret_type = "tuple"

    for itm in reversed(shift_arr):
        tmp_lst = [None for _ in range(1 << itm)]
        tmp_lst[0] = ret_lst
        if ret_type == "tuple":
            tmp_lst = tuple(tmp_lst)
        ret_lst = tmp_lst
    return ret_lst


class VirtualSwitch(VirtualMux):
    """
    A virtual switch is a multiplexer with a single pin. The multiplex function can accept
    either boolean values or the strings 'TRUE' and 'FALSE'. The vitual address used to switch
    can be defined as a list with the single element (as if it were a multiplexer) or by using
    the shorthand which is to define the pin_name attribute as a string.

    The switch method was included in the original definition. However it is more consistent with
    the VirtualMux base class to use the callable syntax on the switch object. It remains for
    backward compatibility.
    """

    pin_name = ""
    map_tree = ("FALSE", "TRUE")

    def multiplex(self, signal_output, trigger_update=True):
        if signal_output is True:
            signal = "TRUE"
        elif signal_output is False:
            signal = "FALSE"
        else:
            signal = signal_output
        super().multiplex(signal, trigger_update=trigger_update)

    def __init__(self, pin_name=None):
        if pin_name is None:
            pin_name = self.pin_name
        if not self.pin_list:
            self.pin_list = [pin_name]
        super().__init__()

    @deprecated
    def switch(self, value, trigger_update=True):
        if value not in [True, False]:
            raise ValueError("Virtual Switches only accept True or False")
        self.multiplex(value, trigger_update=trigger_update)


class TestAddressHandler(AddressHandler):
    def update_output(self, value):
        print("Updating from {}".format(self.__class__.__name__))
        print(
            *zip(
                self.pin_list, [b for b in bits(value, len(self.pin_list), order="LSB")]
            ),
            sep="\n"
        )


class RelayMatrixMux(VirtualMux):
    clearing_time = 0.01

    def clear_callback(self):
        virtual_address = self.signal_map.get(self.default_signal, 0b0)
        values = self._build_values_update(virtual_address)
        self._clear_callback(values, self.clearing_time)


class JigMeta(type):
    """
    usage:
    Metaclass for Jig Driver
    Dynamically adds multiplexers and multiplexer groups to the Jig Class definition
    """

    def __new__(mcs, clsname, bases, dct):
        muxes = dct.get("multiplexers", None)
        if muxes is not None:
            mux_dct = {mux.__class__.__name__: mux for mux in muxes}
            dct["mux"] = type("MuxController", (), mux_dct)
        return super().__new__(mcs, clsname, bases, dct)


class JigDriver(metaclass=JigMeta):
    """
    :attribute address_handlers: Iterable of Address Handlers
    [<Address_Handler_Instance1>,...
    "<Address_Handler_InstanceX>"]

    :attribute multiplexers: Iterable Virtual Muxes
    {<Mux_Instance1>,...
    "<Mux_InstanceX>}

    :attribute defaults: Iterable of the default pins to set high on driver reset
    """

    multiplexers = ()
    address_handlers = ()
    defaults = ()

    def __init__(self):
        super().__init__()
        self.virtual_map = VirtualAddressMap()
        for addr_hand in self.address_handlers:
            self.virtual_map.install_address_handler(addr_hand)
        for mux in self.multiplexers:
            self.virtual_map.install_multiplexer(mux)

    def __setitem__(self, key, value):
        self.virtual_map.update_pin_by_name(key, value)

    def __getitem__(self, item):
        return self.virtual_map[item]

    def active_pins(self):
        return self.virtual_map.active_pins()

    def reset(self):
        """
        Reset the multiplexers to the default values
        Raises exception if failed
        :return: None
        """
        self.virtual_map.update_defaults()  # TODO Test if this is required
        for _, mux in self.mux.__dict__.items():
            if isinstance(mux, VirtualMux):
                mux.defaults()

    def iterate_all_mux_paths(self):
        for _, mux in self.mux.__dict__.items():
            if isinstance(mux, VirtualMux):
                yield from self.iterate_mux_paths(mux)

    def iterate_mux_paths(self, mux):
        """
        :param mux: Multiplexer as an object
        :return: Generator of multiplexer signal paths
        """
        for pth in mux.signal_map:
            if pth is not None:
                mux(pth)
                yield "{}: {}".format(mux.__class__.__name__, pth)
        mux.defaults()
