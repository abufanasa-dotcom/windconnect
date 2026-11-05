from concurrent.futures import ThreadPoolExecutor

import pytest

from windconnect.control import Scenario, read_command, send_command
from windconnect.storage import StateStore, atomic_json, read_json


def test_atomic_snapshot_concurrent_readers(runtime_dir):
    path = runtime_dir / "state.json"
    atomic_json(path, {"counter": 0})

    def writer():
        for counter in range(30):
            atomic_json(path, {"counter": counter, "data": "x" * 1000})

    with ThreadPoolExecutor(max_workers=2) as pool:
        future = pool.submit(writer)
        for _ in range(100):
            assert isinstance(read_json(path)["counter"], int)
        future.result(timeout=10)
    assert not list(runtime_dir.glob("*.tmp"))


def test_missing_corrupt_and_non_object(runtime_dir):
    path = runtime_dir / "state.json"
    assert read_json(path) is None
    path.write_text("broken", encoding="utf-8")
    with pytest.raises(ValueError):
        read_json(path)
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError):
        read_json(path)


def test_events_tail_rotation_and_partial_line(runtime_dir):
    store = StateStore(runtime_dir)
    assert store.events() == []
    for i in range(3):
        store.append_event({"kind": "TEST", "index": i})
    with (runtime_dir / "events.jsonl").open("a", encoding="utf-8") as stream:
        stream.write("partial\n")
    assert [e["index"] for e in store.events(2)] == [1, 2]
    with (runtime_dir / "events.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(" " * 1_000_000 + "\n")
    store.append_event({"kind": "NEW"})
    assert (runtime_dir / "events.previous.jsonl").exists()
    assert store.events()[-1]["kind"] == "NEW"


def test_commands_and_validation(runtime_dir):
    assert read_command(runtime_dir) is None
    command_id = send_command(runtime_dir, Scenario.FREEZE)
    assert read_command(runtime_dir)["id"] == command_id
    atomic_json(runtime_dir / "control.json", {"scenario": "normal"})
    with pytest.raises(ValueError):
        read_command(runtime_dir)


def test_runtime_lock_is_exclusive_and_released(runtime_dir):
    a, b = StateStore(runtime_dir), StateStore(runtime_dir)
    with a.ownership():
        with pytest.raises((RuntimeError, OSError)):
            with b.ownership():
                pytest.fail("second writer acquired lock")
    with b.ownership():
        pass
