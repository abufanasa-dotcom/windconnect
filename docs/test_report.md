# Testbericht – WindConnect 1.0.0

**Ausgeführt am 05.11.2026, Europe/Berlin.** Dies ist ein Bericht über ausgeführte
Prüfungen, keine industrielle Freigabe. Keine echten emsys-Systeme wurden verwendet.

## Umgebung

- Windows NT 10.0.26300.0 (Windows 11), x86_64.
- Python 3.13.15, MSC v.1944, 64 Bit.
- Python 3.14.7 und 3.11.16 waren zusätzlich auffindbar; nicht als Projektlaufzeit genutzt.
- Defekte WindowsApps-Aliase für `python` und `py`; lokale Python-3.13-Laufzeit per uv
  heruntergeladen, venv explizit erzeugt. Keine globale Python-Installation geändert.
- Direkte Abhängigkeiten: PyModbus 3.11.4, Streamlit 1.66.1, NumPy 2.2.6,
  pandas 2.2.3, PyArrow 20.0.0; Tests Pytest 9.0.2, Ruff 0.14.4.
- Build: Hatchling 1.27.0. Vollständige Constraints in `requirements-lock.txt`.
- Im eingeschränkten Ausführungskontext wurden TEMP/TMP auf einen lokalen
  beschreibbaren `data/tmp`-Ordner gesetzt. Neuinstallation in separater `.venv-clean`.
- Desktop-Projektordner enthielt nur den Plan. Keine Kelmarsh-benannten Dateien in
  den inspizierten Desktop-/Workspace-Pfaden gefunden; keine fremden Projekte geändert.

## Phasengates

| Gate | Tatsächlich ausgeführte Prüfung | Ergebnis |
|---|---|---|
| A | Editable-Installation, `python -m pytest -q`, `ruff check .` | 1 passed in 0.04s; All checks passed |
| B | Simulator, Grenzen, Seed, uint32-Überlauf, Register-Roundtrip | 33 passed in 0.12s |
| C | Echte TCP-Reads, Schreibschutz, Serverstopp, Restart, Portkollision, Timeout | 36 passed in 1.42s; Ruff sauber |
| D | Alle Diagnosen, Recovery, Deduplizierung, Storage-/IPC-/Backend-Integration | 53 passed in 4.76s; Ruff sauber |
| E | Streamlit-AppTests + echte Brave-Browser-Demo aller Szenarien | 60 passed; Browser zeigt alle Fehler und RECOVERED |
| F | Frische pip-Installation, komplette Suite, Lint/Format, Prozess-Smokes | Bestanden; Details unten |

## Endgültige Befehle und Originalausgaben

Aus dem Projektverzeichnis, jeweils mit explizitem Interpreter:

```powershell
# Erzeugung mit explizitem lokalen Python-3.13-Interpreter:
& '<Python-3.13-Pfad>\python.exe' -m venv .venv-clean
.\.venv-clean\Scripts\python.exe -m pip install --cache-dir data/pip-cache -c requirements-lock.txt -e ".[dev]"
```

Ausgabe: `Successfully built windconnect`, anschließend `Successfully installed ... windconnect-1.0.0`.
Exit-Code **0**. Es wurde eine neue venv benutzt, nicht die Entwicklungs-venv kopiert.

```powershell
.\.venv-clean\Scripts\python.exe -m pytest -q
```

```text
............................................................             [100%]
60 passed in 17.16s
```

**Keine Warnungen** im abschließenden Lauf in der frischen Umgebung.

```powershell
.\.venv-clean\Scripts\python.exe -m pip check
.\.venv-clean\Scripts\ruff.exe check .
.\.venv-clean\Scripts\ruff.exe format --check .
```

```text
No broken requirements found.
All checks passed!
24 files already formatted
```

Der Formatcheck umfasst auch die beiden abschließend hinzugefügten Smoke-Skripte.
Der vollständige 60-Test-Lauf erfolgte nach der letzten Änderung am Anwendungscode;
danach wurden nur Smoke-Hilfsskripte/Dokumentation ergänzt und separat ausgeführt.

```powershell
.\.venv-clean\Scripts\python.exe scripts/verify_demo.py
```

Ergebnis mit Exit-Code **0**:

```text
observed_states: HEALTHY → STALE_DATA → HEALTHY → CONNECTION_LOST → HEALTHY
                 → INVALID_MEASUREMENT → HEALTHY
recoveries: 3
process_exit: 0
port_released: true
```

