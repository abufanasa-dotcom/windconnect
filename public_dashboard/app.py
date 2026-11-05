"""Bilingual public demo: real loopback Modbus, bounded lifecycle, session isolation."""

import asyncio
import json
from datetime import UTC, datetime

import streamlit as st

from windconnect.control import Scenario
from windconnect.presentation import utc_label
from windconnect.public_demo import PublicDemoSession
from windconnect.public_text import messages

st.set_page_config(
    page_title="WindConnect | Modbus TCP Monitoring",
    page_icon=":material/wind_power:",
    layout="wide",
)
if "public_demo" not in st.session_state:
    st.session_state.public_demo = PublicDemoSession()
demo = st.session_state.public_demo
with st.sidebar:
    st.header("WindConnect", icon=":material/wind_power:")
    language = st.segmented_control(
        "Sprache / Language",
        options=["de", "en"],
        default="de",
        format_func=lambda value: {"de": "Deutsch", "en": "English"}[value],
        key="lang",
        bind="query-params",
    )
    language = language if language in {"de", "en"} else "de"
    text = messages(language)
    st.subheader(text["controls"])
    for scenario in Scenario:
        if st.button(text[scenario.value], key=f"demo_{scenario.value}", width="stretch"):
            demo.set_scenario(scenario)
    if st.button(text["reset"], key="demo_reset", type="primary", width="stretch"):
        demo.set_scenario(Scenario.NORMAL)
    st.divider()
    automatic = st.toggle(text["automatic"], value=True, key="public_automatic")
    st.button(text["refresh"], key="public_poll", icon=":material/refresh:", width="stretch")
    st.caption(text["isolated"])
    st.link_button(text["source"], "https://github.com/abufanasa-dotcom/windconnect")

st.title(text["title"])
st.caption(text["subtitle"])


@st.fragment(run_every=1 if automatic else None)
def monitor():
    try:
        snapshot = asyncio.run(demo.poll())
    except (OSError, RuntimeError, ValueError):
        st.error(text["error"])
        return
    diagnosis = snapshot["diagnosis"]
    state = diagnosis["state"]
    st.subheader(text["status"])
    alert = (
        st.success if state == "HEALTHY" else st.warning if state == "STALE_DATA" else st.error
    )
    alert(f"{state} · {text[state]}")
    st.caption(
        f"{text['scenario']}: {text[snapshot['scenario']]} · {text['observed']}: {state}"
    )
    read_status = text["success"] if snapshot["read_succeeded"] else text["failed"]
    contact = diagnosis["last_contact_utc"]
    st.caption(
        f"{text['read']}: {read_status} · {text['contact']}: "
        f"{utc_label(contact) if contact else text['none']}"
    )
    st.subheader(text["measurements"])
    sample = snapshot["sample"] or diagnosis["last_good"]
    age = None
    if sample:
        age = max(
            0,
            (
                datetime.now(UTC) - datetime.fromisoformat(sample["timestamp_utc"])
            ).total_seconds(),
        )
        if state != "HEALTHY":
            st.caption(text["historical"])
        power = f"{sample['power_kw']:.1f}"
        wind = f"{sample['wind_speed_mps']:.2f}"
        if language == "de":
            power, wind = power.replace(".", ","), wind.replace(".", ",")
        with st.container(horizontal=True):
            st.metric(text["power"], power + " kW", border=True)
            st.metric(text["wind"], wind + " m/s", border=True)
            st.metric(text["operating"], text[sample["operating_state"]], border=True)
            age_label = f"{age:.1f}"
            if language == "de":
                age_label = age_label.replace(".", ",")
            st.metric(text["age"], age_label + " s", border=True)
        st.caption(
            f"{text['timestamp']}: {utc_label(sample['timestamp_utc'])} · "
            f"{text['sequence']}: {sample['sequence_number']}"
        )
    else:
        st.info(text["missing"])
    left, right = st.columns([1.2, 1])
    with left, st.container(border=True):
        st.subheader(text["trend"])
        if snapshot["history"]:
            rows = [
                {
                    text["chart_time"]: datetime.fromisoformat(item["timestamp_utc"]),
                    text["power"]: item["power_kw"],
                }
                for item in snapshot["history"]
            ]
            st.line_chart(
                rows,
                x=text["chart_time"],
                y=text["power"],
                y_label=text["power"] + " (kW)",
                height=230,
                alt=text["chart_alt"],
            )
        st.caption(text["history"])
    with right, st.container(border=True):
        st.subheader(text["evidence"])
        if state == "INVALID_MEASUREMENT":
            st.text(text["invalid_evidence"])
        elif state == "CONNECTION_LOST":
            st.text(text["lost_evidence"])
        elif age is not None:
            evidence = text["age_evidence"].format(age=age, threshold=demo.engine.stale_after)
            st.text(evidence.replace(".", ",") if language == "de" else evidence)
        st.markdown(f"**{text['next_check']}**")
        st.text(text[f"check_{state}"])
    st.subheader(text["events"])
    rows = [
        {
            "UTC": utc_label(event["timestamp_utc"]),
            text["event"]: event["kind"],
            text["severity"]: event["severity"],
            text["description"]: text[event["kind"]],
        }
        for event in reversed(snapshot["events"])
    ]
    st.dataframe(rows, hide_index=True, height=220, alt=text["events"])
    st.caption(text["event_limit"])
    with st.expander(text["architecture"]):
        st.write(text["architecture_text"])
        st.download_button(
            text["export"],
            json.dumps(snapshot, ensure_ascii=False, indent=2),
            file_name="windconnect_session.json",
            mime="application/json",
        )


monitor()
