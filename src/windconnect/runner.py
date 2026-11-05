"""One backend process, one asyncio loop, separate real TCP polling client."""

import argparse
import asyncio
import logging
import time
from collections import deque
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from uuid import uuid4

from windconnect.control import Scenario, read_command
from windconnect.diagnostics import DiagnosticsEngine
from windconnect.modbus_client import ModbusPoller, TransportError
from windconnect.modbus_server import LocalModbusServer
from windconnect.registers import decode, encode
from windconnect.simulator import TurbineSimulator
from windconnect.storage import StateStore

DEFAULT_DATA = Path(__file__).resolve().parents[2] / "data"
LOGGER = logging.getLogger("windconnect")


async def run_backend(
    *,
    directory: Path = DEFAULT_DATA,
    port: int = 15020,
    interval: float = 1,
    stale_after: float = 5,
    timeout: float = 0.5,
    retries: int = 1,
    seed: int = 42,
    duration: float | None = None,
    stop: asyncio.Event | None = None,
) -> None:
    if interval <= 0 or stale_after < interval * 2 or (duration is not None and duration <= 0):
        raise ValueError(
            "Intervall > 0; Stale-Schwelle >= 2 Intervalle; Dauer > 0 erforderlich"
        )
    poller = ModbusPoller(port, timeout, retries)
    store = StateStore(directory)
    simulator = TurbineSimulator(seed)
    engine = DiagnosticsEngine(stale_after)
    server = LocalModbusServer(port)
    run_id = str(uuid4())
    history = deque(maxlen=120)
    scenario, ack_id = Scenario.NORMAL, None
    frozen = None
    snapshot = {}
    began = time.monotonic()
    with store.ownership():
        try:
            # A stale control file must never replay a fault on a new backend run.
            try:
                old_command = read_command(directory)
                ack_id = old_command["id"] if old_command else None
            except (ValueError, OSError):
                pass
            await server.start()
            while not (stop and stop.is_set()):
                tick = time.monotonic()
                if duration is not None and tick - began >= duration:
                    break
                command_error = None
                try:
                    command = read_command(directory)
                    if command and command["id"] != ack_id:
                        scenario = Scenario(command["scenario"])
                        ack_id = command["id"]
                        frozen = None
                        LOGGER.info("Demo-Szenario angefordert: %s", scenario)
                except (ValueError, OSError) as exc:
                    command_error = f"Demo-Befehl nicht lesbar: {exc}"
                    LOGGER.warning(command_error)
                now = datetime.now(UTC)
                if scenario == Scenario.DISCONNECT:
                    await server.stop()
                else:
                    await server.start()
                    if scenario == Scenario.FREEZE:
                        if frozen is None:
                            frozen = simulator.sample(now)
                        generated = frozen
                    else:
                        generated = simulator.sample(now)
                    registers = encode(generated)
                    if scenario == Scenario.INVALID:
                        registers[10] = 65535  # 655.35 m/s, over the documented limit.
                    server.publish(registers)
                sample, error, invalid = None, None, None
                try:
                    registers = await poller.read_registers()
                    try:
                        sample = decode(registers)
                    except ValueError as exc:
                        invalid = str(exc)
                except TransportError as exc:
                    error = str(exc)
                observed = datetime.now(UTC)
                diagnosis, events = engine.observe(
                    monotonic_now=time.monotonic(),
                    utc_now=observed,
                    sample=sample,
                    error=error,
                    invalid=invalid,
                )
                for event in events:
                    event["run_id"] = run_id
                    store.append_event(event)
                    LOGGER.info("Diagnose %s: %s", event["kind"], event["evidence"])
                if sample is not None and diagnosis["state"] == "HEALTHY":
                    history.append(sample.to_dict())
                snapshot = {
                    "schema_version": 1,
                    "run_id": run_id,
                    "backend_running": True,
                    "updated_at_utc": observed.isoformat(),
                    "synthetic": True,
                    "endpoint": f"127.0.0.1:{port}",
                    "scenario": scenario.value,
                    "ack_id": ack_id,
                    "command_error": command_error,
                    "diagnosis": diagnosis,
                    "sample": sample.to_dict() if sample else None,
                    "history": list(history),
                    "interval": interval,
                    "timeout": timeout,
                    "retries": retries,
                    "stale_after": stale_after,
                }
                store.snapshot(snapshot)
                delay = max(0, interval - (time.monotonic() - tick))
                if stop is not None:
                    try:
                        await asyncio.wait_for(stop.wait(), timeout=delay)
                    except TimeoutError:
                        pass
                else:
                    await asyncio.sleep(delay)
        finally:
            await server.stop()
            if snapshot:
                snapshot.update(
                    backend_running=False, updated_at_utc=datetime.now(UTC).isoformat()
                )
                store.snapshot(snapshot)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="WindConnect: ausschließlich lokale Simulation"
    )
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--port", type=int, default=15020)
    parser.add_argument("--interval", type=float, default=1)
    parser.add_argument("--stale-after", type=float, default=5)
    parser.add_argument("--timeout", type=float, default=0.5)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--duration", type=float)
    args = parser.parse_args()
    args.data_dir.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        args.data_dir / "backend.log", maxBytes=1_000_000, backupCount=1, encoding="utf-8"
    )
    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler, logging.StreamHandler()],
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    try:
        asyncio.run(
            run_backend(
                directory=args.data_dir,
                port=args.port,
                interval=args.interval,
                stale_after=args.stale_after,
                timeout=args.timeout,
                retries=args.retries,
                seed=args.seed,
                duration=args.duration,
            )
        )
    except KeyboardInterrupt:
        LOGGER.info("Backend beendet")
    except (ValueError, OSError, RuntimeError) as exc:
        LOGGER.error("Start/Betrieb fehlgeschlagen: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
