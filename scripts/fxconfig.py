import argparse
import json
import visa
from pyvisa.errors import VisaIOError
from pathlib import Path
from shutil import copy2
from os import replace

from fixate.drivers.pps.bk_178x import BK178X

"""
Example config file. Typically called local_config.json. note that INSTRUMENTS is the only top level key that
is used anywhere.

 
{
    "INSTRUMENTS": {
        "serial": {
            "COM1": [
                "address: 0,checksum: 28,command: 49,model: 6823,serial_number: 3697210019,software_version: 29440,start: 170,",
                9600
            ]
        },
        "visa": [
            [
                "RIGOL TECHNOLOGIES,DG1022 ,DG1D144904270,,00.03.00.09.00.02.11\n",
                "USB0::0x09C4::0x0400::DG1D144904270::INSTR"
            ],
            [
                "FLUKE,8846A,3821015,08/02/10-11:53\r\n",
                "ASRL13::INSTR"
            ]
        ]
    }
}
"""


class FxConfigError(Exception): pass


# Stolen from discover.py. This should probably get consolidated back there,
# but I want to avoid messing with the internals for now.
def visa_id_query(visa_resource_name):
    """
    Attempt to open `visa_resource_name` and if successful, send an *IDN? command. Return
    the result of the idn command as a string.
    :param visa_resource_name:
    :return:
    """
    instr = visa.ResourceManager().open_resource(visa_resource_name, query_delay=0.1)
    # 1 s timeout is overly conservative. But if we call clear() that can take a while for some instruments
    instr.timeout = 1000
    # instr.clear()
    resp = instr.query("*IDN?")

    if resp:
        instr.close()
        return resp.strip()

    # At least one instrument (Siglent SPD3303X power supply) only responds
    # when the line termination is set to \n
    instr.read_termination = '\n'
    instr.write_termination = '\n'

    resp = instr.query("*IDN?")

    if resp:
        instr.close()
        return resp.strip()

    raise FxConfigError(
        "Resource '{}' didn't respond to an IDN command".format(visa_resource_name))


def serial_id_query(port, baudrate):
    """
    The only serial type instrument we use is the BK Precision 178x. So we just going to hard code
    calling the identity method on that class.
    :return:
    """

    pps = BK178X(port)
    pps.baud_rate = baudrate        # baud_rate property implementation has the side effect of opening the port.
    return pps.identify(as_string=True)


def parse_args():
    parser = argparse.ArgumentParser(description="""
        Fixate Config Helper Utility""")

    parser.add_argument("config", help="Path to config file")
    # parser.add_argument("new_config", help="New file to write to")

    return parser.parse_args()


def print_curent_config(config_dict):
    for visa_instrument in config_dict["INSTRUMENTS"]["visa"]:
        print("VISA || " + visa_instrument[1].strip() + " || " + visa_instrument[0].strip())

    for com_port, parameters in config_dict["INSTRUMENTS"]["serial"].items():
        print("SERIAL || " + com_port + " || " + str(parameters))


def backup_file(file_path):
    """
    Create a backup of `file_path` in the same directory. Appends ".bak" to the file name.
    :param file_path:
    :return: Pathlib.Path object which is the path of the new file
    """
    backup_path = Path(file_path + ".bak")
    copy2(file_path, backup_path)
    return backup_path


