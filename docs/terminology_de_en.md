# Terminologie: Deutsch ↔ English

Beide Sprachfassungen beschreiben denselben Funktionsumfang. Die öffentliche
Oberfläche verwendet die folgenden Begriffe; Protokoll-/Diagnosecodes bleiben unverändert.

| Deutsch | English | Bedeutung in WindConnect |
|---|---|---|
| Modbus-TCP-Monitoring | Modbus TCP monitoring | Wiederholte Leseanfragen über tatsächliche TCP-Sockets auf Loopback |
| Fehlerdiagnose | Fault diagnostics | Regelbasierte Einordnung beobachteter Kommunikations- und Messdatenfehler |
| Kommunikationsstatus | Communication status | Erfolg oder Fehlschlag der TCP-/Modbus-Leseanfrage |
| Messwertgültigkeit | Measurement validity | Prüfung von Registerformat, Betriebszustand und zulässigen Wertebereichen |
| Datenaktualität | Data freshness | Prüfung von Sequenzfortschritt, Messzeitfortschritt und Probenalter |
| Veraltete Messdaten | Stale measurement data | Erfolgreiche Antwort mit nicht mehr aktuellen Messdaten |
| Wirkleistung | Active power | Synthetische elektrische Wirkleistung in kW, 0–3000 kW |
| Windgeschwindigkeit | Wind speed | Synthetische Geschwindigkeit in m/s, 0–60 m/s |
| Betriebszustand | Operating state | RUNNING, STOPPED oder FAULT; getrennt vom Kommunikationsstatus |
| UTC-Messzeitstempel | UTC measurement timestamp | Explizites Registerfeld, Unix-Epoche in Millisekunden |
| Sequenznummer | Sequence number | uint32-Zähler einer Probe, mit definiertem Überlauf |
| Holding-Register | Holding register | 16-Bit-Wort des Modbus-Datenmodells, hier über FC03 gelesen |
| Registerbelegung | Register map | Projektspezifische Zuordnung der zwölf Register |
| Skalierte Ganzzahl | Scaled integer | Ganzzahliger Rohwert mit explizitem Faktor für kW bzw. m/s |
| Höchstwertiges Wort zuerst | Most significant word first | Projektspezifische Reihenfolge bei Feldern über mehrere Register |
| Wiederherstellung | Recovery | Neue gültige und aktuelle Probe nach einer Störung; Ereignis RECOVERED |
| Virtuelles Kraftwerk | Virtual power plant (VPP) | Anwendungskontext; keine tatsächlich implementierte VPP-Anbindung |

## Präzise Abgrenzung

- Ein erfolgreicher Modbus-Read belegt Erreichbarkeit auf Anwendungsebene, aber nicht
  automatisch Messwertgültigkeit oder Datenaktualität.
- Eine ungültige Probe kann in einer erfolgreichen Modbus-Antwort enthalten sein.
- 0 kW oder STOPPED sind für sich genommen kein Kommunikationsfehler.
- Die Standard-Aktualitätsschwelle beträgt 5 s. Für HEALTHY müssen Kommunikation,
  Gültigkeit und Aktualität die implementierten Prüfungen bestehen.
- HEALTHY bedeutet keine zertifizierte oder umfassende Zustandsbewertung einer echten Anlage.
- Die Leistungskennlinie ist ein vereinfachtes synthetisches Modell, kein validierter
  digitaler Zwilling und keine physikalische Ertragsprognose.
- Der öffentliche Browser kommuniziert per HTTP/WebSocket mit Streamlit. Der tatsächliche
  Modbus-TCP-Austausch erfolgt ausschließlich serverseitig auf 127.0.0.1.

## Zwei Ausführungsarten

Die lokale Variante nutzt einen fortlaufenden Backend-Prozess und atomare Dateien.
Die öffentliche Variante bewahrt Simulator und Diagnose pro Streamlit-Sitzung im Speicher
und erzeugt pro Abfrage einen kurzlebigen Server/Client-Austausch. Fehlerfälle sind in beiden
Varianten synthetisch; es gibt keine Verbindung zu realen Anlagen oder emsys-Systemen.

## Primärquellen

- [Modbus Application Protocol Specification V1.1b3](https://www.modbus.org/file/secure/modbusprotocolspecification.pdf):
  Datenmodell, 16-Bit-Holding-Register, FC03 und Big-Endian-Darstellung.
- [PyModbus 3.11 Server API](https://pymodbus.readthedocs.io/en/v3.11.0/source/server.html):
  verwendete Serverarchitektur; der konkrete installierte Stand ist 3.11.4.
- [Streamlit Session State](https://docs.streamlit.io/develop/concepts/architecture/session-state):
  sitzungsbezogener Speicher der öffentlichen Demo.

Die Wortreihenfolge über mehrere Modbus-Register ist in diesem Projekt ausdrücklich
festgelegt und wird nicht als universelle Eigenschaft jeder Modbus-Anlage dargestellt.
