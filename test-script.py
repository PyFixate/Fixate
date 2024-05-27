import dataclasses

from fixate.core.checks import chk_true
from fixate.core.common import TestClass, TestList, TestScript
from fixate.core.ui import user_info
from fixate.drivers import dmm


class JigDmm:
    """Just for my testing..."""
    def voltage_dc(self, _range: float) -> None:
        pass

    def measurement(self) -> float:
        user_info("Do some measurement!!!")
        return 0.0

    def close(self):
        user_info("Closing dummy dmm")


@dataclasses.dataclass
class Jig123DriverManager:
    dmm: JigDmm = dataclasses.field(default_factory=JigDmm)
    # This doesn't work right at the moment... not sure why yet.
    # dmm: dmm.DMM = dataclasses.field(default_factory=dmm.open)


class Jig123TestList(TestList[Jig123DriverManager]):
    pass


class Jig123TestClass(TestClass[Jig123DriverManager]):
    pass


class FailTest(Jig123TestClass):
    def set_up(self, dm: Jig123DriverManager):
        dm.dmm.voltage_dc(_range=30)

    def test(self, dm: Jig123DriverManager):
        v = dm.dmm.measurement()
        user_info(f"voltage measured was {v}")
        chk_true(False, "force a failure to see test cleanup")

class PassTest(Jig123TestClass):
    def test(self, dm: Jig123DriverManager):
        user_info(f"voltage measured was {dm.dmm.measurement()}")



# New TestScript class bundles a test list with a driver manager. In
# test_variants.py, we will define TestScript objects instead of top level
# test lists like we do now. I've used a dataclass for the driver manager,
# but it could be any class. It is also possible to define a small function
# to use as the `default_factor` say for a serial port, where we need to use
# findftdi to get the right port to open.

# Note that this is a bit of a compromise and might end up being a problem.
# At the moment would be possible for different `drivers` on our standard
# driver manager to use each other. We can't (easily) control creation order
# here, so that could run into problems. The behaviour is also slightly
# different to what we have now were each driver get "automatically" opened
# when accessed for the first time. With this design the sequence would
# create the driver manger, calling the default factory of each driver. I'm
# not sure that is necessarily good or bad. But is subtly different to existing
# driver managers.
#

TEST_SCRIPT = TestScript(
    test_list=Jig123TestList([FailTest(), PassTest()]),
    dm_type=Jig123DriverManager,
)
