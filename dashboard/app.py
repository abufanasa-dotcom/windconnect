"""German support dashboard. No long-lived server/client starts on UI reruns."""

import json
import os
from datetime import UTC, datetime
from pathlib import Path

import streamlit as st

from windconnect.control import Scenario, read_command, send_command
from windconnect.presentation import (
    backend_available,
    snapshot_age,
    utc_label,
    validate_snapshot,
)
from windconnect.runner import DEFAULT_DATA
from windconnect.storage import StateStore, read_json

DIRECTORY = Path(os.environ.get("WINDCONNECT_DATA_DIR", DEFAULT_DATA))
LABELS = {
    "normal": "Normalbetrieb",
    "freeze": "Daten einfrieren",
    "disconnect": "Verbindung unterbrechen",
    "invalid": "Ungültigen Messwert senden",
}
STATES = {"RUNNING": "In Betrieb", "STOPPED": "Gestoppt", "FAULT": "Anlagenfehler"}

st.set_page_config(
    page_title="WindConnect | VPP-Verbindungsdiagnose",
    page_icon=":material/wind_power:",
    layout="wide",
)
st.title("WindConnect – VPP-Verbindungsdiagnose (Simulation)")
st.caption("Demonstrationsprojekt – keine Verbindung zu realen Anlagen oder emsys-Systemen")

with st.sidebar:
    st.header("WindConnect", icon=":material/wind_power:")
    st.caption("SUPPORT & DIAGNOSTIK · LOKALE DEMO")
    st.subheader("Demo-Steuerung")
    st.caption(
        "Szenario anfordern. Die Diagnose folgt erst aus den beobachteten Modbus-Antworten."
    )
    for mode, label in LABELS.items():
        if st.button(label, key=f"scenario_{mode}", width="stretch"):
            try:
                send_command(DIRECTORY, Scenario(mode))
                st.toast("Demo-Befehl gesendet. Auf Beobachtung warten.")
            except OSError as exc:
                st.error(f"Demo-Befehl konnte nicht gespeichert werden: {exc}")
    if st.button("Fehler zurücksetzen", key="reset", type="primary", width="stretch"):
        try:
            send_command(DIRECTORY, Scenario.NORMAL)
            st.toast("Normalbetrieb angefordert.")
        except OSError as exc:
            st.error(f"Zurücksetzen fehlgeschlagen: {exc}")
    st.divider()
    automatic = st.toggle("Automatisch aktualisieren (1 s)", value=True, key="autorefresh")
    st.button("Jetzt aktualisieren", icon=":material/refresh:", width="stretch")
    st.caption("100 % synthetische Messwerte · 3-MW-Modell · nur Loopback")


