from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from windconnect.diagnostics import DiagnosticsEngine
from windconnect.presentation import backend_available
from windconnect.simulator import TurbineSimulator
from windconnect.storage import StateStore, read_json

APP = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"


def seed_state(directory, health="HEALTHY", running=True):
    now = datetime.now(UTC)
    sample = TurbineSimulator().sample(now)
    diagnosis, events = DiagnosticsEngine().observe(
        monotonic_now=0,
        utc_now=now,
        sample=sample,
    )
    diagnosis["state"] = health
    state = {
        "schema_version": 1,
        "updated_at_utc": now.isoformat(),
        "run_id": "test",
        "backend_running": running,
        "interval": 1,
        "timeout": 0.5,
        "retries": 1,
        "diagnosis": diagnosis,
        "sample": sample.to_dict(),
        "history": [sample.to_dict()],
        "endpoint": "127.0.0.1:15020",
        "scenario": "normal",
        "ack_id": None,
    }
    store = StateStore(directory)
    store.snapshot(state)
    for event in events:
        store.append_event(event)
    return state


def test_no_data_and_corrupt_snapshot(runtime_dir, monkeypatch):
    monkeypatch.setenv("WINDCONNECT_DATA_DIR", str(runtime_dir))
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not app.exception
    assert "Noch keine Daten" in app.info[0].value
    (runtime_dir / "state.json").write_text("broken", encoding="utf-8")
    app.run()
    assert not app.exception
    assert "Zustandsdatei" in app.error[0].value


@pytest.mark.parametrize(
    "health", ["HEALTHY", "CONNECTION_LOST", "STALE_DATA", "INVALID_MEASUREMENT"]
)
def test_all_diagnostic_states_render(runtime_dir, monkeypatch, health):
    monkeypatch.setenv("WINDCONNECT_DATA_DIR", str(runtime_dir))
    seed_state(runtime_dir, health)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not app.exception
    assert len(app.metric) == 4
    alerts = list(app.success) + list(app.error) + list(app.warning)
    assert any(health in alert.value for alert in alerts)
    assert app.dataframe


def test_controls_send_ipc_without_fabricating_diagnosis(runtime_dir, monkeypatch):
    monkeypatch.setenv("WINDCONNECT_DATA_DIR", str(runtime_dir))
    seed_state(runtime_dir)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    for action in ("freeze", "disconnect", "invalid", "normal"):
        app.button(key=f"scenario_{action}").click().run()
        assert not app.exception
        assert read_json(runtime_dir / "control.json")["scenario"] == action
        assert read_json(runtime_dir / "state.json")["diagnosis"]["state"] == "HEALTHY"
        assert any("wartet auf Backend" in item.value for item in app.info)
    app.button(key="reset").click().run()
    assert not app.exception
    assert read_json(runtime_dir / "control.json")["scenario"] == "normal"
    app.toggle(key="autorefresh").set_value(False).run()
    assert not app.exception


def test_stopped_backend_never_appears_online(runtime_dir, monkeypatch):
    monkeypatch.setenv("WINDCONNECT_DATA_DIR", str(runtime_dir))
    state = seed_state(runtime_dir, running=False)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not app.exception
    assert not app.success
    assert "historisch" in app.error[0].value
    state["backend_running"] = True
    assert not backend_available(state, datetime.now(UTC) + timedelta(seconds=20))
