import asyncio
import socket
from datetime import UTC, datetime, timedelta

import pytest

from windconnect.control import Scenario
from windconnect.public_demo import PublicDemoSession
from windconnect.public_text import TEXT, messages

BASE = datetime(2026, 11, 5, tzinfo=UTC)


def test_public_demo_real_transport_all_faults_recovery_and_cleanup():
    async def scenario():
        session = PublicDemoSession()

        async def poll(t):
            value = await session.poll(utc_now=BASE + timedelta(seconds=t), monotonic_now=t)
            assert value["transport"] == "real_loopback_modbus_tcp"
            assert value["listener_closed"]
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", value["port"]))
            return value

        assert (await poll(0))["diagnosis"]["state"] == "HEALTHY"
        session.set_scenario(Scenario.FREEZE)
        assert (await poll(1))["diagnosis"]["state"] == "HEALTHY"
        frozen = await poll(6)
        assert frozen["diagnosis"]["state"] == "STALE_DATA"
        assert frozen["read_succeeded"] is True
        assert frozen["sample"]["sequence_number"] == 2
        assert (await poll(7))["diagnosis"]["state"] == "STALE_DATA"
        assert sum(e["kind"] == "STALE_DATA" for e in session.events) == 1
        session.set_scenario(Scenario.NORMAL)
        assert (await poll(8))["diagnosis"]["state"] == "HEALTHY"
        session.set_scenario(Scenario.DISCONNECT)
        lost = await poll(9)
        assert lost["diagnosis"]["state"] == "CONNECTION_LOST"
        assert lost["read_succeeded"] is False
        assert lost["diagnosis"]["last_good"]
        session.set_scenario(Scenario.NORMAL)
        assert (await poll(10))["diagnosis"]["state"] == "HEALTHY"
        session.set_scenario(Scenario.INVALID)
        invalid = await poll(11)
        assert invalid["read_succeeded"] is True
        assert invalid["diagnosis"]["state"] == "INVALID_MEASUREMENT"
        session.set_scenario(Scenario.NORMAL)
        assert (await poll(12))["diagnosis"]["state"] == "HEALTHY"
        assert sum(e["kind"] == "RECOVERED" for e in session.events) == 3

    asyncio.run(asyncio.wait_for(scenario(), timeout=10))


def test_public_visitors_do_not_share_state_or_faults():
    async def scenario():
        first, second = PublicDemoSession(), PublicDemoSession()
        first.set_scenario(Scenario.INVALID)
        a, b = await asyncio.gather(first.poll(), second.poll())
        assert a["diagnosis"]["state"] == "INVALID_MEASUREMENT"
        assert b["diagnosis"]["state"] == "HEALTHY"
        assert a["history"] == []
        assert len(b["history"]) == 1
        assert all(event["kind"] == "HEALTHY" for event in second.events)
        assert first.events is not second.events

    asyncio.run(asyncio.wait_for(scenario(), timeout=5))


def test_demo_scenario_is_validated():
    with pytest.raises(ValueError):
        PublicDemoSession().set_scenario("arbitrary-host")


def test_public_language_parity_and_technical_state_names():
    assert all(len(pair) == 2 and all(pair) for pair in TEXT.values())
    assert messages("de").keys() == messages("en").keys()
    assert "Wirkleistung" == messages("de")["power"]
    assert "Active power" == messages("en")["power"]
    assert "VPP" not in messages("de")["title"]
    assert "127.0.0.1" in messages("en")["architecture_text"]
    with pytest.raises(ValueError):
        messages("unknown")