def interactively_update_config(config_file_path):
    """

    For each instrument in the old config
      if it's USB & detected by visa now, keep it
      if it's USB & not detected by visa now, prompt the user to delete
      if it's serial, prompt the user if they want to send IDN
          if yes and it matches, keep it
          if yes and it doesn't match, prompt the user to delete or update
          if no prompt the user to delete. Otherwise keep.
    For each USB instrument that is detected, but not in the old config,
    prompt user to IDN. If IDN is successful, prompt if they want to keep.

      After all that is done, ask the user if they want to add any new serial
      devices. If yes, prompt for serial port, send IDN, add to config if successful.

    Also need to repeat the whole process for "serial" instrument
    the only "serial" instrument we have to date in the BK precision power supply
    Driver classes for a serial instrument need to implement the instr.identify(as_string=True)
    method. The string returned by identify is stored in the config.
    :param config_file_path:
    :return:
    """

    # A list visa instruments. Each instrument is represented as a two element list:
    # [<idn string>, <visa resource name>]
    # A concrete example with a single entry would be:
    # [
    #   ["RIGOL TECHNOLOGIES,DG1022 ,DG1D144904270,,00.03.00.09.00.02.11\n",
    #   "USB0::0x09C4::0x0400::DG1D144904270::INSTR"],
    # ]
    new_visa = []

    # A dict of serial instruments. A.K.A the BK power supply.
    # Keyed on port name, then instrument specific details, which is a list e.g.
    # {
    #       "COM37": [
    #           "address: 0,checksum: 28,command: 49,model: 6823,serial_number: 3697210019,software_version: 29440,start: 170,",
    #           9600
    #       ]
    # }
    new_serial = {}

    print("** Resources Reported By Visa **")
    rm = visa.ResourceManager()
    visa_resource_list = rm.list_resources()
    for resource in visa_resource_list:
        print(resource)
    print()

    print("** Existing instruments **")
    with open(config_file_path, 'r') as config_file:
        config_dict = json.load(config_file)
        print_curent_config(config_dict)

        for visa_instrument in config_dict["INSTRUMENTS"]["visa"]:
            idn_response, resource_name = visa_instrument
            idn_response = idn_response.strip()

            if resource_name.startswith("USB"):
                # USB instruments are kept if they are detected by the ResourceManger
                if resource_name in visa_resource_list:
                    print("Existing USB Instrument '{}' was found by the visa resource manager".format(resource_name))
                    new_visa.append(visa_instrument)
                else:
                    print("Existing USB Instrument '{}' not found by the visa resource manager".format(resource_name))
                    answer = input("Do you want to keep it? [y]/n")
                    if answer == "n":
                        # to delete, we simply don't add to new_visa
                        print("'{}' deleted".format(resource_name))
                    else:
                        print("'{}' kept".format(resource_name))
                        new_visa.append(visa_instrument)

            elif resource_name.startswith("ASRL"):
                if resource_name in visa_resource_list:
                    print("Existing Serial Instrument '{}' was found by the visa resource manager".format(resource_name))
                    print("Config IDN string was '{}'".format(idn_response))

                    answer = input("Do you want to check IDN? y/[n]")
                    if answer == "y":
                        try:
                            idn = visa_id_query(resource_name)
                        except (FxConfigError, VisaIOError):
                            print("Error trying to run IDN command")
                            pass
                        else:
                            print("Instrument '{}' returned IDN String '{}'".format(resource_name, idn))
                            if idn == idn_response:
                                print("Existing IDN has been kept")
                            else:
                                print("IDN String updated in config")
                            new_visa.append((idn, resource_name))

                    else:
                        answer = input("Do you want to keep it? [y]/n")
                        if answer == "n":
                            # to delete, we simply don't add to new_visa
                            print("'{}' deleted".format(resource_name))
                        else:
                            print("'{}' kept".format(resource_name))
                            new_visa.append(visa_instrument)

                else:
                    print("Existing Serial Instrument '{}' not found by the visa resource manager".format(resource_name))
                    answer = input("Do you want to keep it? [y]/n")
                    if answer == "n":
                        # to delete, we simply don't add to new_visa
                        print("'{}' deleted".format(resource_name))
                    else:
                        print("'{}' kept".format(resource_name))
                        new_visa.append(visa_instrument)

            elif resource_name.startswith("TCP"):
                print("Existing TCP Instrument '{}' will be kept".format(resource_name))
                new_visa.append(visa_instrument)

            else:
                # if there is a visa resource we don't recognise, keep it for now.
                print("Existing resource '{}' type is no know & will be kept".format(resource_name))
                new_visa.append(visa_instrument)

    config_dict["INSTRUMENTS"]["visa"] = new_visa
    # config_dict["INSTRUMENTS"]["serial"] = new_serial

    with open(config_file_path, 'w') as config_file:
        json.dump(config_dict, config_file, sort_keys=True, indent=4)


def main():
    args = parse_args()

    print("Fixate instrument config utility:")

    backup_path = backup_file(args.config)

    try:
        interactively_update_config(args.config)
    except:
        backup_path.replace(args.config)
        raise


if __name__ == "__main__":
    main()
    # args = parse_args()
    #
    # with open(args.config, 'r') as config_file:
    #     config_dict = json.load(config_file)
    #
    #     print("Serial Instruments in config file")
    #     for serial_instrument in config_dict["INSTRUMENTS"]["serial"]:
    #         print(serial_instrument)
    #
    #     print("Identity from connected PS")
    #     for port, params in config_dict["INSTRUMENTS"]["serial"].items():
    #         id, baudrate = params
    #         print(serial_id_query(port, baudrate))