Dieses Skript startet einen neuen Backend-Prozess, sendet Befehle über die echte CLI,
prüft Diagnose und Befehlsbestätigung, wartet auf reguläres Ende und bindet den
gleichen Modbus-Port unmittelbar erneut. Es verwendet einen eigenen temporären
Datenordner und einen dynamischen Loopback-Port. Reportzeit: `2026-11-05T13:35:02.863542+00:00`.

```powershell
.\.venv-clean\Scripts\python.exe scripts/verify_dashboard_start.py
```

```text
Clean Streamlit HTTP startup: ok
Streamlit smoke process stopped; listener unreachable
```

Exit-Code **0**. Eigener UI-Prozess, dynamischer Loopback-Port, HTTP-Health geprüft.
Ein interner 10-s-Watchdog beendet ausschließlich diesen Wegwerfprozess.
Das ist ein Start-/Cleanup-Test, kein Browser-Rendering-Test und kein Test eines
graceful Streamlit-Shutdowns. Die AppTests und Browserprüfung decken das Rendering ab.

Zusätzlich: `runner --help`, `cli --help` ausgeführt; die dokumentierten Optionen
existieren. Der laufende Demo-UI-Endpunkt `/_stcore/health` antwortete `ok`.

## Testmatrix

| Anforderung | Nachweis |
|---|---|
| Gesund, aktuelle Messungen | Unit-, TCP-, Backend-, AppTest und Browser |
| Verbindungsverlust | Echter Listener-Stopp, begrenzte Reads, Last-good beibehalten |
| Veraltete Daten trotz erfolgreichem Read | Sequenz/Zeit einzeln und gemeinsam eingefroren; Browser |
| Ungültige Daten | Wertebereich, Magic/Version, Payloadlänge, Zustand, zukünftige Zeit |
| Recovery nur mit frischer Probe | Unit-Test mit gecachter Probe; 3 recoveries im Prozess-Smoke |
| 0 kW/STOPPED gültig | Simulator- und Diagnose-Unit-Tests |
| Ereignisse dedupliziert | 10 gleiche Fehlerpolls erzeugen genau ein Übergangsereignis |
| Endianness und Präzision | Bekannte Wörter und Roundtrip aller Felder |
| Neustart und Cleanup | Same-Port-Restart, finally-Cleanup, reguläres Prozessende |
| Konkurrierende Backends | OS-Dateisperre und Portkollision |
| Dateien | Atomarer Austausch mit parallelem Leser, defekte Daten, Logrotation |
| Dashboard-Steuerung | AppTest klickt alle Szenarien und Reset; Diagnose wird nicht erfunden |
| Backend beendet | AppTest verhindert grünes Online-Signal bei historischem HEALTHY |
| Windows-Neuinstallation | Eigene frische venv, pip-Constraints-Installation, gesamte Suite |

## Manuelle Browserprüfung

Brave, lokaler Endpunkt `http://127.0.0.1:8501`, zwei getrennte Prozesse:
`python -m windconnect.runner` und `python -m streamlit run dashboard/app.py`.

Beobachtet: HEALTHY mit fortlaufender Sequenz; danach STALE_DATA nach Einfrieren
bei weiter aktualisiertem Kontakt; CONNECTION_LOST nach Unterbrechung; INVALID_MEASUREMENT
mit „Windgeschwindigkeit außerhalb 0–60 m/s“. Nach jedem Reset wurden HEALTHY und
RECOVERED im sichtbaren Ereignisprotokoll beobachtet. Die UI blieb bedienbar.
Die Aufnahme `screenshots/stale-data.png` belegt den Stale-Fall, `healthy.png` den Normalbetrieb.

## Während der Umsetzung gefundene und behobene Fehler

1. Sandbox-Tempordner nicht beschreibbar: projektlokale TEMP/TMP-/uv-Cache-Pfade.
2. Falscher PyModbus-Import für ExcCodes: korrekter Import aus `pymodbus.constants`.
3. Windows-Port-Doppelbelegung mit PyModbus-SO_REUSEADDR: deaktiviert und getestet.
4. Timeout von 100 ms war kürzer als der PyModbus-Connect-Overhead: Testparameter korrigiert.
5. Kurzzeitige Windows-Dateifreigabekonflikte: begrenzte Retries auch beim Snapshot-Lesen.
6. Application Control blockierte eine DLL der zunächst aufgelösten neuen pandas-Version:
   getestete ältere Datenpakete fixiert. Keine Sicherheitsrichtlinie verändert.
7. Metadatenrest nach abgebrochenem NumPy-Austausch erzeugte 7 Warnungen im ersten
   60-Test-Lauf: isolierter Rest entfernt; endgültiger Clean-Install-Lauf ohne Warnungen.
