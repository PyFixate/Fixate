# from x import y as y tell linters that we intend
# to export the symbol as part of our public interface
# https://github.com/microsoft/pyright/blob/main/docs/typed-libraries.md#library-interface

# Originally, test scripts had to reach into the internal
# packages and modules for imports. However, we will start
# to move the API intended for use in test scripts into the
# top level package namespace and try to be clearer about what
# is public vs private.
from fixate._switching import (
    # Type Alias
    Signal as Signal,
    Pin as Pin,
    PinList as PinList,
    PinSet as PinSet,
    SignalMap as SignalMap,
    TreeDef as TreeDef,
    PinUpdateCallback as PinUpdateCallback,
    # Runtime API
    PinSetState as PinSetState,
    PinUpdate as PinUpdate,
    VirtualMux as VirtualMux,
    VirtualSwitch as VirtualSwitch,
    RelayMatrixMux as RelayMatrixMux,
    AddressHandler as AddressHandler,
    PinValueAddressHandler as PinValueAddressHandler,
    MuxGroup as MuxGroup,
    JigDriver as JigDriver,
    generate_pin_group as generate_pin_group,
    generate_relay_matrix_pin_list as generate_relay_matrix_pin_list,
)

from fixate.main import run_main_program as run

__version__ = "0.6.3"
