import cmd2
import argparse


"""
Original plan is starting to become a mess. So explore an interactive shell instead

fxconfig <config file>

Commands
========
fx> list existing                           # show the entries from config file
fx> list visa                               # show resources returned by visa_resources()
fx> list updated                            # show what will be saved modified state
fx> add visa serial <port> [<baudrate>]
fx> add visa tcp <host | ip address>
fx> add serial bk176x <port> <baudrate>
fx> test existing                           # idn everything in existing config and report
fx> test updated                            # idn everything in updated config and report
fx> save                                    # replace existing with updated. existing will be first copied to *.bak

nice to have:
fx> test visa serial ...
fx> test visa tcp
fx> test serial

"""

# create the top-level parser for the base command
list_parser = argparse.ArgumentParser(prog='list')
list_parser.add_argument('list_type', choices=["existing", "updated", "visa"])


class FxConfigCmd(cmd2.Cmd):

    @cmd2.with_argparser(list_parser)
    def do_list(self, args):
        """Display either existing, visa or updated instrument list."""

        if args.list_type == "existing":
            self.poutput("do existing")

        elif args.list_type == "updated":
            self.poutput("do updated")

        elif args.list_type == "visa":
            self.poutput("do visa")
        else:
            raise Exception("we shouldn't have gotten here")

    def do_save(self, args):
        """Save over the existing config file with updated."""
        self.poutput("saving...")


if __name__ == '__main__':
    app = FxConfigCmd()
    app.cmdloop()



