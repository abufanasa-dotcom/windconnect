# Modbus-TCP-Registermap, Version 1

Endpoint `127.0.0.1:15020`, Device/Unit-ID **1**, Holding-Register lesen mit **FC03**.
Zwölf Register in **einer** Anfrage lesen. Keine Schreibfunktionen vorgesehen;
Remote-Schreibversuche werden mit ILLEGAL_FUNCTION abgewiesen.

**Protokolladressen sind nullbasiert.** Die Referenz 40001 bezeichnet Adresse 0;
40001 wird niemals als Drahtadresse gesendet. PyModbus-Client:
`read_holding_registers(0, count=12, device_id=1)`.

| Adresse | Referenz | Inhalt | Encoding |
|---|---|---|---|
| 0 | 40001 | Magic | uint16, 0x5743 (WC) |
| 1 | 40002 | Formatversion | uint16, 1 |
| 2–5 | 40003–40006 | Messzeit | uint64, Unix-Epoche in UTC-Millisekunden |
| 6–7 | 40007–40008 | Sequenz | uint32, Überlauf modulo 2^32 |
| 8–9 | 40009–40010 | Leistung | uint32, Rohwert / 10 = kW |
| 10 | 40011 | Wind | uint16, Rohwert / 100 = m/s |
| 11 | 40012 | Betriebszustand | uint16: RUNNING=1, STOPPED=2, FAULT=3 |

Big-endian pro Register und **höchstwertiges Wort zuerst** bei mehrteiligen Feldern.
Python-Structformat: `>HHQIIHH` = 24 Bytes = 12 Register.
Skalierung wird beim Senden auf den nächsten ganzzahligen Rohwert gerundet.
Maximaler Rundungsfehler: 0,05 kW, 0,005 m/s und 0,5 ms.

Beispiel: Sequenz 0x12345678 → Register `[0x1234, 0x5678]`;
1234,5 kW → `[0, 12345]`; 10,25 m/s → `[1025]`.

Validierung: 0–3000 kW, 0–60 m/s, bekannte Version/Magic, exakte Registeranzahl,
gültige UTC-konvertierbare Epoche und bekannter Betriebszustand. Die Kennlinie erzeugt
bei Wind <3 oder >=25 m/s STOPPED mit 0 kW. RUNNING bei Einschaltwind 3 m/s darf
ebenfalls 0 kW haben. FAULT ist definiert und dekodierbar; der MVP erzeugt diesen
Anlagenzustand nicht automatisch und trennt ihn von der Kommunikationsdiagnose.

Alle Register werden synchron ohne await im selben Event-Loop ersetzt; die
FC03-Leseoperation sieht eine vollständige Probe. Keine Timestamp-Funktion von Modbus
wird vorausgesetzt: die Zeit wird explizit als eigenes Feld übertragen.

Fehlermodus `invalid` umgeht absichtlich die normale Sender-Validierung und setzt
Register 10 auf 65535. Die Clientdekodierung muss diesen Wert ablehnen.
