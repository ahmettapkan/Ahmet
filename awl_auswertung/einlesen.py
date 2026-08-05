"""Einlesen der Tagesdateien (Tabellenblatt "AWL")."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path

import openpyxl

BLATT = "AWL"

# Feste Koordinaten des AWL-Blattes (1-basiert).
ZEILE_KOPF = 6          # B6 "Datum: ", D6 = Datum der Tagesdatei
SPALTE_DATUM = 4        # D
ZEILE_TITEL = 1         # G1 Projekt, J1 Kostenstelle, N1 Vertragsart
SPALTE_PROJEKT = 7      # G
SPALTE_KOSTENSTELLE = 10  # J
SPALTE_VERTRAGSART = 14   # N

ERSTE_DATENZEILE = 11
LETZTE_DATENZEILE = 359  # 360 enthält die Summenzeile

SPALTE_MA_NR = 1        # A  Mitarbeiter-Nr. (interne lfd. Nummer)
SPALTE_P_ID = 3         # C  P-Id
SPALTE_NAME = 4         # D  Mitarbeiter
SPALTE_ANMELDUNG = 5    # E  Anmeldung (MA-Nr., z. B. H474)
SPALTE_TAETIG_IN = 6    # F  tätig in
SPALTE_STUNDEN = 8      # H  Stunden gesamt pro Tag (dezimal)
SPALTE_ANWESENHEIT = 9  # I  Anwesenheitscode

# Bis hierhin muss jede Zeile gelesen werden (N = Vertragsart in Zeile 1).
MAX_SPALTE = max(SPALTE_VERTRAGSART, SPALTE_ANWESENHEIT)

WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag",
              "Freitag", "Samstag", "Sonntag"]


class AWLFehler(Exception):
    """Die Datei ist keine verwertbare AWL-Tagesdatei."""


@dataclass(frozen=True)
class Tageseintrag:
    """Eine Mitarbeiterzeile eines Tages."""

    datum: dt.date
    p_id: str
    name: str
    anmeldung: str
    taetig_in: str
    code: str
    iststunden: float
    quelldatei: str

    @property
    def jahr_kw(self) -> tuple[int, int]:
        iso = self.datum.isocalendar()
        return iso[0], iso[1]

    @property
    def wochentag(self) -> str:
        return WOCHENTAGE[self.datum.weekday()]

    @property
    def schluessel(self) -> str:
        """Eindeutiger Mitarbeiterschlüssel; ohne P-Id greift der Name."""
        return self.p_id or self.name


@dataclass(frozen=True)
class Tagesdatei:
    """Eine eingelesene AWL-Tagesdatei."""

    pfad: Path
    datum: dt.date
    projekt: str
    kostenstelle: str
    vertragsart: str
    eintraege: tuple[Tageseintrag, ...]

    @property
    def jahr_kw(self) -> tuple[int, int]:
        iso = self.datum.isocalendar()
        return iso[0], iso[1]


# Formelfehler in Vorratszeilen (z. B. #N/A aus einem VLOOKUP) sind kein Inhalt.
FEHLERWERTE = {"#N/A", "#WERT!", "#VALUE!", "#BEZUG!", "#REF!",
               "#NAME?", "#DIV/0!", "#NULL!", "#ZAHL!", "#NUM!"}


def _wert(zeile: tuple, spalte: int):
    """Zellwert aus einer iter_rows-Zeile; kurze Zeilen liefern None."""
    index = spalte - 1
    return zeile[index].value if index < len(zeile) else None


def _text(wert) -> str:
    """Zellwert als bereinigter Text; 0, Fehlerwerte und None werden zu ""."""
    if wert is None:
        return ""
    if isinstance(wert, float) and wert.is_integer():
        wert = int(wert)
    text = str(wert).strip()
    if text == "0" or text in FEHLERWERTE:
        return ""
    return text


def _name(wert) -> str:
    """Mitarbeitername; leere Vorratszeilen liefern über die Formel ", "."""
    text = _text(wert)
    return "" if not text.replace(",", "").strip() else text


def _zahl(wert) -> float:
    if isinstance(wert, (int, float)):
        return float(wert)
    if isinstance(wert, str):
        try:
            return float(wert.replace(",", "."))
        except ValueError:
            return 0.0
    return 0.0


def _datum(wert) -> dt.date | None:
    if isinstance(wert, dt.datetime):
        return wert.date()
    if isinstance(wert, dt.date):
        return wert
    return None


def tagesdatei_lesen(pfad: Path | str) -> Tagesdatei:
    """Eine AWL-Tagesdatei (.xlsm/.xlsx) einlesen.

    Gelesen werden ausschließlich zwischengespeicherte Werte, die Datei wird
    nicht verändert.
    """
    pfad = Path(pfad)
    mappe = openpyxl.load_workbook(pfad, read_only=True, data_only=True)
    try:
        if BLATT not in mappe.sheetnames:
            raise AWLFehler(f"{pfad.name}: Tabellenblatt '{BLATT}' fehlt.")
        blatt = mappe[BLATT]

        datum: dt.date | None = None
        projekt = kostenstelle = vertragsart = ""
        eintraege: list[Tageseintrag] = []

        # Im read_only-Modus ist der wahlfreie Zellzugriff sehr langsam,
        # deshalb wird das Blatt genau einmal sequenziell durchlaufen.
        # iter_rows liefert im read_only-Modus lückenlos alle Zeilen des
        # Bereichs, leere Zellen als EmptyCell ohne .row - daher enumerate.
        for nr, zeile in enumerate(
            blatt.iter_rows(min_row=1, max_row=LETZTE_DATENZEILE,
                            max_col=MAX_SPALTE),
            start=1,
        ):
            if nr == ZEILE_TITEL:
                projekt = _text(_wert(zeile, SPALTE_PROJEKT))
                kostenstelle = _text(_wert(zeile, SPALTE_KOSTENSTELLE))
                vertragsart = _text(_wert(zeile, SPALTE_VERTRAGSART))
                continue

            if nr == ZEILE_KOPF:
                datum = _datum(_wert(zeile, SPALTE_DATUM))
                continue

            if nr < ERSTE_DATENZEILE:
                continue

            name = _name(_wert(zeile, SPALTE_NAME))
            if not name:
                continue  # leere Vorratszeile

            eintraege.append(
                Tageseintrag(
                    datum=dt.date(1900, 1, 1),  # wird unten korrigiert
                    p_id=_text(_wert(zeile, SPALTE_P_ID)),
                    name=name,
                    anmeldung=_text(_wert(zeile, SPALTE_ANMELDUNG)),
                    taetig_in=_text(_wert(zeile, SPALTE_TAETIG_IN)),
                    code=_text(_wert(zeile, SPALTE_ANWESENHEIT)),
                    iststunden=round(_zahl(_wert(zeile, SPALTE_STUNDEN)), 4),
                    quelldatei=pfad.name,
                )
            )
    finally:
        mappe.close()

    if datum is None:
        raise AWLFehler(
            f"{pfad.name}: In Zelle AWL!D{ZEILE_KOPF} steht kein gültiges Datum."
        )

    eintraege = [
        Tageseintrag(
            datum=datum,
            p_id=e.p_id,
            name=e.name,
            anmeldung=e.anmeldung,
            taetig_in=e.taetig_in,
            code=e.code,
            iststunden=e.iststunden,
            quelldatei=e.quelldatei,
        )
        for e in eintraege
    ]

    return Tagesdatei(
        pfad=pfad,
        datum=datum,
        projekt=projekt,
        kostenstelle=kostenstelle,
        vertragsart=vertragsart,
        eintraege=tuple(eintraege),
    )


def dateien_sammeln(pfade: list[Path | str]) -> list[Path]:
    """Aus Dateien und/oder Ordnern die Liste der AWL-Dateien bilden."""
    gefunden: list[Path] = []
    for eintrag in pfade:
        p = Path(eintrag)
        if p.is_dir():
            for kandidat in sorted(p.iterdir()):
                if _ist_awl_datei(kandidat):
                    gefunden.append(kandidat)
        elif p.is_file():
            if not _ist_awl_datei(p):
                raise AWLFehler(f"{p.name}: keine .xlsx-/.xlsm-Datei.")
            gefunden.append(p)
        else:
            raise AWLFehler(f"{p}: Datei oder Ordner nicht gefunden.")
    return gefunden


def _ist_awl_datei(pfad: Path) -> bool:
    if not pfad.is_file():
        return False
    if pfad.name.startswith("~$") or pfad.name.startswith("."):
        return False  # Excel-Sperrdateien
    return pfad.suffix.lower() in {".xlsx", ".xlsm"}


def tagesdateien_lesen(
    pfade: list[Path | str],
) -> tuple[list[Tagesdatei], list[str]]:
    """Alle Dateien einlesen und Dubletten je Datum auflösen.

    Liegen mehrere Dateien für denselben Tag vor (z. B. eine Korrekturfassung),
    gewinnt die zuletzt geänderte Datei. Rückgabe: (Tagesdateien, Hinweise).
    """
    hinweise: list[str] = []
    je_datum: dict[dt.date, Tagesdatei] = {}

    for pfad in dateien_sammeln(pfade):
        datei = tagesdatei_lesen(pfad)
        vorhanden = je_datum.get(datei.datum)
        if vorhanden is None:
            je_datum[datei.datum] = datei
            continue
        neuer = max(
            (vorhanden, datei), key=lambda d: d.pfad.stat().st_mtime
        )
        verworfen = datei if neuer is vorhanden else vorhanden
        je_datum[datei.datum] = neuer
        hinweise.append(
            f"Mehrere Dateien für {datei.datum:%d.%m.%Y}: verwendet wird "
            f"'{neuer.pfad.name}' (zuletzt geändert), ignoriert wird "
            f"'{verworfen.pfad.name}'."
        )

    return [je_datum[d] for d in sorted(je_datum)], hinweise
