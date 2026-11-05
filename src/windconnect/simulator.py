"""Seeded, deliberately simple 3 MW turbine power curve."""

import math
import random
from datetime import datetime

from windconnect.models import OperatingState, TurbineSample


class TurbineSimulator:
    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)
        self.sequence = 0

    def sample(self, timestamp: datetime, wind: float | None = None) -> TurbineSample:
        self.sequence = (self.sequence + 1) & 0xFFFFFFFF
        if wind is None:
            wind = 9 + 3 * math.sin(self.sequence / 20) + self._rng.uniform(-0.3, 0.3)
        if not math.isfinite(wind) or not 0 <= wind <= 60:
            raise ValueError("Windgeschwindigkeit außerhalb 0–60 m/s")
        running = 3 <= wind < 25
        power = min(3000, 3000 * ((wind - 3) / 9) ** 3) if running else 0.0
        sample = TurbineSample(
            timestamp,
            self.sequence,
            round(power, 1),
            round(wind, 2),
            OperatingState.RUNNING if running else OperatingState.STOPPED,
        )
        sample.validate()
        return sample
