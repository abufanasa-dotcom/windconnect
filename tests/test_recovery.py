import asyncio
import socket

from windconnect.control import Scenario, send_command
from windconnect.runner import run_backend
from windconnect.storage import StateStore, read_json


def test_complete_backend_fault_walkthrough_and_restart(runtime_dir):
    async def scenario():
        # Reserve then release an ephemeral port; actual server bind still validates ownership.
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        stop = asyncio.Event()
        task = asyncio.create_task(
            run_backend(
                directory=runtime_dir,
                port=port,
                interval=0.1,
                stale_after=0.5,
                timeout=0.4,
                retries=0,
                stop=stop,
            )
        )

        async def wait_for_state(expected, ack=None):
            async with asyncio.timeout(4):
                while True:
                    if task.done():
                        task.result()
                        raise AssertionError("Backend stopped unexpectedly")
                    state = read_json(runtime_dir / "state.json")
                    if state and state["diagnosis"]["state"] == expected:
                        if ack is None or state["ack_id"] == ack:
                            return state
                    await asyncio.sleep(0.02)

        try:
            first = await wait_for_state("HEALTHY")
            for mode, expected in [
                (Scenario.FREEZE, "STALE_DATA"),
                (Scenario.DISCONNECT, "CONNECTION_LOST"),
                (Scenario.INVALID, "INVALID_MEASUREMENT"),
            ]:
                ack = send_command(runtime_dir, mode)
                state = await wait_for_state(expected, ack)
                assert state["diagnosis"]["last_good"]
                reset = send_command(runtime_dir, Scenario.NORMAL)
                await wait_for_state("HEALTHY", reset)
            # Malformed commands cannot crash the backend or change normal operation.
            (runtime_dir / "control.json").write_text("broken", encoding="utf-8")
            await asyncio.sleep(0.3)
            state = read_json(runtime_dir / "state.json")
            assert state["command_error"]
            assert state["diagnosis"]["state"] == "HEALTHY"
            events = StateStore(runtime_dir).events()
            assert sum(event["kind"] == "RECOVERED" for event in events) == 3
            assert all(event["run_id"] == first["run_id"] for event in events)
        finally:
            stop.set()
            await asyncio.wait_for(task, 3)
        assert read_json(runtime_dir / "state.json")["backend_running"] is False
        # Old fault commands must not replay on restart.
        send_command(runtime_dir, Scenario.DISCONNECT)
        await run_backend(
            directory=runtime_dir,
            port=port,
            interval=0.1,
            stale_after=0.5,
            timeout=0.4,
            retries=0,
            duration=0.3,
        )
        state = read_json(runtime_dir / "state.json")
        assert state["scenario"] == "normal"
        assert state["diagnosis"]["state"] == "HEALTHY"

    asyncio.run(asyncio.wait_for(scenario(), timeout=20))
