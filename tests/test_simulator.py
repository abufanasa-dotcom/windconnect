from datetime import UTC, datetime

import pytest

from windconnect.models import OperatingState
from windconnect.simulator import TurbineSimulator

NOW = datetime(2026, 11, 5, tzinfo=UTC)


def test_seed_is_repeatable():
    a, b = TurbineSimulator(7), TurbineSimulator(7)
    assert [a.sample(NOW) for _ in range(100)] == [b.sample(NOW) for _ in range(100)]


@pytest.mark.parametrize("wind,power", [(0, 0), (2.9, 0), (3, 0), (12, 3000), (25, 0), (60, 0)])
def test_power_curve(wind, power):
    sample = TurbineSimulator().sample(NOW, wind)
    assert sample.power_kw == power
    if wind < 3 or wind >= 25:
        assert sample.operating_state == OperatingState.STOPPED


@pytest.mark.parametrize("wind", [-1, 61, float("nan"), float("inf")])
def test_bad_wind(wind):
    with pytest.raises(ValueError):
        TurbineSimulator().sample(NOW, wind)


def test_counter_wrap():
    simulator = TurbineSimulator()
    simulator.sequence = 0xFFFFFFFF
    assert simulator.sample(NOW).sequence_number == 0
