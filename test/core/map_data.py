from fixate.core.jig_mapping import VirtualMux, shift_nested

# taken from ELV Jig as an example. There are two definition of the same
# mux. One is the old school RPJ version. The other is the new CGL version
# which uses a nested sequence, map_tree. both should generate identical
# output when condensed_signal_map() is called.

# output of condensed_signal_map()
MuxDmmInputHi_signal_map = [
    ("0b00000000000001", "SPARE14"),
    ("0b00000000000010", "SPARE13"),
    ("0b00000000000011", "SPARE12"),
    ("0b00000000000100", "SPARE11"),
    ("0b00000000000101", "CLK_CHK"),
    ("0b00000000000110", "LED_0V_PS2"),
    ("0b00000000000111", "SUPP_CT_POS"),
    ("0b00000000001000", "SUPP_AC_POS"),
    ("0b00000000001001", "SUPP_DC_POS"),
    ("0b00000000001010", "SPARE10"),
    ("0b00000000001011", "SUPP_110VAC"),
    ("0b00000000001100", "PWR_VPS"),
    ("0b00000000001101", "PWR_VREF"),
    ("0b00000000001110", "PWR_EL_IN"),
    ("0b00000000001111", "PWR_CAP"),
    ("0b00000000010000", "PWR_REG_FB"),
    ("0b00000000010001", "PWR_VDC"),
    ("0b00000000010010", "PWR_SNUBBER_OUT"),
    ("0b00000000010011", "CPU_4_20_MA_NEG"),
    ("0b00000000010100", "CPU_VREF_POS"),
    ("0b00000000010101", "CPU_EL_SIGNAL"),
    ("0b00000000010110", "CPU_VPS_POS"),
    ("0b00000000010111", "CPU_VLED"),
    ("0b00000000011000", "CPU_R_A_RST"),
    ("0b00000000011001", "CPU_RELAY_FEEDBACK"),
    ("0b00000000011010", "CPU_ISP_NOT"),
    ("0b00000000011011", "CPU_SWCLK_NOT"),
    ("0b00000000011100", "CPU_VCC"),
    ("0b00000000011101", "CPU_VPS_2"),
    ("0b00000000011110", "CPU_3_3_2_V"),
    ("0b00000000011111", "SPARE9"),
    ("0b00000000100110", "LED_0V_PS1"),
    ("0b00000001000110", "LED_VPS_POS"),
    ("0b00000001100110", "LED_RELAY_DRIVE"),
    ("0b00000010000110", "LED_RELAY_FEEDBACK"),
    ("0b00000010100110", "LED_VREF"),
    ("0b00000011000110", "LED_EL_SIGNAL"),
    ("0b00000011100110", "MUX_C_GND"),
    ("0b00000100011001", "CPU_RST_POS"),
    ("0b00001000011001", "CPU_RST_NEG"),
    ("0b00001100011001", "CPU_FS_POS"),
    ("0b00010000011001", "CPU_FS_NEG"),
    ("0b00010100011001", "CPU_MODE_3"),
    ("0b00011000011001", "CPU_MODE_2"),
    ("0b00011100011001", "CPU_MODE_1"),
    ("0b00100000011010", "CPU_SWDIO"),
    ("0b01000000011010", "CPU_WDI"),
    ("0b01100000011010", "TP4"),
    ("0b10000000011010", "CPU_LED_CLK_5V"),
    ("0b10100000011010", "CPU_LED_EN_5V"),
    ("0b11000000011010", "CPU_LED_DATA_5V"),
    ("0b11100000011010", "CPU_RELAY_DRIVE"),
]


