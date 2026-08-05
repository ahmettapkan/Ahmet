"""Kommandozeile: aus AWL-Tagesdateien eine KW-Auswertung erzeugen."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .auswertung import (
    Wochenauswertung,
    nach_kalenderwochen_gruppieren,
    woche_auswerten,
)
from .bericht import bericht_schreiben
from .einlesen import AWLFehler, tagesdateien_lesen
from .konfig import Konfiguration

BESCHREIBUNG = """\
Ermittelt aus den täglichen AWL-Dateien die Kranken-, Urlaubs- und
Feiertagsstunden einer Kalenderwoche und schreibt sie als Excel-Bericht.
"""

BEISPIELE = """\
Beispiele:
  # alle Dateien eines Ordners auswerten, je KW ein Bericht
  python -m awl_auswertung ./KW31

  # einzelne Dateien, eigener Zielordner
  python -m awl_auswertung Mo.xlsm Di.xlsm -z ./Auswertungen

  # nur KW 31 aus einem Ordner mit mehreren Wochen
  python -m awl_auswertung ./AWL-Archiv --kw 31 --jahr 2026

  # mit eigener Konfiguration (Sollstunden, Kategorien)
  python -m awl_auswertung ./KW31 -k konfiguration.json
"""


def argumente(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="awl_auswertung",
        description=BESCHREIBUNG,
        epilog=BEISPIELE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "quellen", nargs="+", metavar="PFAD",
        help="AWL-Tagesdateien (.xlsm/.xlsx) und/oder Ordner damit",
    )
    parser.add_argument(
        "-z", "--ziel", default=".", metavar="ORDNER",
        help="Zielordner für die Berichte (Standard: aktueller Ordner)",
    )
    parser.add_argument(
        "-k", "--konfiguration", metavar="DATEI",
        help="JSON-Datei mit Sollstunden und Kategorien",
    )
    parser.add_argument(
        "--kw", type=int, metavar="NR",
        help="nur diese Kalenderwoche auswerten",
    )
    parser.add_argument(
        "--jahr", type=int, metavar="JJJJ",
        help="Jahr zur Kalenderwoche (nur zusammen mit --kw sinnvoll)",
    )
    parser.add_argument(
        "-q", "--still", action="store_true",
        help="keine Zusammenfassung auf der Konsole ausgeben",
    )
    return parser.parse_args(argv)


def dateiname(a: Wochenauswertung) -> str:
    kostenstelle = f"_{a.kostenstelle}" if a.kostenstelle else ""
    return f"AWL_Auswertung{kostenstelle}_KW{a.kw:02d}_{a.jahr}.xlsx"


def zusammenfassung(a: Wochenauswertung, ziel: Path) -> str:
    zeilen = [
        f"{a.bezeichnung}  ({a.erster_tag:%d.%m.%Y} – "
        f"{a.letzter_tag:%d.%m.%Y}, {len(a.tagesdateien)} Tagesdatei(en))",
    ]
    for kategorie in a.kategorien:
        stunden = a.stunden(kategorie)
        tage = a.tage(kategorie)
        if stunden or tage:
            zeilen.append(
                f"    {kategorie:<20} {stunden:>9.2f} Std.  "
                f"{tage:>7.2f} Tage"
            )
    if len(zeilen) == 1:
        zeilen.append("    keine Abwesenheiten in dieser Woche")
    for hinweis in a.hinweise:
        zeilen.append(f"    Hinweis: {hinweis}")
    zeilen.append(f"    -> {ziel}")
    return "\n".join(zeilen)


def main(argv: list[str] | None = None) -> int:
    args = argumente(argv)

    try:
        konfig = Konfiguration.laden(args.konfiguration)
    except (OSError, ValueError) as fehler:
        print(f"Fehler in der Konfiguration: {fehler}", file=sys.stderr)
        return 2

    try:
        tagesdateien, hinweise = tagesdateien_lesen(args.quellen)
    except AWLFehler as fehler:
        print(f"Fehler beim Einlesen: {fehler}", file=sys.stderr)
        return 2

    if not tagesdateien:
        print("Es wurden keine AWL-Dateien gefunden.", file=sys.stderr)
        return 1

    gruppen = nach_kalenderwochen_gruppieren(tagesdateien)

    if args.kw is not None:
        gruppen = {
            (jahr, kw): dateien
            for (jahr, kw), dateien in gruppen.items()
            if kw == args.kw and (args.jahr is None or jahr == args.jahr)
        }
        if not gruppen:
            print(
                f"Für KW {args.kw}"
                + (f"/{args.jahr}" if args.jahr else "")
                + " wurden keine Tagesdateien gefunden.",
                file=sys.stderr,
            )
            return 1

    zielordner = Path(args.ziel)
    ausgaben: list[str] = []

    for dateien in gruppen.values():
        namen = {d.pfad.name for d in dateien}
        auswertung = woche_auswerten(
            dateien,
            konfig,
            hinweise=[h for h in hinweise
                      if any(n in h for n in namen)] or None,
        )
        pfad = bericht_schreiben(auswertung, zielordner / dateiname(auswertung))
        ausgaben.append(zusammenfassung(auswertung, pfad))

    if not args.still:
        print("\n\n".join(ausgaben))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
