"""Aggregation der Tageseinträge zu einer Kalenderwochen-Auswertung."""

from __future__ import annotations

import datetime as dt
from collections import defaultdict
from dataclasses import dataclass, field

from .einlesen import Tagesdatei, Tageseintrag
from .konfig import CODE_BESCHREIBUNG, Konfiguration

# Codes, die als "hat gearbeitet" gelten und deshalb in den Durchschnitt der
# Sollstunden einfließen.
ARBEITSCODES = {"A", "AS"}

QUELLE_KONFIG = "Konfiguration"
QUELLE_DURCHSCHNITT = "Ø der KW"
QUELLE_STANDARD = "Standardwert"


@dataclass(frozen=True)
class Abwesenheitszeile:
    """Eine Abwesenheit eines Mitarbeiters an einem Tag."""

    datum: dt.date
    wochentag: str
    p_id: str
    name: str
    anmeldung: str
    taetig_in: str
    code: str
    beschreibung: str
    kategorie: str
    iststunden: float
    sollstunden: float
    sollstunden_quelle: str
    teiltag: bool
    quelldatei: str

    @property
    def abwesenheitsstunden(self) -> float:
        if self.teiltag:
            return round(max(0.0, self.sollstunden - self.iststunden), 4)
        return round(self.sollstunden, 4)

    @property
    def tage(self) -> float:
        if self.sollstunden <= 0:
            return 0.0
        return round(self.abwesenheitsstunden / self.sollstunden, 4)


@dataclass(frozen=True)
class Mitarbeiterzeile:
    p_id: str
    name: str
    anmeldung: str
    taetig_in: str
    gearbeitete_stunden: float
    arbeitstage: int
    sollstunden: float
    sollstunden_quelle: str


@dataclass(frozen=True)
class Codezeile:
    code: str
    beschreibung: str
    kategorie: str
    tage: int
    mitarbeiter: int
    iststunden: float


@dataclass
class Wochenauswertung:
    """Ergebnis für genau eine Kalenderwoche."""

    jahr: int
    kw: int
    projekt: str
    kostenstelle: str
    vertragsart: str
    tagesdateien: list[Tagesdatei]
    abwesenheiten: list[Abwesenheitszeile]
    mitarbeiter: list[Mitarbeiterzeile]
    codes: list[Codezeile]
    kategorien: list[str]
    konfig: Konfiguration
    hinweise: list[str] = field(default_factory=list)

    @property
    def erster_tag(self) -> dt.date:
        return min(d.datum for d in self.tagesdateien)

    @property
    def letzter_tag(self) -> dt.date:
        return max(d.datum for d in self.tagesdateien)

    @property
    def bezeichnung(self) -> str:
        return f"KW {self.kw:02d}/{self.jahr}"

    def stunden(self, kategorie: str) -> float:
        return round(
            sum(z.abwesenheitsstunden
                for z in self.abwesenheiten if z.kategorie == kategorie),
            2,
        )

    def tage(self, kategorie: str) -> float:
        return round(
            sum(z.tage for z in self.abwesenheiten if z.kategorie == kategorie),
            2,
        )


def _sollstunden_ermitteln(
    schluessel: str,
    konfig: Konfiguration,
    arbeitsstunden: dict[str, list[float]],
) -> tuple[float, str]:
    """Sollstunden je Abwesenheitstag inklusive Herkunft der Zahl.

    Rangfolge: 1. Wert aus der Konfiguration, 2. Durchschnitt der in dieser
    Kalenderwoche tatsächlich gearbeiteten Tage, 3. Standardwert.
    """
    fest = konfig.sollstunden_override(schluessel)
    if fest is not None:
        return round(fest, 4), QUELLE_KONFIG

    if konfig.durchschnitt_als_fallback:
        werte = [s for s in arbeitsstunden.get(schluessel, []) if s > 0]
        if werte:
            return round(sum(werte) / len(werte), 4), QUELLE_DURCHSCHNITT

    return round(konfig.standard_sollstunden, 4), QUELLE_STANDARD


def _stammdaten(eintraege: list[Tageseintrag]) -> dict[str, Tageseintrag]:
    """Je P-Id den zuletzt gesehenen Eintrag als Namensquelle."""
    stamm: dict[str, Tageseintrag] = {}
    for e in eintraege:
        if e.schluessel:
            stamm[e.schluessel] = e
    return stamm


