"""Typed values and strict wire validation; all measurements are synthetic."""

import math
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import IntEnum


class OperatingState(IntEnum):
    RUNNING = 1
    STOPPED = 2
    FAULT = 3


@dataclass(frozen=True)
class TurbineSample:
    timestamp_utc: datetime
    sequence_number: int
    power_kw: float
    wind_speed_mps: float
    operating_state: OperatingState

    def validate(self) -> None:
        if self.timestamp_utc.tzinfo is None or self.timestamp_utc.utcoffset() is None:
            raise ValueError("Zeitstempel ohne Zeitzone")
        if not 0 <= self.sequence_number <= 0xFFFFFFFF:
            raise ValueError("Sequenz außerhalb uint32")
        if not math.isfinite(self.power_kw) or not 0 <= self.power_kw <= 3000:
            raise ValueError("Leistung außerhalb 0–3000 kW")
        if not math.isfinite(self.wind_speed_mps) or not 0 <= self.wind_speed_mps <= 60:
            raise ValueError("Windgeschwindigkeit außerhalb 0–60 m/s")
        if self.operating_state not in OperatingState:
            raise ValueError("Unbekannter Betriebszustand")
        if self.operating_state == OperatingState.STOPPED and self.power_kw != 0:
            raise ValueError("Gestoppte Anlage mit Leistung ungleich null")

    def to_dict(self) -> dict:
        result = asdict(self)
        result["timestamp_utc"] = self.timestamp_utc.isoformat()
        result["operating_state"] = self.operating_state.name
        return result
