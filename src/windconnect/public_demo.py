"""Session-owned demo with a real, short-lived loopback Modbus exchange per poll."""

import time
from collections import deque
from datetime import UTC, datetime
from threading import Lock

from windconnect.control import Scenario
from windconnect.diagnostics import DiagnosticsEngine, Health
from windconnect.modbus_client import ModbusPoller, TransportError
from windconnect.modbus_server import LocalModbusServer
from windconnect.models import TurbineSample
from windconnect.registers import decode, encode
from windconnect.simulator import TurbineSimulator


class PublicDemoSession:
    """No shared files, global services, threads, or persistent network listeners."""

    def __init__(self, seed: int = 42, stale_after: float = 5):
        self.simulator = TurbineSimulator(seed)
        self.engine = DiagnosticsEngine(stale_after)
        self.scenario = Scenario.NORMAL
        self.frozen: TurbineSample | None = None
        self.events: deque[dict] = deque(maxlen=100)
        self.history: deque[dict] = deque(maxlen=120)
        self.latest: dict | None = None
        self._lock = Lock()

    def set_scenario(self, scenario: Scenario) -> None:
        scenario = Scenario(scenario)
        with self._lock:
            if scenario != self.scenario:
                self.frozen = None
            self.scenario = scenario

    async def poll(
        self, *, utc_now: datetime | None = None, monotonic_now: float | None = None
    ) -> dict:
        # Streamlit fast reruns may overlap two script threads for the same
        # browser session. Never interleave simulator/diagnostic mutations.
        if not self._lock.acquire(blocking=False):
            if self.latest is not None:
                return self.latest
            raise RuntimeError("Initial poll already in progress")
        try:
            return await self._poll_locked(utc_now=utc_now, monotonic_now=monotonic_now)
        finally:
            self._lock.release()

    async def _poll_locked(
        self, *, utc_now: datetime | None = None, monotonic_now: float | None = None
    ) -> dict:
        generated_at = utc_now or datetime.now(UTC)
        sample, error, invalid = None, None, None
        read_succeeded = False
        server = LocalModbusServer(0)
        try:
            await server.start()
            if self.scenario == Scenario.FREEZE:
                if self.frozen is None:
                    self.frozen = self.simulator.sample(generated_at)
                generated = self.frozen
            else:
                generated = self.simulator.sample(generated_at)
            registers = encode(generated)
            if self.scenario == Scenario.INVALID:
                registers[10] = 65535
            server.publish(registers)
            port = server.port
            if self.scenario == Scenario.DISCONNECT:
                # A real closed listener, followed by a real client request.
                await server.stop()
            try:
                registers = await ModbusPoller(port, timeout=0.5, retries=0).read_registers()
                read_succeeded = True
                try:
                    sample = decode(registers)
                except ValueError as exc:
                    invalid = str(exc)
            except TransportError as exc:
                error = str(exc)
        finally:
            await server.stop()
        observed_at = utc_now or datetime.now(UTC)
        diagnosis, events = self.engine.observe(
            monotonic_now=time.monotonic() if monotonic_now is None else monotonic_now,
            utc_now=observed_at,
            sample=sample,
            error=error,
            invalid=invalid,
        )
        self.events.extend(events)
        if sample and diagnosis["state"] == Health.HEALTHY:
            if (
                not self.history
                or self.history[-1]["sequence_number"] != sample.sequence_number
            ):
                self.history.append(sample.to_dict())
        self.latest = {
            "diagnosis": diagnosis,
            "sample": sample.to_dict() if sample else None,
            "scenario": self.scenario.value,
            "observed_at_utc": observed_at.isoformat(),
            "read_succeeded": read_succeeded,
            "port": port,
            "history": list(self.history),
            "events": list(self.events),
            "transport": "real_loopback_modbus_tcp",
            "listener_closed": not server.running,
        }
        return self.latest
