import cmd2
import argparse
import pyvisa
import json
import copy
import platformdirs
from shutil import copy2
from pathlib import Path
from cmd2.ansi import style, Fg
from fixate.drivers.pps.bk_178x import BK178X
from pyvisa.errors import VisaIOError
import fixate.config

"""
fxconfig is a configuration utility that helps find connected instruments and add them to fixate's driver
configuration file.

Commands
========
fx> list existing                           # show the entries from config file
fx> list visa                               # show resources returned by visa_resources()
fx> list updated                            # show what will be saved modified state
fx> delete                                  # print the updated config and prompt for an entry to delete
fx> add visa serial <port>                  # Only works with default baud rate of 9600
fx> add visa tcp <host | ip address>
fx> add serial <port> <baudrate>            # only works for BK precision power supply at the moment.
fx> add visa usb                            # print numbered list of resources and user can enter a number.
fx> test existing                           # idn everything in existing config and report
fx> test updated                            # idn everything in updated config and report
fx> save                                    # replace existing with updated. existing will be first copied to *.bak
fx> open <path>                             # default to the path for the active environment
fx> new <path>                              # like open, but creates a new file that didn't exist. Error if file exists

"""

# TODO: Prevent writing duplicate to the config.


choices = ["existing", "updated", "visa"]
# create the top-level parser for the base command
list_parser = argparse.ArgumentParser(prog="list")
list_parser.add_argument("type", choices=choices)

test_parser = argparse.ArgumentParser(prog="test")
test_parser.add_argument("type", choices=choices)

add_parser = argparse.ArgumentParser(prog="add")
add_subparsers = add_parser.add_subparsers(title="add command")

add_visa_parser = add_subparsers.add_parser("visa")
add_serial_parser = add_subparsers.add_parser("serial")

add_visa_subparsers = add_visa_parser.add_subparsers()
add_visa_serial_parser = add_visa_subparsers.add_parser("serial")
add_visa_tcp_parser = add_visa_subparsers.add_parser("tcp")
add_visa_usb_parser = add_visa_subparsers.add_parser("usb")

add_visa_serial_parser.add_argument("port")
add_visa_serial_parser.add_argument("--baudrate")

add_visa_tcp_parser.add_argument("ipaddr")

add_serial_parser.add_argument("port")
add_serial_parser.add_argument("baudrate")


class FxConfigError(Exception):
    pass


