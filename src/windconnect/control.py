"""Local file IPC: command acknowledgement does not imply fault detection."""

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from windconnect.storage import atomic_json, read_json


class Scenario(StrEnum):
    NORMAL = "normal"
    DISCONNECT = "disconnect"
    FREEZE = "freeze"
    INVALID = "invalid"


def send_command(directory: Path, scenario: Scenario) -> str:
    command_id = str(uuid4())
    atomic_json(
        directory / "control.json",
        {
            "id": command_id,
            "scenario": Scenario(scenario).value,
            "requested_at": datetime.now(UTC).isoformat(),
        },
    )
    return command_id


def read_command(directory: Path) -> dict | None:
    value = read_json(directory / "control.json")
    if value is not None:
        if not isinstance(value.get("id"), str) or not value["id"]:
            raise ValueError("Demo-Befehl ohne gültige ID")
        Scenario(value.get("scenario"))
    return value
