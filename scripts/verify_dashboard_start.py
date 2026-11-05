"""Start a fresh local Streamlit subprocess, check HTTP health, and clean up."""

import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    output = root / "data" / "dashboard-startup.log"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as log:
        # Stop inside the interpreter, not just the Windows venv launcher.
        # This disposable HTTP smoke process has no persistent resources.
        watchdog = (
            "import os,sys,threading; "
            "timer=threading.Timer(10, lambda: os._exit(0)); "
            "timer.daemon=True; timer.start(); "
            "sys.argv[0]='streamlit'; "
            "from streamlit.web.cli import main; main()"
        )
        process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                watchdog,
                "run",
                "dashboard/app.py",
                "--server.address",
                "127.0.0.1",
                "--server.port",
                str(port),
            ],
            cwd=root,
            stdout=log,
            stderr=log,
        )
        try:
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"Streamlit exited: {process.returncode}; see {output}")
                try:
                    with urllib.request.urlopen(
                        f"http://127.0.0.1:{port}/_stcore/health",
                        timeout=1,
                    ) as response:
                        assert response.read() == b"ok"
                    print("Clean Streamlit HTTP startup: ok")
                    break
                except (urllib.error.URLError, TimeoutError):
                    time.sleep(0.1)
            else:
                raise TimeoutError("Streamlit startup deadline exceeded")
        finally:
            process.wait(timeout=12)
    # Windows can retain TIME_WAIT after the HTTP check; test reachability
    # rather than treating an immediate exclusive rebind as listener evidence.
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.3):
            raise RuntimeError("Streamlit listener remained reachable after process exit")
    except OSError:
        pass
    print("Streamlit smoke process stopped; listener unreachable")


if __name__ == "__main__":
    main()
