"""Atomic snapshots, bounded event logs, and single-writer runtime ownership."""

import json
import os
import tempfile
import time
from collections import deque
from contextlib import contextmanager
from pathlib import Path


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, ensure_ascii=False, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        for attempt in range(5):
            try:
                os.replace(temporary, path)
                break
            except PermissionError:
                if attempt == 4:
                    raise
                time.sleep(0.02)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def read_json(path: Path) -> dict | None:
    try:
        for attempt in range(5):
            try:
                with path.open(encoding="utf-8") as stream:
                    result = json.load(stream)
                break
            except PermissionError:
                if attempt == 4:
                    raise
                time.sleep(0.02)
        if not isinstance(result, dict):
            raise ValueError(f"{path.name}: JSON-Objekt erwartet")
        return result
    except FileNotFoundError:
        return None


class StateStore:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()
        self.directory.mkdir(parents=True, exist_ok=True)

    def snapshot(self, value: dict) -> None:
        atomic_json(self.directory / "state.json", value)

    def append_event(self, event: dict) -> None:
        path = self.directory / "events.jsonl"
        if path.exists() and path.stat().st_size >= 1_000_000:
            os.replace(path, self.directory / "events.previous.jsonl")
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False, allow_nan=False) + "\n")

    def events(self, limit: int = 100) -> list[dict]:
        recent = deque(maxlen=limit)
        for name in ("events.previous.jsonl", "events.jsonl"):
            try:
                with (self.directory / name).open(encoding="utf-8") as stream:
                    for line in stream:
                        try:
                            value = json.loads(line)
                            if isinstance(value, dict):
                                recent.append(value)
                        except json.JSONDecodeError:
                            continue  # A concurrent/incomplete final JSONL line is ignored.
            except FileNotFoundError:
                pass
        return list(recent)

    @contextmanager
    def ownership(self):
        """OS lock is released on crash too; never delete a live lock file."""
        with (self.directory / "runner.lock").open("a+b") as stream:
            stream.seek(0, os.SEEK_END)
            if stream.tell() == 0:
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            if os.name == "nt":
                import msvcrt

                try:
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError as exc:
                    raise RuntimeError(
                        "Für dieses Datenverzeichnis läuft bereits ein Backend"
                    ) from exc
            else:
                import fcntl

                try:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError as exc:
                    raise RuntimeError(
                        "Für dieses Datenverzeichnis läuft bereits ein Backend"
                    ) from exc
            try:
                yield
            finally:
                stream.seek(0)
                if os.name == "nt":
                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
