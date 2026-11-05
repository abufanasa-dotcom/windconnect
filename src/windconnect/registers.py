"""Versioned 12-register, big-endian, scaled-integer protocol."""

import struct
from datetime import UTC, datetime

from windconnect.models import OperatingState, TurbineSample

REGISTER_COUNT = 12
MAGIC = 0x5743
VERSION = 1


def encode(sample: TurbineSample) -> list[int]:
    sample.validate()
    payload = struct.pack(
        ">HHQIIHH",
        MAGIC,
        VERSION,
        round(sample.timestamp_utc.timestamp() * 1000),
        sample.sequence_number,
        round(sample.power_kw * 10),
        round(sample.wind_speed_mps * 100),
        int(sample.operating_state),
    )
    return list(struct.unpack(">12H", payload))


def decode(registers: list[int]) -> TurbineSample:
    if len(registers) != REGISTER_COUNT:
        raise ValueError(f"Registeranzahl {len(registers)} statt {REGISTER_COUNT}")
    if any(type(value) is not int or not 0 <= value <= 65535 for value in registers):
        raise ValueError("Ungültiges 16-Bit-Register")
    magic, version, stamp, sequence, power, wind, state = struct.unpack(
        ">HHQIIHH", struct.pack(">12H", *registers)
    )
    if magic != MAGIC or version != VERSION:
        raise ValueError("Registerformat oder Protokollversion unbekannt")
    try:
        sample = TurbineSample(
            datetime.fromtimestamp(stamp / 1000, UTC),
            sequence,
            power / 10,
            wind / 100,
            OperatingState(state),
        )
    except (ValueError, OverflowError, OSError) as exc:
        raise ValueError("Zeitstempel oder Betriebszustand ungültig") from exc
    sample.validate()
    return sample
