"""Erzeugt AWL-Testdateien im Aufbau der echten Tagesdatei."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from openpyxl import Workbook

from awl_auswertung.einlesen import (
    ERSTE_DATENZEILE,
    SPALTE_ANMELDUNG,
    SPALTE_ANWESENHEIT,
    SPALTE_DATUM,
    SPALTE_KOSTENSTELLE,
    SPALTE_NAME,
    SPALTE_P_ID,
    SPALTE_PROJEKT,
    SPALTE_STUNDEN,
    SPALTE_TAETIG_IN,
    SPALTE_VERTRAGSART,
    ZEILE_KOPF,
    ZEILE_TITEL,
)


def awl_datei_schreiben(
    pfad: Path,
    datum: dt.date,
    zeilen: list[tuple[str, str, str, str, float]],
    projekt: str = "TEDi Kamen",
    kostenstelle: str = "2100",
    vertragsart: str = "Werkvertrag",
    fuellzeilen: int = 3,
) -> Path:
    """Schreibt eine AWL-Datei.

    `zeilen` je Eintrag: (P-Id, Name, MA-Nr., Anwesenheitscode, Iststunden).
    `fuellzeilen` erzeugt leere Vorratszeilen, wie sie die Originaldatei
    enthält (Name ", ", P-Id "#N/A").
    """
    mappe = Workbook()
    blatt = mappe.active
    blatt.title = "AWL"

    blatt.cell(ZEILE_TITEL, SPALTE_PROJEKT, projekt)
    blatt.cell(ZEILE_TITEL, SPALTE_KOSTENSTELLE, kostenstelle)
    blatt.cell(ZEILE_TITEL, SPALTE_VERTRAGSART, vertragsart)
    blatt.cell(ZEILE_KOPF, SPALTE_DATUM, dt.datetime.combine(datum, dt.time()))

    zeile = ERSTE_DATENZEILE
    for p_id, name, anmeldung, code, stunden in zeilen:
        blatt.cell(zeile, SPALTE_P_ID, p_id)
        blatt.cell(zeile, SPALTE_NAME, name)
        blatt.cell(zeile, SPALTE_ANMELDUNG, anmeldung)
        blatt.cell(zeile, SPALTE_TAETIG_IN, "Kommissionierung")
        blatt.cell(zeile, SPALTE_STUNDEN, stunden)
        blatt.cell(zeile, SPALTE_ANWESENHEIT, code)
        zeile += 1

    for _ in range(fuellzeilen):
        blatt.cell(zeile, SPALTE_P_ID, "#N/A")
        blatt.cell(zeile, SPALTE_NAME, ", ")
        blatt.cell(zeile, SPALTE_STUNDEN, 0)
        zeile += 1

    pfad.parent.mkdir(parents=True, exist_ok=True)
    mappe.save(pfad)
    return pfad