class FxConfigCmd(cmd2.Cmd):
    prompt = "fx>"

    def __init__(self):
        super().__init__()
        self.config_file_path = None
        self.existing_config_dict = None
        self.updated_config_dict = None

        # Enable file-system path completion for the save and open commands
        self.complete_save = self.path_complete
        self.complete_open = self.path_complete

    def postloop(self):
        # Print a new line so the shell prompt get printed on a it's own line after we exit
        self.poutput("")

    @cmd2.with_argparser(add_parser)
    def do_add(self, args):
        args.func(self, args)

    def _do_add_visa_tcp(self, args):
        # TODO: Extend the optional parameter to allow port & SOCKET mode to be specified
        resource_name = "TCPIP0::{}::INSTR".format(args.ipaddr)
        self.poutput("Adding '{}'.".format(resource_name))

        try:
            idn = visa_id_query(resource_name)
        except Exception as e:
            self.perror("instrument not found")
            self.perror(e)
        else:
            self.updated_config_dict["INSTRUMENTS"]["visa"].append(
                [idn.strip(), resource_name]
            )

    def _do_add_visa_serial(self, args):
        resource_name = "ASRL{}::INSTR".format(args.port)
        self.poutput("Attempting to add '{}'.".format(resource_name))

        try:
            idn = visa_id_query(resource_name)
        except Exception as e:
            self.perror("instrument not found")
            self.perror(e)
        else:
            self.updated_config_dict["INSTRUMENTS"]["visa"].append(
                [idn.strip(), resource_name]
            )

    def _do_add_usb(self, args):
        rm = pyvisa.ResourceManager()
        resource_list = [x for x in rm.list_resources() if x.startswith("USB")]
        if len(resource_list) > 0:
            for i, resource_name in enumerate(resource_list):
                self.poutput("{}: {}".format(i + 1, resource_name))
            self.poutput("Select an interface to add")
            selection = input()
            selection = int(selection) - 1
            if 0 <= selection < len(resource_list):
                resource_name = resource_list[selection]
                self.updated_config_dict["INSTRUMENTS"]["visa"].append(
                    [visa_id_query(resource_name).strip(), resource_name]
                )
                self.poutput("'{}' added to config.".format(resource_name))
            else:
                self.poutput("Selection not valid")
        else:
            self.poutput("VISA found no USB instruments")

    def _do_add_serial(self, args):
        idn = serial_id_query(args.port, args.baudrate)
        self.updated_config_dict["INSTRUMENTS"]["serial"][args.port] = [
            idn,
            args.baudrate,
        ]

    add_visa_tcp_parser.set_defaults(func=_do_add_visa_tcp)
    add_visa_serial_parser.set_defaults(func=_do_add_visa_serial)
    add_visa_usb_parser.set_defaults(func=_do_add_usb)
    add_serial_parser.set_defaults(func=_do_add_serial)

    @cmd2.with_argparser(list_parser)
    def do_list(self, args):
        """Display either existing, visa or updated instrument list."""

        if args.type == "existing":
            self._print_config_dict(self.existing_config_dict)

        elif args.type == "updated":
            self._print_config_dict(self.updated_config_dict)

        elif args.type == "visa":
            self.poutput("Resources detected by VISA")
            for resource_name in pyvisa.ResourceManager().list_resources():
                self.poutput(resource_name)
        else:
            raise Exception("we shouldn't have gotten here")

    @cmd2.with_argparser(test_parser)
    def do_test(self, args):
        if args.type == "existing":
            self._test_config_dict(self.existing_config_dict)

        elif args.type == "updated":
            self._test_config_dict(self.updated_config_dict)

        elif args.type == "visa":
            for visa_resource_name in pyvisa.ResourceManager().list_resources():
                try:
                    new_idn = visa_id_query(visa_resource_name)
                except (VisaIOError, FxConfigError):
                    self._test_print_error(
                        visa_resource_name, "Error opening or responding to IDN"
                    )
                else:
                    self._test_print_ok(visa_resource_name, new_idn.strip())

        else:
            raise Exception("we shouldn't have gotten here")

    def do_save(self, line=None):
        """Save over the existing config file with updated."""
        if line:
            config_file_path = line
        elif self.config_file_path:
            config_file_path = self.config_file_path
        else:
            config_file_path = None

        if not config_file_path:
            self.perror("No existing config loaded or path to save supplied")
        else:
            print("saving to {}".format(config_file_path))
            backup_path = backup_file(config_file_path)

            try:
                with open(config_file_path, "w") as config_file:
                    json.dump(
                        self.updated_config_dict, config_file, sort_keys=True, indent=4
                    )
            except Exception as e:
                self.perror(e)
                if backup_file:
                    backup_path.replace(config_file_path)
                raise

    def do_open(self, line):
        """
        Open config file

        """
        if line:
            config_file_path = line
        else:
            config_file_path = fixate.config.INSTRUMENT_CONFIG_FILE

        self._load_config_into_dict(config_file_path)

    def _load_config_into_dict(self, config_file_path):

        with open(config_file_path, "r") as config_file:
            self.existing_config_dict = json.load(config_file)

        # Ensure our config has the bare minimum { "INSTRUMENTS": {"visa":[], "serial":{}}}
        instruments_dict = self.existing_config_dict.setdefault("INSTRUMENTS", {})
        instruments_dict.setdefault("visa", [])
        instruments_dict.setdefault("serial", {})

        # create a copy of the config that can be edited
        self.updated_config_dict = copy.deepcopy(self.existing_config_dict)
        self.config_file_path = config_file_path
        self.poutput("Config loaded: {}".format(self.config_file_path))

    def do_new(self, line):
        """
        Create a new config file. Same basic operation as open.
        """
        if line:
            config_file_path = Path(line)
        else:
            config_file_path = fixate.config.INSTRUMENT_CONFIG_FILE

        if config_file_path.exists():
            raise Exception("Path '{}' already exists".format(config_file_path))
        else:
            config_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file_path, "w") as config_file:
                config_file.write(
                    "{}"
                )  # bare minimum valid json. _load_config_into_dict will do the rest.
        self._load_config_into_dict(config_file_path)

    def do_delete(self, line):
        config_dict = self.updated_config_dict
        delete_list = [None]  # ("visa", index) or ("serial", key)
        delete_index = 1
        for i, visa_instrument in enumerate(config_dict["INSTRUMENTS"]["visa"]):
            self.poutput(
                "{}: VISA || {} || {}".format(
                    delete_index, visa_instrument[1].strip(), visa_instrument[0].strip()
                )
            )
            delete_list.append(("visa", i))
            delete_index += 1

        for com_port, parameters in config_dict["INSTRUMENTS"]["serial"].items():
            self.poutput(
                "{}: SERIAL || {} || {}".format(delete_index, com_port, str(parameters))
            )
            delete_list.append(("serial", com_port))
            delete_index += 1

        self.poutput("Select an interface to delete or x to cancel")
        selection = int(input())
        if selection != "x":
            entry_type, index = delete_list[selection]
            del config_dict["INSTRUMENTS"][entry_type][index]

    def _print_config_dict(self, config_dict):
        for visa_instrument in config_dict["INSTRUMENTS"]["visa"]:
            self.poutput(
                "VISA || "
                + visa_instrument[1].strip()
                + " || "
                + visa_instrument[0].strip()
            )

        for com_port, parameters in config_dict["INSTRUMENTS"]["serial"].items():
            self.poutput("SERIAL || " + com_port + " || " + str(parameters))

    def _test_print_error(self, name, msg):
        self.poutput(style("ERROR: ", fg=Fg.RED), end="")
        self.poutput(style(str(name), fg=Fg.CYAN), end="")
        self.poutput(" - {}".format(msg))

    def _test_print_ok(self, name, msg):
        self.poutput(style("OK: ", fg=Fg.GREEN), end="")
        self.poutput(style(str(name), fg=Fg.CYAN), end="")
        self.poutput(" - {}".format(msg))

    def _test_config_dict(self, config_dict):
        visa_resources = config_dict["INSTRUMENTS"]["visa"]
        serial_resources = config_dict["INSTRUMENTS"]["serial"]
        for idn, visa_resource_name in visa_resources:
            try:
                new_idn = visa_id_query(visa_resource_name)
            except (VisaIOError, FxConfigError):
                self._test_print_error(
                    visa_resource_name, "Error opening or responding to IDN"
                )
            except Exception as e:
                self.perror(e)
            else:
                if new_idn.strip() == idn.strip():
                    self._test_print_ok(visa_resource_name, idn.strip())
                else:
                    self._test_print_error(
                        visa_resource_name, "IDN Response does not match"
                    )

        for port, params in serial_resources.items():
            idn, baudrate = params
            try:
                new_id = serial_id_query(port, baudrate)
            except Exception as e:
                self._test_print_error(
                    e, "Error opening port '{}' or responding to ID query".format(port)
                )
            else:
                if new_id.strip() == idn.strip():
                    self._test_print_ok(port, str(params))
                else:
                    self.pfeedback("{} || {}".format(new_id, idn))
                    self._test_print_error(port, "ID query does not match")


