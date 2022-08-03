from typing import Tuple
import pytest

from fixate.drivers.pps.siglent_spd_3303X import SPD3303X


""" Testing the regex parsing of error strings returned by SYST:ERR? query
    Note the response strings vary between firmware versions:
        Old F/W = 1.01.01.02.05     (released 2017)
            '<code> <message>'
        New F/W = 1.01.01.02.07R2   (released 2021)
            '±<code>, <message>'
"""
error_strings = [
    ("0 No Error", (0, "No Error")),  # Old F/W
    ("+0, No Error", (0, "No Error")),  # New F/W
    ("128 Error 128", (128, "Error 128")),  # OLD F/W
    ("+128, Error 128", (128, "Error 128")),  # New F/W
    ("-113,Undefined header,*ID2N?", (-113, "Undefined header,*ID2N?")),
    ("-113,Undefined header,SYST:ERR", (-113, "Undefined header,SYST:ERR")),
]


@pytest.mark.parametrize(("error_string", "expected"), error_strings)
def test_error_parsing(error_string: str, expected: Tuple):
    assert SPD3303X._parse_errors(error_string) == expected
