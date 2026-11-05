# Portfolio und Interview

## Zwei-Minuten-Demo

| Zeit | Aktion und Erklärung |
|---|---|
| 0:00–0:25 | HEALTHY, synthetische Messwerte und Loopback-Endpunkt zeigen |
| 0:25–0:50 | Daten einfrieren, nach mindestens 5 s STALE_DATA zeigen |
| 0:50–1:20 | Letzter Modbus-Kontakt ist aktuell, die Probe nicht: Erreichbarkeit ≠ Aktualität |
| 1:20–1:45 | Zurücksetzen, neue Sequenz und RECOVERED im Protokoll zeigen |
| 1:45–2:00 | Tests, deutsche Prüfschritte und Grenzen der Simulation erklären |

## Pitch

„Ich habe ein lokales Demonstrationsprojekt entwickelt, um die technische Anbindung
einer Windenergieanlage an ein virtuelles Kraftwerk besser zu verstehen. Die Anlage
wird simuliert, Messwerte werden über Modbus TCP übertragen und typische
Kommunikationsprobleme werden gezielt getestet. Das Dashboard zeigt den
Verbindungsstatus, die Aktualität der Daten und dokumentierte Fehlerereignisse.
Besonders wichtig war mir, zwischen einem Verbindungsfehler und veralteten Messwerten
zu unterscheiden. Das Projekt nutzt keine echten emsys-Systeme.“

## Lebenslauf

**WindConnect – VPP Connection & Fault Diagnostics (Eigenständiges Simulationsprojekt)**

Python · Modbus TCP · Streamlit · Fehlerdiagnose

- Lokale Simulation einer Windenergieanlage mit Modbus-TCP-Datenübertragung und
  Monitoring-Dashboard entwickelt.
- Kommunikationsausfall, veraltete Messwerte und ungültige Daten reproduzierbar
  simuliert und diagnostiziert.
- Automatisierte Tests, Ereignisprotokoll und technische Dokumentation für
  nachvollziehbare Fehlersuche erstellt.

Als eigenes Portfolio-Projekt aufführen, nicht als Berufserfahrung, Kundenauftrag
oder emsys-Zusammenarbeit. Testnachweise und Limitierungen stehen im Testbericht.

## Technische Rückfragen

- Warum kein Netzwerk-Ping als Gesundheitsprüfung? Ein antwortender Dienst kann
  eingefrorene Daten liefern. Sequenz und Messzeit sind zusätzliche Belege.
- Warum getrennte UI? Streamlit führt das Skript erneut aus. Dienste gehören in einen
  Prozess mit eindeutigem Start/Stopp, nicht in den Renderpfad.
- Warum skalierte Ganzzahlen? Explizite Einheiten und Wortreihenfolge vermeiden
  stillschweigende Annahmen über Float-/Byte-Layouts.
- Warum JSON statt Datenbank? Wenige lokale Daten, kurzer Demoablauf, übersichtlicher
  Betrieb. Für Langzeitbetrieb wären Persistenz und Betriebsanforderungen neu zu bewerten.
- Was wäre bei realen Anlagen nötig? Anlagen-/Herstellerspezifikation, sichere Netze,
  abgestimmte Betriebsprozesse und deutlich breitere Validierung. Der MVP behauptet
  keine Produktionsreife.
