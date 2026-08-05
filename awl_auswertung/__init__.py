"""Auswertung der Kranken-, Urlaubs- und Feiertagsstunden je Kalenderwoche.

Grundlage sind die täglichen AWL-Dateien (Tabellenblatt "AWL").
"""

from .auswertung import (
    Abwesenheitszeile,
    Wochenauswertung,
    nach_kalenderwochen_gruppieren,
    woche_auswerten,
)
from .bericht import bericht_schreiben
from .einlesen import (
    AWLFehler,
    Tagesdatei,
    Tageseintrag,
    tagesdatei_lesen,
    tagesdateien_lesen,
)
from .konfig import CODE_BESCHREIBUNG, Konfiguration

__all__ = [
    "Abwesenheitszeile",
    "AWLFehler",
    "CODE_BESCHREIBUNG",
    "Konfiguration",
    "Tagesdatei",
    "Tageseintrag",
    "Wochenauswertung",
    "bericht_schreiben",
    "nach_kalenderwochen_gruppieren",
    "tagesdatei_lesen",
    "tagesdateien_lesen",
    "woche_auswerten",
]