8. Setuptools-Build scheiterte bei tiefem Pfad mit WinError 206: Hatchling eingesetzt,
   frische pip-Installation danach erfolgreich.
9. Venv-Launcher-Cleanup des Wegwerf-UI-Smokes: Selbstbeendigung im Interpreter,
   danach keine Verbindung zum Testlistener mehr möglich.

## Grenzen und nicht geprüfte Punkte

- Keine echten Anlagen, emsys-Produkte, VPNs oder industrielle Netze; keinerlei
  Behauptung über Produktionskompatibilität oder Zertifizierung.
- Kein vollständiger physikalischer Wind-/Turbinenzwilling und keine Anlagensteuerung.
- Nur Windows/Python 3.13 tatsächlich getestet; kein Linux/macOS- oder 3.14-Testlauf.
- Kein mehrtägiger Last-/Dauertest, kein Netzkarten-Offlinetest, kein WCAG-Audit und
  keine manuellen mobilen Breakpointtests. Status wird zusätzlich als Text angezeigt.
- Beim Phasenabschluss noch keine Git-Remote-Veröffentlichung; kein externer Anlagendienst und kein automatisches CV-Update.
- Logs und Verlauf sind absichtlich begrenzt; JSON-Dateien sind kein transaktionales
  Langzeitarchiv. Ein einzelner vertrauenswürdiger lokaler Nutzer wird vorausgesetzt.

Alle zehn MVP-Akzeptanzkriterien wurden durch die oben genannten Tests, die
Windows-Neuinstallation, die Dokumentation und die Browser-Demo geprüft. Diese Aussage
bezieht sich auf den lokalen Demonstrationsumfang und die explizit genannten Testgrenzen.


## Prüfung nach Kopie auf den Desktop

Am 05.11.2026 wurde das Projekt nach Desktop/WindConnect kopiert.
Der vorhandene Implementierungsplan blieb erhalten. Ein eigener Python-3.13.15-Interpreter
liegt unter .python/cpython-3.13.15; die venv wurde am neuen Ort neu erstellt.
Die Importe und der Basisinterpreter wurden auf Pfade innerhalb dieses Ordners geprüft.

Ergebnisse im neuen Verzeichnis: **60 passed in 22.86s**, Ruff: All checks passed,
Format: 24 files already formatted, pip check: No broken requirements found.
Der Prozess-Smoke-Test beobachtete alle vier Zustände, drei Recoveries, Exit-Code 0
und einen freigegebenen Modbus-Port. Der alte Projektordner wurde als Sicherung behalten.


## Öffentliche Demo und Terminologieprüfung (05.11.2026)

Die erweiterte Suite wurde nach der Implementierung vollständig ausgeführt: **66 passed in 13.51s**. Zusätzlich wurde der gleichzeitige Betrieb zweier Besuchersitzungen mit echten parallelen Modbus-Abfragen geprüft: **1 passed in 0.24s**. Ruff: All checks passed; Format: 29 files already formatted.

Die öffentliche Demo nutzt je Sitzung getrennte Simulator-/Diagnoseobjekte. Pro Abfrage entsteht ein echter Loopback-TCP-Austausch; der Listener wird anschließend geschlossen. Die Tests prüfen alle Diagnosezustände, dreifache Wiederherstellung, Portfreigabe, Sitzungsisolation, DE/EN-Oberfläche und Steuerung. Im lokalen Browser wurden STALE_DATA bei erfolgreichen Reads und die Sprachumschaltung beobachtet. Die Hosting-Prüfung ist im folgenden Abschnitt dokumentiert.


## Öffentliche Bereitstellung verifiziert (05.11.2026)

URL: https://windconnect-monitoring.streamlit.app/ (Englisch: ?lang=English). Streamlit Community Cloud installierte das Projekt unter Linux mit Python 3.13.18. Die anonyme Browserprüfung bestätigte HEALTHY, STALE_DATA bei erfolgreicher Modbus-Leseantwort, CONNECTION_LOST, INVALID_MEASUREMENT und anschließend RECOVERED/HEALTHY. Der englische Direktlink öffnete die englische Oberfläche. Die zwei unabhängigen Browsersitzungen waren getrennt. Kein Linux-Dauertest und kein Lasttest wurden durchgeführt.

Abschlussprüfung nach Ergänzung des englischen Direktlink-Tests: **66 passed in 14.26s**; Ruff: All checks passed; Format: 29 files already formatted.
