"""Reproducible demo scenarios without dashboard side effects."""

import argparse
from pathlib import Path

from windconnect.control import Scenario, send_command
from windconnect.runner import DEFAULT_DATA
from windconnect.storage import read_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Lokale WindConnect-Demo-Steuerung")
    parser.add_argument(
        "action", choices=[*(item.value for item in Scenario), "reset", "status"]
    )
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    args = parser.parse_args()
    if args.action == "status":
        state = read_json(args.data_dir / "state.json")
        if not state:
            parser.exit(1, "Noch kein Backend-Snapshot vorhanden.\n")
        print(state)
    else:
        scenario = Scenario.NORMAL if args.action == "reset" else Scenario(args.action)
        print(f"Befehl gesendet: {scenario.value}; ID {send_command(args.data_dir, scenario)}")
        print("Die beobachtete Diagnose erscheint erst nach dem nächsten Poll.")


if __name__ == "__main__":
    main()
