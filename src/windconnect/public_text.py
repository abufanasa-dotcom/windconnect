"""Matched German/English terminology for the public demonstration."""

TEXT = {
    "title": (
        "WindConnect – Modbus-TCP-Monitoring und Fehlerdiagnose",
        "WindConnect – Modbus TCP Monitoring and Fault Diagnostics",
    ),
    "subtitle": (
        "Öffentliche Demonstration mit synthetischen Messdaten · keine reale Anlage, "
        "keine emsys-Anbindung",
        "Public demonstration with synthetic measurements · "
        "no real turbine, no emsys integration",
    ),
    "controls": ("Demo-Szenarien", "Demo scenarios"),
    "normal": ("Normalbetrieb", "Normal operation"),
    "freeze": ("Messdaten einfrieren", "Freeze measurement data"),
    "disconnect": ("Verbindung unterbrechen", "Interrupt connection"),
    "invalid": ("Ungültigen Messwert senden", "Send invalid measurement"),
    "reset": ("Fehler zurücksetzen", "Reset fault"),
    "refresh": ("Jetzt abfragen", "Poll now"),
    "automatic": ("Automatisch abfragen (1 s)", "Automatic polling (1 s)"),
    "isolated": (
        "Ihre Sitzung ist unabhängig von anderen Besuchern. Ein Neuladen startet "
        "eine neue Simulation.",
        "Your session is independent of other visitors. Reloading starts a new simulation.",
    ),
    "status": ("Kommunikations- und Messdatenstatus", "Communication and measurement status"),
    "scenario": ("Gewähltes Szenario", "Selected scenario"),
    "observed": ("Beobachtete Diagnose", "Observed diagnosis"),
    "read": ("Modbus-Leseanfrage", "Modbus read request"),
    "success": ("erfolgreich", "successful"),
    "failed": ("fehlgeschlagen", "failed"),
    "contact": ("Letzte erfolgreiche Modbus-Antwort", "Last successful Modbus response"),
    "none": ("Noch nicht verfügbar", "Not available yet"),
    "measurements": ("Synthetische Messwerte", "Synthetic measurements"),
    "power": ("Wirkleistung", "Active power"),
    "wind": ("Windgeschwindigkeit", "Wind speed"),
    "operating": ("Betriebszustand", "Operating state"),
    "age": ("Alter der Messdaten", "Measurement data age"),
    "timestamp": ("UTC-Messzeitstempel", "UTC measurement timestamp"),
    "sequence": ("Sequenznummer", "Sequence number"),
    "RUNNING": ("In Betrieb", "Running"),
    "STOPPED": ("Gestoppt", "Stopped"),
    "FAULT": ("Anlagenfehler", "Turbine fault"),
    "historical": (
        "Zuletzt lesbare bzw. gültige Werte; kein Nachweis aktueller Messdaten.",
        "Last readable or valid values; not evidence of current measurements.",
    ),
    "missing": (
        "Noch keine gültigen Messwerte verfügbar.",
        "No valid measurements available yet.",
    ),
    "trend": ("Wirkleistungsverlauf", "Active power trend"),
    "chart_time": ("Messzeit (Browser-Zeit)", "Measurement time (browser time)"),
    "chart_alt": (
        "Verlauf der gültigen synthetischen Wirkleistung",
        "Valid synthetic active power over time",
    ),
    "history": (
        "Maximal 120 unterschiedliche gültige Proben dieser Sitzung.",
        "Up to 120 distinct valid samples from this session.",
    ),
    "evidence": ("Diagnostischer Befund", "Diagnostic evidence"),
    "next_check": ("Empfohlene Prüfung", "Recommended check"),
    "HEALTHY": (
        "Kommunikation erfolgreich; Messwerte gültig und aktuell.",
        "Communication successful; measurements are valid and fresh.",
    ),
    "STALE_DATA": (
        "Modbus antwortet, aber die Messdaten sind veraltet.",
        "Modbus responds, but measurement data are stale.",
    ),
    "CONNECTION_LOST": (
        "Keine erfolgreiche Modbus-Antwort erhalten.",
        "No successful Modbus response received.",
    ),
    "INVALID_MEASUREMENT": (
        "Eine erfolgreiche Leseantwort enthält einen ungültigen Messwert.",
        "A successful read response contains an invalid measurement.",
    ),
    "RECOVERED": (
        "Wiederherstellung durch eine neue, gültige Probe bestätigt.",
        "Recovery confirmed by a new, valid sample.",
    ),
    "check_HEALTHY": (
        "Messzeitstempel und Sequenznummer weiter beobachten.",
        "Continue observing the measurement timestamp and sequence number.",
    ),
    "check_STALE_DATA": (
        "Fortschritt von Sequenznummer und Messzeitstempel prüfen.",
        "Check that the sequence number and measurement timestamp advance.",
    ),
    "check_CONNECTION_LOST": (
        "Serverzustand, Loopback-Endpunkt und Anfrage-Timeout prüfen.",
        "Check server state, loopback endpoint, and request timeout.",
    ),
    "check_INVALID_MEASUREMENT": (
        "Registerbelegung, Skalierung und Wertebereich prüfen.",
        "Check the register map, scaling, and permitted range.",
    ),
    "invalid_evidence": (
        "Register 10: 65535 → 655,35 m/s; zulässig sind 0–60 m/s.",
        "Register 10: 65535 → 655.35 m/s; permitted range: 0–60 m/s.",
    ),
    "lost_evidence": (
        "Der lokale Testserver wurde vor der Client-Anfrage geschlossen.",
        "The local test server was closed before the client request.",
    ),
    "age_evidence": (
        "Datenalter: {age:.1f} s · Aktualitätsschwelle: {threshold:.1f} s",
        "Data age: {age:.1f} s · freshness threshold: {threshold:.1f} s",
    ),
    "events": ("Ereignisprotokoll", "Event log"),
    "event": ("Ereignis", "Event"),
    "description": ("Beschreibung", "Description"),
    "severity": ("Schweregrad", "Severity"),
    "event_limit": (
        "Maximal 100 Zustandswechsel dieser Sitzung; keine dauerhafte Speicherung.",
        "Up to 100 state transitions from this session; no permanent storage.",
    ),
    "architecture": ("Wie arbeitet diese öffentliche Demo?", "How does this public demo work?"),
    "architecture_text": (
        "Pro Abfrage werden ein Modbus-TCP-Server und ein separater Client auf dem App-Server "
        "gestartet. Der Datenaustausch erfolgt tatsächlich über TCP auf 127.0.0.1 mit einem "
        "kurzlebigen Port. Danach wird der Listener geschlossen. "
        "Der Browser zeigt die Ergebnisse; "
        "er baut selbst keine Modbus-Verbindung auf. Simulator, Diagnose und Verlauf sind je "
        "Sitzung getrennt. Die vollständige lokale Variante bietet ein fortlaufendes Backend "
        "und dateibasiertes Protokoll. Der VPP-Bezug ist ein Anwendungskontext, keine reale "
        "VPP-Anbindung oder Anlagensteuerung.",
        "Each poll starts a Modbus TCP server and a separate client on the app server. Data "
        "are actually exchanged over TCP at 127.0.0.1 on a short-lived port. The listener then "
        "closes. The browser displays the results; it does not establish a Modbus connection "
        "itself. Simulator, diagnostics, and history are isolated per session. The full local "
        "version provides a continuously running backend and file-based logging. VPP is an "
        "application context, not a real virtual power plant integration or turbine control.",
    ),
    "source": ("Quellcode und lokale Installation", "Source code and local installation"),
    "export": ("Sitzungsbericht herunterladen", "Download session report"),
    "error": (
        "Die Demo-Abfrage ist fehlgeschlagen. Bitte erneut abfragen.",
        "The demo poll failed. Please poll again.",
    ),
}


def messages(language: str) -> dict[str, str]:
    if language not in {"de", "en"}:
        raise ValueError("Supported languages: de, en")
    index = 0 if language == "de" else 1
    return {key: values[index] for key, values in TEXT.items()}
