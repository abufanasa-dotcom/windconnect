from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from windconnect.diagnostics import DiagnosticsEngine, Health
from windconnect.models import OperatingState, TurbineSample

BASE = datetime(2026, 11, 5, tzinfo=UTC)


def sample(t=0, seq=1):
    return TurbineSample(BASE + timedelta(seconds=t), seq, 1000, 9, OperatingState.RUNNING)


def observe(engine, t=0, value=None, **kwargs):
    return engine.observe(
        monotonic_now=t, utc_now=BASE + timedelta(seconds=t), sample=value, **kwargs
    )


def test_fault_priority_and_deduplication():
    engine = DiagnosticsEngine()
    good = sample()
    assert observe(engine, value=good)[0]["state"] == Health.HEALTHY
    for t in range(1, 11):
        diagnosis, events = observe(engine, t, good, error="timeout", invalid="bad")
        assert diagnosis["state"] == Health.CONNECTION_LOST
        assert len(events) == (1 if t == 1 else 0)
        assert diagnosis["last_good"] == good.to_dict()
        assert diagnosis["last_contact_utc"] == BASE.isoformat()
    diagnosis, events = observe(engine, 11, sample(11, 2))
    assert diagnosis["state"] == Health.HEALTHY
    assert [e["kind"] for e in events] == ["RECOVERED", "HEALTHY"]


@pytest.mark.parametrize(
    "freeze_sequence,freeze_timestamp", [(True, True), (True, False), (False, True)]
)
def test_each_freshness_signal_must_advance(freeze_sequence, freeze_timestamp):
    engine = DiagnosticsEngine(5)
    observe(engine, value=sample())
    for t in range(1, 7):
        value = sample(0 if freeze_timestamp else t, 1 if freeze_sequence else t + 1)
        diagnosis, _ = observe(engine, t, value)
        assert diagnosis["state"] == (Health.STALE_DATA if t >= 5 else Health.HEALTHY)


def test_invalid_before_stale_and_recovery_requires_new_data():
    engine = DiagnosticsEngine()
    good = sample()
    observe(engine, value=good)
    assert (
        observe(engine, 6, good, invalid="bad scaling")[0]["state"]
        == Health.INVALID_MEASUREMENT
    )
    assert observe(engine, 7, good)[0]["state"] == Health.STALE_DATA
    assert observe(engine, 8, sample(8, 2))[0]["state"] == Health.HEALTHY


def test_immediate_reconnect_with_cached_sample_is_not_recovered():
    engine = DiagnosticsEngine()
    observe(engine, value=sample())
    observe(engine, 1, error="timeout")
    diagnosis, events = observe(engine, 2, sample())
    assert diagnosis["state"] == Health.STALE_DATA
    assert "RECOVERED" not in [event["kind"] for event in events]
    diagnosis, events = observe(engine, 3, sample(3, 2))
    assert diagnosis["state"] == Health.HEALTHY
    assert events[0]["kind"] == "RECOVERED"


def test_stopped_zero_is_valid():
    engine = DiagnosticsEngine()
    value = replace(sample(), power_kw=0, operating_state=OperatingState.STOPPED)
    assert observe(engine, value=value)[0]["state"] == Health.HEALTHY


def test_counter_rollover_is_fresh():
    engine = DiagnosticsEngine(1)
    observe(engine, value=sample(0, 0xFFFFFFFF))
    assert observe(engine, 2, sample(2, 0))[0]["state"] == Health.HEALTHY


def test_old_first_sample_and_future_clock():
    engine = DiagnosticsEngine()
    assert observe(engine, 6, sample())[0]["state"] == Health.STALE_DATA
    assert observe(engine, 7, sample(20, 2))[0]["state"] == Health.INVALID_MEASUREMENT


def test_invalid_model_and_missing_sample():
    engine = DiagnosticsEngine()
    assert (
        observe(engine, value=replace(sample(), power_kw=-1))[0]["state"]
        == Health.INVALID_MEASUREMENT
    )
    assert observe(engine)[0]["state"] == Health.INVALID_MEASUREMENT


def test_invalid_configuration():
    with pytest.raises(ValueError):
        DiagnosticsEngine(0)
