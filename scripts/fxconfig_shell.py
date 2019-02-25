import cmd2
import argparse
import visa
import json
import copy
from fxconfig import backup_file, visa_id_query, FxConfigError, serial_id_query
from pyvisa.errors import VisaIOError


"""
Original plan is starting to become a mess. So explore an interactive shell instead

fxconfig <config file>

Commands
========
fx> list existing                           # show the entries from config file
fx> list visa                               # show resources returned by visa_resources()
fx> list updated                            # show what will be saved modified state
fx> add visa-serial <port> [<baudrate>]
fx> add visa-tcp <host | ip address>
fx> add serial-bk176x <port> <baudrate>
fx> add visa list                           # print numbered show resources and user can enter a number.
fx> test existing                           # idn everything in existing config and report
fx> test updated                            # idn everything in updated config and report
fx> save                                    # replace existing with updated. existing will be first copied to *.bak

nice to have:
fx> test visa serial <port> [<baudrate>]
fx> test visa tcp <host | ip address>
fx> test serial

"""

# TODO: Prevent writing duplicate to the config.

# I found these here: http://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html
# But surely there is a library or some other magic that can do this for us?
RED = "\u001b[31m"
CYAN = "\u001b[36m"
GREEN = "\u001b[32m"


choices=["existing", "updated", "visa"]
# create the top-level parser for the base command
list_parser = argparse.ArgumentParser(prog='list')
list_parser.add_argument('type', choices=choices)

test_parser = argparse.ArgumentParser(prog='test')
test_parser.add_argument('type', choices=choices)

add_parser = argparse.ArgumentParser(prog='add')
add_subparsers = add_parser.add_subparsers(title="add command")

add_visa_parser = add_subparsers.add_parser('visa')
add_serial_parser = add_subparsers.add_parser('serial')

add_visa_subparsers = add_visa_parser.add_subparsers()
add_visa_serial_parser = add_visa_subparsers.add_parser('serial')
add_visa_tcp_parser = add_visa_subparsers.add_parser('tcp')
add_visa_usb_parser = add_visa_subparsers.add_parser('usb')

add_visa_serial_parser.add_argument("port")
add_visa_serial_parser.add_argument("--baudrate")

add_visa_tcp_parser.add_argument("ipaddr")


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
            self.updated_config_dict["INSTRUMENTS"]["visa"].append([idn.strip(), resource_name])

    def _do_add_visa_serial(self, args):
        resource_name = "ASRL{}::INSTR".format(args.port)
        self.poutput("Attempting to add '{}'.".format(resource_name))

        try:
            idn = visa_id_query(resource_name)
        except Exception as e:
            self.perror("instrument not found")
            self.perror(e)
        else:
            self.updated_config_dict["INSTRUMENTS"]["visa"].append([idn.strip(), resource_name])

    def _do_add_usb(self, args):
        rm = visa.ResourceManager()
        resource_list = [x for x in rm.list_resources() if x.startswith("USB")]
        if len(resource_list) > 0:
            for i, resource_name in enumerate(resource_list):
                self.poutput("{}: {}".format(i+1, resource_name))
            self.poutput("Select an interface to add")
            selection = input()
            selection = int(selection) - 1
            if 0 <= selection < len(resource_list):
                resource_name = resource_list[selection]
                self.updated_config_dict["INSTRUMENTS"]["visa"].append([visa_id_query(resource_name).strip(), resource_name])
                self.poutput("'{}' added to config.".format(resource_name))
            else:
                self.poutput("Selection not valid")
        else:
            self.poutput("VISA found no USB instruments")

    add_visa_tcp_parser.set_defaults(func=_do_add_visa_tcp)
    add_visa_serial_parser.set_defaults(func=_do_add_visa_serial)
    add_visa_usb_parser.set_defaults(func=_do_add_usb)

    @cmd2.with_argparser(list_parser)
    def do_list(self, args):
        """Display either existing, visa or updated instrument list."""

        if args.type == "existing":
            self._print_config_dict(self.existing_config_dict)

        elif args.type == "updated":
            self._print_config_dict(self.updated_config_dict)

        elif args.type == "visa":
            self.poutput("Resources detected by VISA")
            for resource_name in visa.ResourceManager().list_resources():
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
            for visa_resource_name in visa.ResourceManager().list_resources():
                try:
                    new_idn = visa_id_query(visa_resource_name)
                except (VisaIOError, FxConfigError):
                    self._test_print_error(visa_resource_name, "Error opening or responding to IDN")
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
                with open(config_file_path, 'w') as config_file:
                    json.dump(self.updated_config_dict, config_file, sort_keys=True, indent=4)
            except Exception as e:
                self.perror(e)
                if backup_file:
                    backup_path.replace(config_file_path)
                raise

    def do_open(self, line):
        """Open config file"""
        config_file_path = line

        with open(config_file_path, 'r') as config_file:
            self.existing_config_dict = json.load(config_file)

        # create a copy of the config that can be edited
        self.updated_config_dict = copy.deepcopy(self.existing_config_dict)
        self.config_file_path = config_file_path
        self.poutput("Config loaded")

    def _print_config_dict(self, config_dict):
        for visa_instrument in config_dict["INSTRUMENTS"]["visa"]:
            self.poutput("VISA || " + visa_instrument[1].strip() + " || " + visa_instrument[0].strip())

        for com_port, parameters in config_dict["INSTRUMENTS"]["serial"].items():
            self.poutput("SERIAL || " + com_port + " || " + str(parameters))

    def _test_print_error(self, name, msg):
        self.poutput("ERROR: ", end="", color=RED)
        self.poutput(str(name), end="", color=CYAN)
        self.poutput(" - {}".format(msg))

    def _test_print_ok(self, name, msg):
        self.poutput("OK: ", end="", color=GREEN)
        self.poutput(str(name), end="", color=CYAN)
        self.poutput(" - {}".format(msg))

    def _test_config_dict(self, config_dict):
        visa_resources = config_dict["INSTRUMENTS"]["visa"]
        serial_resources = config_dict["INSTRUMENTS"]["serial"]
        for idn, visa_resource_name in visa_resources:
            try:
                new_idn = visa_id_query(visa_resource_name)
            except (VisaIOError, FxConfigError):
                self._test_print_error(visa_resource_name, "Error opening or responding to IDN")
            except Exception as e:
                self.perror(e)
            else:
                if new_idn.strip() == idn.strip():
                    self._test_print_ok(visa_resource_name, idn.strip())
                else:
                    self._test_print_error(visa_resource_name, "IDN Response does not match")

        for port, params in serial_resources.items():
            id, baudrate = params
            try:
                new_id = serial_id_query(port, baudrate)
            except Exception as e:
                self._test_print_error(e, "Error opening port '{}' or responding to ID query".format(port))
            else:
                if new_id.strip() == id.strip():
                    self._test_print_ok(port, str(params))
                else:
                    self._test_print_error(port, "ID query does not match")


if __name__ == '__main__':
    app = FxConfigCmd()
    app.cmdloop()



