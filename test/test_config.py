import fixate.config
from pathlib import Path

CONFIG_DIR = Path(__file__).parent / "config"


def test_read_local_config():
    """
    We should get a list of InstrumentConfig objects. This is just a real
    simple smoke test.
    """
    result = fixate.config.load_instrument_config(CONFIG_DIR / "instruments.json")

    assert len(result) == 4
    assert (
        len(
            [
                inst_conf
                for inst_conf in result
                if inst_conf.instrument_type == fixate.config.InstrumentType.VISA
            ]
        )
        == 3
    )


def test_find_instrument_by_id_success(monkeypatch):
    instr = fixate.config.InstrumentConfig(
        id="RIGOL TECHNOLOGIES,DG1022 ,DG1D144904270,,00.03.00.09.00.02.11\n",
        address="USB0::0x09C4::0x0400::DG1D144904270::INSTR",
        instrument_type=fixate.config.InstrumentType.VISA,
        parameters={},
    )
    monkeypatch.setattr(fixate.config, "INSTRUMENTS", [instr])
    result = fixate.config.find_instrument_by_id("DG1.1")
    assert result == instr


def test_find_instrument_by_id_success(monkeypatch):
    instr = fixate.config.InstrumentConfig(
        id="RIGOL TECHNOLOGIES,DG1022 ,DG1D144904270,,00.03.00.09.00.02.11\n",
        address="USB0::0x09C4::0x0400::DG1D144904270::INSTR",
        instrument_type=fixate.config.InstrumentType.VISA,
        parameters={},
    )
    monkeypatch.setattr(fixate.config, "INSTRUMENTS", [instr])
    result = fixate.config.find_instrument_by_id("Not a match")
    assert result is None