@st.fragment(run_every=1 if automatic else None)
def monitoring():
    try:
        state = read_json(DIRECTORY / "state.json")
        if state is None:
            st.info("Noch keine Daten. Bitte das Backend in einem zweiten Terminal starten.")
            st.code("python -m windconnect.runner", language="powershell")
            return
        validate_snapshot(state)
        store = StateStore(DIRECTORY)
        events = store.events()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        st.error(f"Lokale Zustandsdatei nicht lesbar oder ungültig: {exc}")
        st.caption("Backend-Log prüfen und die Ansicht erneut aktualisieren.")
        return
    diagnosis = state["diagnosis"]
    available = backend_available(state)
    healthy = available and diagnosis["state"] == "HEALTHY"
    status = "Online · HEALTHY" if healthy else f"Störung · {diagnosis['state']}"
    if not available:
        status = "Backend nicht aktiv · historische Diagnose"
    st.subheader("Anlagenstatus")
    message = f"{status} — {diagnosis['explanation']}"
    if healthy:
        st.success(message, icon=":material/check_circle:")
    elif not available:
        st.error(
            "Backend nicht aktiv. Angezeigte Messwerte sind historisch.",
            icon=":material/cloud_off:",
        )
    elif diagnosis["state"] == "STALE_DATA":
        st.warning(message, icon=":material/schedule:")
    else:
        st.error(message, icon=":material/error:")
    st.caption(
        f"{state['endpoint']} · Letzter erfolgreicher Kontakt: "
        f"{utc_label(diagnosis['last_contact_utc'])} · "
        f"Snapshot-Alter: {snapshot_age(state):.1f} s"
    )
    try:
        command = read_command(DIRECTORY)
        if command and command["id"] != state.get("ack_id"):
            st.info(f"Angefordert: {LABELS[command['scenario']]} · wartet auf Backend")
        else:
            st.caption(
                f"Backend-Szenario: {LABELS[state['scenario']]} · "
                f"Beobachtete Diagnose: {diagnosis['state']}"
            )
    except (OSError, ValueError, KeyError) as exc:
        st.warning(f"Demo-Steuerdatei prüfen: {exc}")
    if state.get("command_error"):
        st.warning(state["command_error"])
    st.subheader("Messwerte")
    sample = state.get("sample") or diagnosis.get("last_good")
    if not sample:
        st.info("Noch keine gültigen Messwerte verfügbar.")
    else:
        if not healthy:
            st.caption(
                "Historische / zuletzt lesbare Werte — kein Nachweis aktueller Anlagendaten."
            )
        age = max(
            0,
            (
                datetime.now(UTC) - datetime.fromisoformat(sample["timestamp_utc"])
            ).total_seconds(),
        )
        with st.container(horizontal=True):
            st.metric("Leistung", f"{sample['power_kw']:,.1f} kW", border=True)
            st.metric("Windgeschwindigkeit", f"{sample['wind_speed_mps']:.2f} m/s", border=True)
            st.metric(
                "Betriebszustand",
                STATES.get(sample["operating_state"], "Unbekannt"),
                border=True,
            )
            st.metric("Alter der Messwerte", f"{age:.1f} s", border=True)
        st.caption(
            f"Messzeit: {utc_label(sample['timestamp_utc'])} · "
            f"Sequenz: {sample['sequence_number']} · alle Werte synthetisch"
        )
    left, right = st.columns([1.15, 1])
    with left, st.container(border=True):
        st.subheader("Leistungsverlauf")
        history = state.get("history", [])
        if history:
            chart_data = [
                {
                    "Messzeit (Browser-Zeit)": datetime.fromisoformat(row["timestamp_utc"]),
                    "Leistung (kW)": row["power_kw"],
                }
                for row in history
            ]
            st.line_chart(
                chart_data,
                x="Messzeit (Browser-Zeit)",
                y="Leistung (kW)",
                height=220,
                alt="Verlauf der zuletzt gültigen synthetischen Leistungsmessungen",
            )
        else:
            st.info("Der Verlauf beginnt mit der ersten gesunden Messung.")
        st.caption("Letzte 120 gesunde Messungen dieses Backend-Laufs; bei Fehlern pausiert.")
    with right, st.container(border=True):
        st.subheader("Fehlerdiagnose")
        st.markdown(f"**{diagnosis['state']}** · {diagnosis['severity']}")
        st.text(diagnosis["evidence"])
        st.markdown("**Empfohlene nächste Prüfung**")
        for check in diagnosis["checks"]:
            st.markdown(f"- {check}")
        st.caption(
            "Diagnostische Hinweise; keine automatischen Eingriffe in Anlagen oder Netzwerke."
        )
    st.subheader("Ereignisprotokoll")
    if events:
        rows = [
            {
                "Zeit (UTC)": utc_label(event["timestamp_utc"]),
                "Ereignis": event["kind"],
                "Schweregrad": event["severity"],
                "Beschreibung": event["explanation"],
                "Beobachtung": event["evidence"],
            }
            for event in reversed(events)
        ]
        st.dataframe(
            rows,
            hide_index=True,
            height=240,
            alt="Diagnosewechsel und Wiederherstellungen mit UTC-Zeitstempeln",
        )
        st.caption("Letzte 100 Ereignisse, einschließlich früherer Backend-Läufe.")
    else:
        st.info("Noch keine Diagnoseereignisse vorhanden.")
    with st.expander("Diagnosebericht exportieren"):
        st.download_button(
            "Snapshot und Ereignisse herunterladen",
            json.dumps({"snapshot": state, "events": events}, ensure_ascii=False, indent=2),
            file_name="windconnect_diagnose.json",
            mime="application/json",
        )


monitoring()