# RPJ version
class MuxDmmInputHi(VirtualMux):
    """"""

    # LSB(index 0) to MSB(index -1)
    pin_list = [
        "DMM_HI5",
        "DMM_HI4",
        "DMM_HI3",
        "DMM_HI2",
        "DMM_HI1",  # Main DMM Hi Relays
        "P0.21",
        "P0.20",
        "P0.19",  # MuxC
        "P0.18",
        "P0.17",
        "P0.16",  # MuxB
        "P0.15",
        "P0.14",
        "P0.13",  # MuxA
    ]

    def map_signals(self):
        self.map_shifted(
            base_index=0,
            start_index=self.pin_list.index("DMM_HI5"),
            values=[
                None,
                "SPARE14",
                "SPARE13",
                "SPARE12",
                "SPARE11",
                "CLK_CHK",
                None,  # Overridden later
                "SUPP_CT_POS",
                "SUPP_AC_POS",
                "SUPP_DC_POS",
                "SPARE10",
                "SUPP_110VAC",
                "PWR_VPS",
                "PWR_VREF",
                "PWR_EL_IN",
                "PWR_CAP",
                "PWR_REG_FB",
                "PWR_VDC",
                "PWR_SNUBBER_OUT",
                "CPU_4_20_MA_NEG",
                "CPU_VREF_POS",
                "CPU_EL_SIGNAL",
                "CPU_VPS_POS",
                "CPU_VLED",
                "CPU_R_A_RST",
                None,  # Overridden later
                None,  # Overridden later
                "CPU_SWCLK_NOT",
                "CPU_VCC",
                "CPU_VPS_2",
                "CPU_3_3_2_V",
                "SPARE9",
            ],
        )
        # Mux C
        self.map_shifted(
            base_index=6,
            start_index=self.pin_list.index("P0.21"),
            values=[
                "LED_0V_PS2",
                "LED_0V_PS1",
                "LED_VPS_POS",
                "LED_RELAY_DRIVE",
                "LED_RELAY_FEEDBACK",
                "LED_VREF",
                "LED_EL_SIGNAL",
                "MUX_C_GND",
            ],
        )
        # Mux B
        self.map_shifted(
            base_index=25,
            start_index=self.pin_list.index("P0.18"),
            values=[
                "CPU_RELAY_FEEDBACK",
                "CPU_RST_POS",
                "CPU_RST_NEG",
                "CPU_FS_POS",
                "CPU_FS_NEG",
                "CPU_MODE_3",
                "CPU_MODE_2",
                "CPU_MODE_1",
            ],
        )
        # Mux A
        self.map_shifted(
            base_index=26,
            start_index=self.pin_list.index("P0.15"),
            values=[
                "CPU_ISP_NOT",
                "CPU_SWDIO",
                "CPU_WDI",
                "TP4",
                "CPU_LED_CLK_5V",
                "CPU_LED_EN_5V",
                "CPU_LED_DATA_5V",
                "CPU_RELAY_DRIVE",
            ],
        )


class TestMultipleDefsFails(VirtualMux):
    pin_list = ["P0", "P1", "P2", "P3"]

    def map_signals(self):
        pass

    def map_singles(self):
        self.map_single("Test1", "P0", "P1")
        self.map_single("Test2", "P1", "P2")
        self.map_single("Test3", "P1", "P0")

    def map_trees(self):
        self._map_tree(("Test1", "Test2", "Test3", "Test4"), 0, 0)
        self._map_tree(("Test5", "Test6", "Test7", "Test8"), 3, 0)

    def map_shifteds(self):
        self.map_shifted(0, 0, ("Test1", "Test2", "Test3", "Test4"))
        self.map_shifted(3, 0, ("Test5", "Test6", "Test7", "Test8"))

    def map_combo(self):
        self._map_tree(("Test1", "Test2", "Test3", "Test4"), 0, 0)
        self.map_single("Test5", "P1", "P0")


# CGL version
class MuxDmmInputHi_treedef(VirtualMux):
    pin_list = [
        "DMM_HI5",
        "DMM_HI4",
        "DMM_HI3",
        "DMM_HI2",
        "DMM_HI1",  # Main DMM Hi Relays
        "P0.21",
        "P0.20",
        "P0.19",  # MuxC
        "P0.18",
        "P0.17",
        "P0.16",  # MuxB
        "P0.15",
        "P0.14",
        "P0.13",  # MuxA
    ]

    map_tree = (
        None,
        "SPARE14",
        "SPARE13",
        "SPARE12",
        "SPARE11",
        "CLK_CHK",
        (  # MUX C - U29
            "LED_0V_PS2",
            "LED_0V_PS1",
            "LED_VPS_POS",
            "LED_RELAY_DRIVE",
            "LED_RELAY_FEEDBACK",
            "LED_VREF",
            "LED_EL_SIGNAL",
            "MUX_C_GND",
        ),
        "SUPP_CT_POS",
        "SUPP_AC_POS",
        "SUPP_DC_POS",
        "SPARE10",
        "SUPP_110VAC",
        "PWR_VPS",
        "PWR_VREF",
        "PWR_EL_IN",
        "PWR_CAP",
        "PWR_REG_FB",
        "PWR_VDC",
        "PWR_SNUBBER_OUT",
        "CPU_4_20_MA_NEG",
        "CPU_VREF_POS",
        "CPU_EL_SIGNAL",
        "CPU_VPS_POS",
        "CPU_VLED",
        "CPU_R_A_RST",
        (  # MUX C Level
            (  # MUX B - U2
                "CPU_RELAY_FEEDBACK",
                "CPU_RST_POS",
                "CPU_RST_NEG",
                "CPU_FS_POS",
                "CPU_FS_NEG",
                "CPU_MODE_3",
                "CPU_MODE_2",
                "CPU_MODE_1",
            ),
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ),
        (  # MUX C Level
            (  # MUX B Level
                (  # MUX A - U1
                    "CPU_ISP_NOT",
                    "CPU_SWDIO",
                    "CPU_WDI",
                    "TP4",
                    "CPU_LED_CLK_5V",
                    "CPU_LED_EN_5V",
                    "CPU_LED_DATA_5V",
                    "CPU_RELAY_DRIVE",
                ),
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ),
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ),
        "CPU_SWCLK_NOT",
        "CPU_VCC",
        "CPU_VPS_2",
        "CPU_3_3_2_V",
        "SPARE9",
    )