# Stolen from discover.py. This should probably get consolidated back there,
# but I want to avoid messing with the internals for now.
def visa_id_query(visa_resource_name):
    """
    Attempt to open `visa_resource_name` and if successful, send an *IDN? command. Return
    the result of the idn command as a string.
    :param visa_resource_name:
    :return:
    """
    instr = pyvisa.ResourceManager().open_resource(visa_resource_name, query_delay=0.1)
    # 1 s timeout is overly conservative. But if we call clear() that can take a while for some instruments
    instr.timeout = 1000
    # instr.clear()
    resp = instr.query("*IDN?")

    if resp:
        instr.close()
        return resp.strip()

    # At least one instrument (Siglent SPD3303X power supply) only responds
    # when the line termination is set to \n
    instr.read_termination = "\n"
    instr.write_termination = "\n"

    resp = instr.query("*IDN?")

    if resp:
        instr.close()
        return resp.strip()

    raise FxConfigError(
        "Resource '{}' didn't respond to an IDN command".format(visa_resource_name)
    )


def serial_id_query(port, baudrate):
    """
    The only serial type instrument we use is the BK Precision 178x. So we just going to hard code
    calling the identity method on that class.
    :return:
    """
    pps = BK178X(port)
    pps.baud_rate = baudrate  # baud_rate property implementation has the side effect of opening the port.
    return pps.identify(as_string=True)


def backup_file(file_path):
    """
    Create a backup of `file_path` in the same directory. Appends ".bak" to the file name.
    :param file_path:
    :return: Pathlib.Path object which is the path of the new file
    """
    backup_path = Path(file_path).with_suffix(".json.bak")
    file_path = Path(file_path)
    if file_path.exists():
        copy2(file_path, backup_path)
    else:
        backup_path = None
    return backup_path


def main():
    app = FxConfigCmd()
    app.cmdloop()