def woche_auswerten(
    tagesdateien: list[Tagesdatei],
    konfig: Konfiguration,
    hinweise: list[str] | None = None,
) -> Wochenauswertung:
    """Alle Tagesdateien einer Kalenderwoche zu einer Auswertung verdichten."""
    if not tagesdateien:
        raise ValueError("Es wurden keine Tagesdateien übergeben.")

    kws = {d.jahr_kw for d in tagesdateien}
    if len(kws) != 1:
        raise ValueError(
            "woche_auswerten erwartet Dateien genau einer Kalenderwoche, "
            f"erhalten: {sorted(kws)}"
        )
    jahr, kw = kws.pop()

    eintraege = [e for d in tagesdateien for e in d.eintraege]
    stamm = _stammdaten(eintraege)

    # Tatsächlich gearbeitete Stunden je Mitarbeiter (Basis für den Ø-Fallback).
    arbeitsstunden: dict[str, list[float]] = defaultdict(list)
    for e in eintraege:
        if e.schluessel and e.code in ARBEITSCODES and e.iststunden > 0:
            arbeitsstunden[e.schluessel].append(e.iststunden)

    sollstunden: dict[str, tuple[float, str]] = {
        schluessel: _sollstunden_ermitteln(schluessel, konfig, arbeitsstunden)
        for schluessel in stamm
    }

    abwesenheiten: list[Abwesenheitszeile] = []
    for e in sorted(eintraege, key=lambda x: (x.datum, x.name)):
        kategorie = konfig.kategorie(e.code)
        if kategorie is None:
            continue
        soll, quelle = sollstunden.get(
            e.schluessel,
            (round(konfig.standard_sollstunden, 4), QUELLE_STANDARD),
        )
        abwesenheiten.append(
            Abwesenheitszeile(
                datum=e.datum,
                wochentag=e.wochentag,
                p_id=e.p_id,
                name=e.name,
                anmeldung=e.anmeldung,
                taetig_in=e.taetig_in,
                code=e.code,
                beschreibung=CODE_BESCHREIBUNG.get(e.code, ""),
                kategorie=kategorie,
                iststunden=e.iststunden,
                sollstunden=soll,
                sollstunden_quelle=quelle,
                teiltag=konfig.ist_teiltag(e.code),
                quelldatei=e.quelldatei,
            )
        )

    mitarbeiter = []
    for schluessel, letzter in sorted(stamm.items(), key=lambda kv: kv[1].name):
        soll, quelle = sollstunden[schluessel]
        geleistet = arbeitsstunden.get(schluessel, [])
        mitarbeiter.append(
            Mitarbeiterzeile(
                p_id=letzter.p_id,
                name=letzter.name,
                anmeldung=letzter.anmeldung,
                taetig_in=letzter.taetig_in,
                gearbeitete_stunden=round(sum(geleistet), 4),
                arbeitstage=len(geleistet),
                sollstunden=soll,
                sollstunden_quelle=quelle,
            )
        )

    codes = _codes_zaehlen(eintraege, konfig)

    kategorien = [
        k for k in konfig.kategorie_reihenfolge
        if k in set(konfig.kategorien.values())
    ]

    return Wochenauswertung(
        jahr=jahr,
        kw=kw,
        projekt=tagesdateien[0].projekt,
        kostenstelle=tagesdateien[0].kostenstelle,
        vertragsart=tagesdateien[0].vertragsart,
        tagesdateien=list(tagesdateien),
        abwesenheiten=abwesenheiten,
        mitarbeiter=mitarbeiter,
        codes=codes,
        kategorien=kategorien,
        konfig=konfig,
        hinweise=list(hinweise or []),
    )


def _codes_zaehlen(
    eintraege: list[Tageseintrag], konfig: Konfiguration
) -> list[Codezeile]:
    """Alle vorkommenden Anwesenheitscodes zählen - auch nicht gewertete."""
    tage: dict[str, int] = defaultdict(int)
    stunden: dict[str, float] = defaultdict(float)
    personen: dict[str, set[str]] = defaultdict(set)

    for e in eintraege:
        if not e.code:
            continue
        tage[e.code] += 1
        stunden[e.code] += e.iststunden
        personen[e.code].add(e.schluessel)

    return [
        Codezeile(
            code=code,
            beschreibung=CODE_BESCHREIBUNG.get(code, "unbekannter Code"),
            kategorie=konfig.kategorie(code) or "- nicht gewertet -",
            tage=tage[code],
            mitarbeiter=len(personen[code]),
            iststunden=round(stunden[code], 4),
        )
        for code in sorted(tage)
    ]


def nach_kalenderwochen_gruppieren(
    tagesdateien: list[Tagesdatei],
) -> dict[tuple[int, int], list[Tagesdatei]]:
    gruppen: dict[tuple[int, int], list[Tagesdatei]] = defaultdict(list)
    for datei in tagesdateien:
        gruppen[datei.jahr_kw].append(datei)
    return {kw: sorted(d, key=lambda x: x.datum)
            for kw, d in sorted(gruppen.items())}