class MuxDmmInputHi_treedef_compact(VirtualMux):
    pin_list = [
        "DMM_HI5",
        "DMM_HI4",
        "DMM_HI3",
        "DMM_HI2",
        "DMM_HI1",  # Main DMM Hi Relays
        "P0.21",
        "P0.20",
        "P0.19",  # MuxC
        "P0.18",
        "P0.17",
        "P0.16",  # MuxB
        "P0.15",
        "P0.14",
        "P0.13",  # MuxA
    ]
    mux_c = (
        "LED_0V_PS2",
        "LED_0V_PS1",
        "LED_VPS_POS",
        "LED_RELAY_DRIVE",
        "LED_RELAY_FEEDBACK",
        "LED_VREF",
        "LED_EL_SIGNAL",
        "MUX_C_GND",
    )
    mux_b = (
        "CPU_RELAY_FEEDBACK",
        "CPU_RST_POS",
        "CPU_RST_NEG",
        "CPU_FS_POS",
        "CPU_FS_NEG",
        "CPU_MODE_3",
        "CPU_MODE_2",
        "CPU_MODE_1",
    )
    mux_a = (
        "CPU_ISP_NOT",
        "CPU_SWDIO",
        "CPU_WDI",
        "TP4",
        "CPU_LED_CLK_5V",
        "CPU_LED_EN_5V",
        "CPU_LED_DATA_5V",
        "CPU_RELAY_DRIVE",
    )
    map_tree = (
        None,
        "SPARE14",
        "SPARE13",
        "SPARE12",
        "SPARE11",
        "CLK_CHK",
        mux_c,
        "SUPP_CT_POS",
        "SUPP_AC_POS",
        "SUPP_DC_POS",
        "SPARE10",
        "SUPP_110VAC",
        "PWR_VPS",
        "PWR_VREF",
        "PWR_EL_IN",
        "PWR_CAP",
        "PWR_REG_FB",
        "PWR_VDC",
        "PWR_SNUBBER_OUT",
        "CPU_4_20_MA_NEG",
        "CPU_VREF_POS",
        "CPU_EL_SIGNAL",
        "CPU_VPS_POS",
        "CPU_VLED",
        "CPU_R_A_RST",
        shift_nested(mux_b, [3]),
        shift_nested(mux_a, [3, 3]),
        "CPU_SWCLK_NOT",
        "CPU_VCC",
        "CPU_VPS_2",
        "CPU_3_3_2_V",
        "SPARE9",
    )


MuxDisplayLEDs_signal_map = [
    ("0b000010111", "LED_10_PC"),
    ("0b000011011", "LED_20_PC"),
    ("0b000011101", "LED_30_PC"),
    ("0b000011110", "LED_40_PC"),
    ("0b000100111", "LED_50_PC"),
    ("0b000101011", "LED_60_PC"),
    ("0b000101101", "LED_70_PC"),
    ("0b000101110", "LED_80_PC"),
    ("0b001000111", "LED_90_PC"),
    ("0b001001011", "LED_100_PC"),
    ("0b001001101", "LED_CT_Fault"),
    ("0b001001110", "LED_HRM_Trip"),
    ("0b010000111", "LED_Trip"),
    ("0b010001011", "LED_Healthy"),
    ("0b010001110", "LED_NFS"),
    ("0b100000000", "LED_Relay"),
]


