"""Bounded clean-process walkthrough. Run from the repository root."""

import json
import socket
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from windconnect.storage import StateStore, read_json


def main():
    root = Path(__file__).resolve().parents[1]
    scratch = root / "data" / "smoke"
    scratch.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(dir=scratch) as temporary:
        directory = Path(temporary)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        with (directory / "output.log").open("w", encoding="utf-8") as log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "windconnect.runner",
                    "--data-dir",
                    str(directory),
                    "--port",
                    str(port),
                    "--interval",
                    "0.2",
                    "--stale-after",
                    "0.6",
                    "--timeout",
                    "0.5",
                    "--retries",
                    "0",
                    "--duration",
                    "10",
                ],
                cwd=root,
                stdout=log,
                stderr=log,
            )
            try:
                for action, expected in [
                    (None, "HEALTHY"),
                    ("freeze", "STALE_DATA"),
                    ("reset", "HEALTHY"),
                    ("disconnect", "CONNECTION_LOST"),
                    ("reset", "HEALTHY"),
                    ("invalid", "INVALID_MEASUREMENT"),
                    ("reset", "HEALTHY"),
                ]:
                    if action:
                        subprocess.run(
                            [
                                sys.executable,
                                "-m",
                                "windconnect.cli",
                                action,
                                "--data-dir",
                                str(directory),
                            ],
                            cwd=root,
                            check=True,
                            timeout=3,
                            capture_output=True,
                        )
                    deadline = time.monotonic() + 4
                    while time.monotonic() < deadline:
                        state = read_json(directory / "state.json")
                        command = read_json(directory / "control.json")
                        acknowledged = not action or (
                            state and state["ack_id"] == command["id"]
                        )
                        if state and acknowledged and state["diagnosis"]["state"] == expected:
                            results.append(expected)
                            break
                        if process.poll() is not None:
                            raise RuntimeError("Backend exited before completing walkthrough")
                        time.sleep(0.05)
                    else:
                        raise TimeoutError(f"Expected {expected}; got {state}")
                assert process.wait(timeout=12) == 0
                state = read_json(directory / "state.json")
                assert state["backend_running"] is False
                events = StateStore(directory).events()
                assert sum(event["kind"] == "RECOVERED" for event in events) == 3
                with socket.socket() as probe:
                    probe.bind(("127.0.0.1", port))
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=3)
    report = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "python": sys.version,
        "observed_states": results,
        "recoveries": 3,
        "process_exit": 0,
        "port_released": True,
    }
    output = root / "data" / "smoke-result.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
