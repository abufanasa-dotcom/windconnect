"""Dashboard view helpers; an old HEALTHY snapshot must never appear online."""

from datetime import UTC, datetime


def snapshot_age(state: dict, now: datetime | None = None) -> float:
    stamp = datetime.fromisoformat(state["updated_at_utc"])
    if stamp.tzinfo is None:
        raise ValueError("Snapshot-Zeitstempel ohne Zeitzone")
    age = ((now or datetime.now(UTC)) - stamp).total_seconds()
    if age < -2:
        raise ValueError("Snapshot-Zeitstempel liegt in der Zukunft")
    return max(0, age)


def backend_available(state: dict, now: datetime | None = None) -> bool:
    deadline = max(5, 3 * state["interval"] + (state["retries"] + 1) * state["timeout"])
    return bool(state["backend_running"] and snapshot_age(state, now) < deadline)


def validate_snapshot(state: dict) -> None:
    if state.get("schema_version") != 1:
        raise ValueError("Snapshot-Version unbekannt")
    if state["diagnosis"]["state"] not in {
        "HEALTHY",
        "STALE_DATA",
        "CONNECTION_LOST",
        "INVALID_MEASUREMENT",
    }:
        raise ValueError("Diagnosestatus unbekannt")
    snapshot_age(state)
    backend_available(state)
    for field in ("sample",):
        sample = state.get(field)
        if sample is not None:
            float(sample["power_kw"])
            float(sample["wind_speed_mps"])
            datetime.fromisoformat(sample["timestamp_utc"])


def utc_label(value: str | None) -> str:
    if not value:
        return "Noch kein Kontakt"
    return datetime.fromisoformat(value).astimezone(UTC).strftime("%d.%m.%Y %H:%M:%S UTC")
