from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "public_dashboard" / "app.py"


def test_public_dashboard_fault_controls_language_and_recovery():
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    assert not app.exception
    assert "Modbus-TCP-Monitoring" in app.title[0].value
    assert "HEALTHY" in app.success[0].value
    app.button(key="demo_disconnect").click().run()
    assert not app.exception
    assert "CONNECTION_LOST" in app.error[0].value
    app.button(key="demo_reset").click().run()
    assert not app.exception
    assert "HEALTHY" in app.success[0].value
    app.button(key="demo_invalid").click().run()
    assert not app.exception
    assert "INVALID_MEASUREMENT" in app.error[0].value
    app.segmented_control(key="lang").set_value("en").run()
    assert not app.exception
    assert "Modbus TCP Monitoring" in app.title[0].value
    assert "invalid measurement" in app.error[0].value
    assert "Active power" in [metric.label for metric in app.metric]
    assert "RECOVERED" in app.dataframe[0].value["Event"].tolist()
    app.button(key="demo_reset").click().run()
    assert not app.exception
    assert "HEALTHY" in app.success[0].value


def test_public_dashboard_independent_browser_sessions():
    first = AppTest.from_file(str(APP), default_timeout=20).run()
    first.button(key="demo_invalid").click().run()
    second = AppTest.from_file(str(APP), default_timeout=20).run()
    assert not first.exception and not second.exception
    assert first.session_state.public_demo.latest["diagnosis"]["state"] == "INVALID_MEASUREMENT"
    assert second.session_state.public_demo.latest["diagnosis"]["state"] == "HEALTHY"
