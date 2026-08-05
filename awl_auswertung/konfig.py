"""Konfiguration der Auswertung (Kategorien, Sollstunden)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

# Anwesenheitscodes laut Auswahlliste im Tabellenblatt AWL (Spalte DD/DE).
# Dient als Beschriftung im Bericht und als Vollstaendigkeitspruefung.
CODE_BESCHREIBUNG: dict[str, str] = {
    "A": "Anwesend",
    "AK": "Arbeit, und Krank",
    "AKAS": "Arbeit, und Krank AS",
    "AP": "anderes Projekt",
    "AS": "Ausbildung",
    "BG": "Beschäftigungsverbot durch HLG",
    "BI": "Beschäftigungsverbot durch Arzt",
    "EX": "Kündigung",
    "EZ": "Elternzeit",
    "FA": "Freizeitausgleich",
    "FAK": "Freizeitausgleich Kunde",
    "FE": "fehlt entschuldigt",
    "FU": "fehlt unentschuldigt",
    "KZA": "Kurzarbeit",
    "K2": "Krank",
    "KA": "Arbeitsunfall",
    "MS": "Mutterschutz",
    "R": "Ruhe",
    "U2": "bezahlter Urlaub",
    "UU": "unbezahlter Urlaub",
    "Q": "Quarantäne",
    "Ft": "Feiertag",
}

# Zuordnung Anwesenheitscode -> Auswertungskategorie.
# Codes, die hier nicht auftauchen, werden nicht als Abwesenheit gewertet
# (sie erscheinen aber im Tabellenblatt "Alle Codes" des Berichts).
STANDARD_KATEGORIEN: dict[str, str] = {
    "K2": "Krank",
    "AK": "Krank",
    "AKAS": "Krank",
    "KA": "Arbeitsunfall",
    "U2": "Urlaub",
    "UU": "Urlaub unbezahlt",
    "Ft": "Feiertag",
}

# Reihenfolge und Auswahl der Kategorien in den Uebersichten.
STANDARD_KATEGORIE_REIHENFOLGE: list[str] = [
    "Krank",
    "Urlaub",
    "Feiertag",
    "Arbeitsunfall",
    "Urlaub unbezahlt",
]

# Codes, bei denen der Mitarbeiter einen Teil des Tages gearbeitet hat.
# Abwesenheitsstunden = Sollstunden - bereits erfasste Iststunden.
STANDARD_TEILTAG_CODES: list[str] = ["AK", "AKAS"]


@dataclass
class Konfiguration:
    """Alle Stellschrauben der Auswertung an einem Ort."""

    # Sollstunden je Abwesenheitstag, wenn kein anderer Wert ermittelbar ist.
    standard_sollstunden: float = 8.0

    # Sollstunden je Mitarbeiter, Schluessel ist die P-Id (Spalte C der AWL)
    # als Text, z. B. {"29910": 7.5}. Hat Vorrang vor allem anderen.
    sollstunden_je_mitarbeiter: dict[str, float] = field(default_factory=dict)

    # Wenn True: fehlt ein Eintrag oben, wird der Durchschnitt der tatsaechlich
    # gearbeiteten Stunden desselben Mitarbeiters in derselben KW verwendet.
    durchschnitt_als_fallback: bool = True

    kategorien: dict[str, str] = field(
        default_factory=lambda: dict(STANDARD_KATEGORIEN)
    )
    kategorie_reihenfolge: list[str] = field(
        default_factory=lambda: list(STANDARD_KATEGORIE_REIHENFOLGE)
    )
    teiltag_codes: list[str] = field(
        default_factory=lambda: list(STANDARD_TEILTAG_CODES)
    )

    def kategorie(self, code: str | None) -> str | None:
        """Auswertungskategorie zu einem Anwesenheitscode, sonst None."""
        if not code:
            return None
        return self.kategorien.get(code.strip())

    def ist_teiltag(self, code: str | None) -> bool:
        if not code:
            return False
        return code.strip() in self.teiltag_codes

    def sollstunden_override(self, p_id: str) -> float | None:
        if str(p_id).startswith("_"):
            return None  # Kommentarschlüssel, kein Mitarbeiter
        wert = self.sollstunden_je_mitarbeiter.get(str(p_id))
        return float(wert) if wert is not None else None

    @classmethod
    def laden(cls, pfad: Path | str | None) -> "Konfiguration":
        """Konfiguration aus einer JSON-Datei lesen; None -> Standardwerte."""
        if pfad is None:
            return cls()
        roh: dict[str, Any] = json.loads(Path(pfad).read_text(encoding="utf-8"))
        # Schlüssel mit führendem "_" dienen als Kommentar, da JSON keine kennt.
        daten = {k: v for k, v in roh.items() if not k.startswith("_")}
        unbekannt = set(daten) - {f.name for f in fields(cls)}
        if unbekannt:
            raise ValueError(
                f"Unbekannte Schlüssel in der Konfiguration: {sorted(unbekannt)}"
            )
        konfig = cls(**daten)
        konfig.pruefen()
        return konfig

    def pruefen(self) -> None:
        if self.standard_sollstunden <= 0:
            raise ValueError("standard_sollstunden muss größer als 0 sein.")
        for p_id, stunden in self.sollstunden_je_mitarbeiter.items():
            if float(stunden) < 0:
                raise ValueError(
                    f"Negative Sollstunden für P-Id {p_id}: {stunden}"
                )
        fehlende = [k for k in self.kategorien.values()
                    if k not in self.kategorie_reihenfolge]
        for kategorie in fehlende:
            self.kategorie_reihenfolge.append(kategorie)
