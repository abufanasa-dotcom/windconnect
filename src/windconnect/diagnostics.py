"""Fault priority and monotonic freshness, independent of transport and UI."""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from windconnect.models import TurbineSample


class Health(StrEnum):
    HEALTHY = "HEALTHY"
    CONNECTION_LOST = "CONNECTION_LOST"
    INVALID_MEASUREMENT = "INVALID_MEASUREMENT"
    STALE_DATA = "STALE_DATA"


GUIDANCE = {
    Health.HEALTHY: (
        "INFO",
        "Verbindung und Messwerte sind aktuell.",
        ["Zeitstempel und Sequenz im Blick behalten."],
    ),
    Health.CONNECTION_LOST: (
        "ERROR",
        "Keine gültige Modbus-Antwort erhalten.",
        ["Läuft das lokale Backend?", "Loopback-Port und Fehlerkontext prüfen."],
    ),
    Health.INVALID_MEASUREMENT: (
        "ERROR",
        "Die empfangenen Messwerte sind ungültig.",
        ["Registermap, Skalierung und Wertebereiche prüfen."],
    ),
    Health.STALE_DATA: (
        "WARNING",
        "Modbus antwortet, aber Messwerte sind veraltet.",
        [
            "Sequenz und Messzeitstempel vergleichen.",
            "Aktualisierung des simulierten Datenlieferanten prüfen.",
        ],
    ),
}


class DiagnosticsEngine:
    def __init__(self, stale_after: float = 5):
        if stale_after <= 0:
            raise ValueError("Aktualitätsschwelle muss positiv sein")
        self.stale_after = stale_after
        self.state: Health | None = None
        self.last_seen: TurbineSample | None = None
        self.last_good: TurbineSample | None = None
        self.last_contact: datetime | None = None
        self._sequence_at: float | None = None
        self._timestamp_at: float | None = None
        self._recovery_pending = False

    def observe(
        self,
        *,
        monotonic_now: float,
        utc_now: datetime,
        sample: TurbineSample | None = None,
        error: str | None = None,
        invalid: str | None = None,
    ) -> tuple[dict, list[dict]]:
        events = []
        if error is not None:
            state, evidence = Health.CONNECTION_LOST, error
        else:
            self.last_contact = utc_now
            if sample is not None and invalid is None:
                try:
                    sample.validate()
                except ValueError as exc:
                    invalid = str(exc)
            if invalid is not None or sample is None:
                state, evidence = Health.INVALID_MEASUREMENT, invalid or "Messwert fehlt"
            elif (sample.timestamp_utc - utc_now).total_seconds() > 2:
                state, evidence = (
                    Health.INVALID_MEASUREMENT,
                    "Messzeitstempel liegt in der Zukunft",
                )
            else:
                previous = self.last_seen
                sequence_advanced = previous is None or (
                    0 < (sample.sequence_number - previous.sequence_number) % 2**32 < 2**31
                )
                timestamp_advanced = (
                    previous is None or sample.timestamp_utc > previous.timestamp_utc
                )
                if sequence_advanced:
                    self._sequence_at = monotonic_now
                if timestamp_advanced:
                    self._timestamp_at = monotonic_now
                age = max(
                    monotonic_now - self._sequence_at,
                    monotonic_now - self._timestamp_at,
                    (utc_now - sample.timestamp_utc).total_seconds(),
                )
                self.last_seen = sample
                if age >= self.stale_after:
                    state, evidence = (
                        Health.STALE_DATA,
                        f"Keine vollständige Aktualisierung: {age:.1f} s",
                    )
                elif self._recovery_pending and not (sequence_advanced and timestamp_advanced):
                    state, evidence = (
                        Health.STALE_DATA,
                        "Warte auf eine frische Probe zur Wiederherstellung",
                    )
                else:
                    state, evidence = (
                        Health.HEALTHY,
                        "Modbus-Lesen erfolgreich; Sequenz und Zeit aktuell",
                    )
                    self.last_good = sample
        severity, explanation, checks = GUIDANCE[state]
        if state != self.state:
            if state == Health.HEALTHY and self._recovery_pending:
                events.append(
                    self._event(
                        "RECOVERED",
                        "INFO",
                        utc_now,
                        "Frische, gültige Messwerte wieder verfügbar.",
                        evidence,
                        checks,
                    )
                )
            events.append(
                self._event(state.value, severity, utc_now, explanation, evidence, checks)
            )
        self.state = state
        self._recovery_pending = state != Health.HEALTHY
        return {
            "state": state.value,
            "severity": severity,
            "explanation": explanation,
            "evidence": evidence,
            "checks": checks,
            "last_contact_utc": self.last_contact.isoformat() if self.last_contact else None,
            "last_good": self.last_good.to_dict() if self.last_good else None,
        }, events

    @staticmethod
    def _event(kind, severity, stamp, explanation, evidence, checks):
        return {
            "id": str(uuid4()),
            "timestamp_utc": stamp.astimezone(UTC).isoformat(),
            "kind": kind,
            "severity": severity,
            "explanation": explanation,
            "evidence": evidence,
            "checks": checks,
        }