class MuxDisplayLEDs(VirtualMux):
    """
    Mux for the leds on the display board tests
    """

    pin_list = [
        "DispQ7",
        "DispQ6",
        "DispQ5",
        "DispQ4",
        "DispQ3",
        "DispQ2",
        "DispQ1",
        "DispQ0",
        "P0.0",
    ]

    # pin_list = ["DispQ0", "DispQ1", "DispQ2", "DispQ3", "DispQ4", "DispQ5", "DispQ6", "DispQ7", "P0.0"]

    def map_signals(self):
        self.map_single(
            "LED_10_PC", "DispQ3", "DispQ7", "DispQ6", "DispQ5"
        )  # D5 LED 10%
        self.map_single(
            "LED_20_PC", "DispQ3", "DispQ7", "DispQ6", "DispQ4"
        )  # D6 LED 20%
        self.map_single(
            "LED_30_PC", "DispQ3", "DispQ7", "DispQ4", "DispQ5"
        )  # D8 LED 30%
        self.map_single(
            "LED_40_PC", "DispQ3", "DispQ4", "DispQ6", "DispQ5"
        )  # D9 LED 40%
        self.map_single(
            "LED_50_PC", "DispQ2", "DispQ7", "DispQ6", "DispQ5"
        )  # D10 LED 50%
        self.map_single(
            "LED_60_PC", "DispQ2", "DispQ7", "DispQ6", "DispQ4"
        )  # D11 LED 60%
        self.map_single(
            "LED_70_PC", "DispQ2", "DispQ7", "DispQ4", "DispQ5"
        )  # D13 LED 70%
        self.map_single(
            "LED_80_PC", "DispQ2", "DispQ4", "DispQ6", "DispQ5"
        )  # D14 LED 80%
        self.map_single(
            "LED_90_PC", "DispQ1", "DispQ7", "DispQ6", "DispQ5"
        )  # D16 LED 90%
        self.map_single(
            "LED_100_PC", "DispQ1", "DispQ7", "DispQ6", "DispQ4"
        )  # D18 LED 100%
        self.map_single(
            "LED_CT_Fault", "DispQ1", "DispQ7", "DispQ4", "DispQ5"
        )  # D23 LED CT Fault
        self.map_single(
            "LED_HRM_Trip", "DispQ1", "DispQ4", "DispQ6", "DispQ5"
        )  # D24 LED HRM Trip
        self.map_single(
            "LED_Trip", "DispQ0", "DispQ7", "DispQ6", "DispQ5"
        )  # D20 LED Trip
        self.map_single(
            "LED_Healthy", "DispQ0", "DispQ7", "DispQ6", "DispQ4"
        )  # D15 LED Healthy
        self.map_single(
            "LED_NFS", "DispQ0", "DispQ4", "DispQ6", "DispQ5"
        )  # D25 LED NFS
        # Driven from a different set
        self.map_single("LED_Relay", "P0.0")  # D26 LED Relay


class MuxDisplayLEDs_listdef(VirtualMux):
    """
    Mux for the leds on the display board tests
    """

    pin_list = [
        "DispQ7",
        "DispQ6",
        "DispQ5",
        "DispQ4",
        "DispQ3",
        "DispQ2",
        "DispQ1",
        "DispQ0",
        "P0.0",
    ]

    map_list = (
        ("LED_10_PC", "DispQ3", "DispQ7", "DispQ6", "DispQ5"),  # D5 LED 10%
        ("LED_20_PC", "DispQ3", "DispQ7", "DispQ6", "DispQ4"),  # D6 LED 20%
        ("LED_30_PC", "DispQ3", "DispQ7", "DispQ4", "DispQ5"),  # D8 LED 30%
        ("LED_40_PC", "DispQ3", "DispQ4", "DispQ6", "DispQ5"),  # D9 LED 40%
        ("LED_50_PC", "DispQ2", "DispQ7", "DispQ6", "DispQ5"),  # D10 LED 50%
        ("LED_60_PC", "DispQ2", "DispQ7", "DispQ6", "DispQ4"),  # D11 LED 60%
        ("LED_70_PC", "DispQ2", "DispQ7", "DispQ4", "DispQ5"),  # D13 LED 70%
        ("LED_80_PC", "DispQ2", "DispQ4", "DispQ6", "DispQ5"),  # D14 LED 80%
        ("LED_90_PC", "DispQ1", "DispQ7", "DispQ6", "DispQ5"),  # D16 LED 90%
        ("LED_100_PC", "DispQ1", "DispQ7", "DispQ6", "DispQ4"),  # D18 LED 100%
        ("LED_CT_Fault", "DispQ1", "DispQ7", "DispQ4", "DispQ5"),  # D23 LED CT Fault
        ("LED_HRM_Trip", "DispQ1", "DispQ4", "DispQ6", "DispQ5"),  # D24 LED HRM Trip
        ("LED_Trip", "DispQ0", "DispQ7", "DispQ6", "DispQ5"),  # D20 LED Trip
        ("LED_Healthy", "DispQ0", "DispQ7", "DispQ6", "DispQ4"),  # D15 LED Healthy
        ("LED_NFS", "DispQ0", "DispQ4", "DispQ6", "DispQ5"),  # D25 LED NFS
        ("LED_Relay", "P0.0"),  # D26 LED Relay
    )


if __name__ == "__main__":
    mux = MuxDisplayLEDs().condensed_signal_map()

    mux2 = MuxDisplayLEDs_listdef().condensed_signal_map()
    print(mux)
    print(mux2)
    print(mux == mux2)
