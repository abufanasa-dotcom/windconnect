from dataclasses import replace
from datetime import UTC, datetime

import pytest

from windconnect.models import OperatingState, TurbineSample
from windconnect.registers import decode, encode

SAMPLE = TurbineSample(
    datetime(2026, 11, 5, tzinfo=UTC), 0x12345678, 1234.5, 10.25, OperatingState.RUNNING
)


@pytest.mark.parametrize(
    "sample",
    [
        SAMPLE,
        replace(SAMPLE, power_kw=0, operating_state=OperatingState.STOPPED),
        replace(SAMPLE, sequence_number=0xFFFFFFFF, power_kw=3000, wind_speed_mps=60),
    ],
)
def test_round_trip(sample):
    assert decode(encode(sample)) == sample


def test_known_word_order():
    registers = encode(SAMPLE)
    assert registers[:2] == [0x5743, 1]
    assert registers[6:8] == [0x1234, 0x5678]
    assert registers[8:] == [0, 12345, 1025, 1]


@pytest.mark.parametrize("index,value", [(0, 0), (1, 99), (10, 65535), (11, 99), (8, 65535)])
def test_invalid_payload(index, value):
    registers = encode(SAMPLE)
    registers[index] = value
    with pytest.raises(ValueError):
        decode(registers)


@pytest.mark.parametrize("registers", [[], [0] * 11, [0] * 13, [-1] * 12, [65536] * 12])
def test_bad_shape(registers):
    with pytest.raises(ValueError):
        decode(registers)


@pytest.mark.parametrize(
    "changes",
    [
        {"power_kw": -1},
        {"power_kw": float("nan")},
        {"wind_speed_mps": 61},
        {"sequence_number": -1},
        {"timestamp_utc": datetime(2026, 1, 1)},
        {"operating_state": OperatingState.STOPPED},
    ],
)
def test_invalid_model(changes):
    with pytest.raises(ValueError):
        encode(replace(SAMPLE, **changes))
