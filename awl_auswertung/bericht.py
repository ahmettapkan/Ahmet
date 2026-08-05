"""Erzeugt die Excel-Auswertung einer Kalenderwoche."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from .auswertung import Wochenauswertung
from .einlesen import WOCHENTAGE
from .konfig import CODE_BESCHREIBUNG

SCHRIFT = "Arial"

FARBE_KOPF = "1F3864"        # dunkelblau, Tabellenkopf
FARBE_TITEL = "D9E2F3"       # hellblau, Titelblock
FARBE_SUMME = "FFF2CC"       # hellgelb, Summenzeilen
FARBE_EINGABE = "FFFF00"     # gelb, vom Anwender pflegbare Zellen
FARBE_HINWEIS = "FCE4D6"     # hellorange, Hinweise

RAHMEN = Border(*(Side(style="thin", color="BFBFBF"),) * 4)

FMT_STD = "#,##0.00"
FMT_TAGE = "#,##0.00"
FMT_DATUM = "DD.MM.YYYY"

BLATT_UEBERSICHT = "Übersicht"
BLATT_MITARBEITER = "Je Mitarbeiter"
BLATT_DETAILS = "Details"
BLATT_CODES = "Alle Codes"
BLATT_KONFIG = "Konfiguration"

# Spaltenaufbau des Blattes "Details" (1-basiert).
D_DATUM, D_KW, D_WOCHENTAG = 1, 2, 3
D_P_ID, D_NAME, D_ANMELDUNG, D_TAETIG = 4, 5, 6, 7
D_CODE, D_BESCHREIBUNG, D_KATEGORIE = 8, 9, 10
D_IST, D_SOLL, D_QUELLE, D_TEILTAG = 11, 12, 13, 14
D_ABW_STD, D_TAGE, D_DATEI = 15, 16, 17

DETAIL_KOPF = [
    "Datum", "KW", "Wochentag", "P-Id", "Mitarbeiter", "MA-Nr.", "tätig in",
    "Code", "Beschreibung", "Kategorie", "Iststunden", "Sollstunden/Tag",
    "Quelle Sollstunden", "Teiltag", "Abwesenheitsstunden", "Tage",
    "Quelldatei",
]
DETAIL_BREITEN = [12, 6, 12, 10, 30, 10, 16, 8, 28, 18, 12, 15, 18, 9, 20,
                  8, 46]

ERSTE_DETAILZEILE = 2


def _kopfzeile(blatt: Worksheet, zeile: int, texte: list[str],
               breiten: list[int] | None = None) -> None:
    for spalte, text in enumerate(texte, start=1):
        zelle = blatt.cell(zeile, spalte, text)
        zelle.font = Font(name=SCHRIFT, size=10, bold=True, color="FFFFFF")
        zelle.fill = PatternFill("solid", fgColor=FARBE_KOPF)
        zelle.alignment = Alignment(horizontal="center", vertical="center",
                                    wrap_text=True)
        zelle.border = RAHMEN
    if breiten:
        for spalte, breite in enumerate(breiten, start=1):
            blatt.column_dimensions[get_column_letter(spalte)].width = breite
    blatt.row_dimensions[zeile].height = 30


def _titel(blatt: Worksheet, zeile: int, text: str, spalten: int = 6) -> int:
    zelle = blatt.cell(zeile, 1, text)
    zelle.font = Font(name=SCHRIFT, size=12, bold=True, color="1F3864")
    zelle.fill = PatternFill("solid", fgColor=FARBE_TITEL)
    for spalte in range(2, spalten + 1):
        blatt.cell(zeile, spalte).fill = PatternFill("solid",
                                                     fgColor=FARBE_TITEL)
    return zeile + 1


def _text(blatt: Worksheet, zeile: int, spalte: int, wert,
          fett: bool = False, format: str | None = None):
    zelle = blatt.cell(zeile, spalte, wert)
    zelle.font = Font(name=SCHRIFT, size=10, bold=fett)
    if format:
        zelle.number_format = format
    return zelle


def bericht_schreiben(auswertung: Wochenauswertung, ziel: Path | str) -> Path:
    """Schreibt die Auswertung einer Kalenderwoche als .xlsx."""
    ziel = Path(ziel)
    mappe = Workbook()
    mappe.remove(mappe.active)

    detail_letzte = _details_blatt(mappe, auswertung)
    _uebersicht_blatt(mappe, auswertung, detail_letzte)
    _mitarbeiter_blatt(mappe, auswertung, detail_letzte)
    _codes_blatt(mappe, auswertung)
    _konfig_blatt(mappe, auswertung)

    # Übersicht als erstes Blatt anzeigen.
    mappe.move_sheet(BLATT_UEBERSICHT, offset=-mappe.sheetnames.index(
        BLATT_UEBERSICHT))
    mappe.active = 0

    ziel.parent.mkdir(parents=True, exist_ok=True)
    mappe.save(ziel)
    return ziel


# ---------------------------------------------------------------- Details ---

def _details_blatt(mappe: Workbook, a: Wochenauswertung) -> int:
    """Rohdatenblatt: eine Zeile je Abwesenheit. Rückgabe: letzte Datenzeile."""
    blatt = mappe.create_sheet(BLATT_DETAILS)
    _kopfzeile(blatt, 1, DETAIL_KOPF, DETAIL_BREITEN)

    zeile = ERSTE_DETAILZEILE
    for z in a.abwesenheiten:
        _text(blatt, zeile, D_DATUM, z.datum, format=FMT_DATUM)
        _text(blatt, zeile, D_KW, a.kw)
        _text(blatt, zeile, D_WOCHENTAG, z.wochentag)
        _text(blatt, zeile, D_P_ID, z.p_id)
        _text(blatt, zeile, D_NAME, z.name)
        _text(blatt, zeile, D_ANMELDUNG, z.anmeldung)
        _text(blatt, zeile, D_TAETIG, z.taetig_in)
        _text(blatt, zeile, D_CODE, z.code)
        _text(blatt, zeile, D_BESCHREIBUNG, z.beschreibung)
        _text(blatt, zeile, D_KATEGORIE, z.kategorie)
        _text(blatt, zeile, D_IST, z.iststunden, format=FMT_STD)

        # Sollstunden sind die einzige Eingabegröße dieses Blattes: wird sie
        # geändert, rechnen Details, Übersicht und Mitarbeiterblatt neu.
        soll = _text(blatt, zeile, D_SOLL, z.sollstunden, format=FMT_STD)
        soll.fill = PatternFill("solid", fgColor=FARBE_EINGABE)

        _text(blatt, zeile, D_QUELLE, z.sollstunden_quelle)
        _text(blatt, zeile, D_TEILTAG, "Ja" if z.teiltag else "Nein")
        _text(
            blatt, zeile, D_ABW_STD,
            f'=IF(N{zeile}="Ja",MAX(0,L{zeile}-K{zeile}),L{zeile})',
            fett=True, format=FMT_STD,
        )
        _text(blatt, zeile, D_TAGE,
              f"=IF(L{zeile}=0,0,O{zeile}/L{zeile})", format=FMT_TAGE)
        _text(blatt, zeile, D_DATEI, z.quelldatei)
        zeile += 1

    letzte = max(zeile - 1, ERSTE_DETAILZEILE)

    summe = zeile + 1
    _text(blatt, summe, D_KATEGORIE, "Summe:", fett=True)
    for spalte in (D_IST, D_ABW_STD, D_TAGE):
        buchstabe = get_column_letter(spalte)
        zelle = _text(
            blatt, summe, spalte,
            f"=SUM({buchstabe}{ERSTE_DETAILZEILE}:{buchstabe}{letzte})",
            fett=True, format=FMT_STD,
        )
        zelle.fill = PatternFill("solid", fgColor=FARBE_SUMME)

    blatt.auto_filter.ref = f"A1:{get_column_letter(D_DATEI)}{letzte}"
    blatt.freeze_panes = "A2"
    return letzte


# -------------------------------------------------------------- Übersicht ---

def _uebersicht_blatt(mappe: Workbook, a: Wochenauswertung,
                      detail_letzte: int) -> None:
    blatt = mappe.create_sheet(BLATT_UEBERSICHT)
    for spalte, breite in enumerate([26, 14, 14, 14, 14, 14, 14, 14], start=1):
        blatt.column_dimensions[get_column_letter(spalte)].width = breite

    zeile = _titel(
        blatt, 1,
        f"Kranken-, Urlaubs- und Feiertagsstunden – {a.bezeichnung}", 8,
    )
    zeile += 1

    kopfdaten = [
        ("Projekt:", a.projekt),
        ("Kostenstelle:", a.kostenstelle),
        ("Vertragsart:", a.vertragsart),
        ("Kalenderwoche:", a.bezeichnung),
        ("Zeitraum:", f"{a.erster_tag:%d.%m.%Y} – {a.letzter_tag:%d.%m.%Y}"),
        ("Ausgewertete Tage:", len(a.tagesdateien)),
        ("Mitarbeiter in der AWL:", len(a.mitarbeiter)),
    ]
    for beschriftung, wert in kopfdaten:
        _text(blatt, zeile, 1, beschriftung, fett=True)
        _text(blatt, zeile, 2, wert)
        zeile += 1

    zeile += 1
    zeile = _titel(blatt, zeile, "Summe je Kategorie", 8)

    _kopfzeile(blatt, zeile, ["Kategorie", "Stunden", "Tage"])
    zeile += 1
    erste_kategorie = zeile

    bereich_kat = _bereich(D_KATEGORIE, detail_letzte)
    bereich_std = _bereich(D_ABW_STD, detail_letzte)
    bereich_tage = _bereich(D_TAGE, detail_letzte)

    for kategorie in a.kategorien:
        _text(blatt, zeile, 1, kategorie, fett=True).border = RAHMEN
        _text(blatt, zeile, 2,
              f"=SUMIF({bereich_kat},$A{zeile},{bereich_std})",
              format=FMT_STD).border = RAHMEN
        _text(blatt, zeile, 3,
              f"=SUMIF({bereich_kat},$A{zeile},{bereich_tage})",
              format=FMT_TAGE).border = RAHMEN
        zeile += 1

    letzte_kategorie = zeile - 1
    _text(blatt, zeile, 1, "Gesamt", fett=True).fill = PatternFill(
        "solid", fgColor=FARBE_SUMME)
    for spalte in (2, 3):
        buchstabe = get_column_letter(spalte)
        zelle = _text(
            blatt, zeile, spalte,
            f"=SUM({buchstabe}{erste_kategorie}:{buchstabe}{letzte_kategorie})",
            fett=True, format=FMT_STD,
        )
        zelle.fill = PatternFill("solid", fgColor=FARBE_SUMME)
    zeile += 2

    # Matrix Kategorie x Tag
    zeile = _titel(blatt, zeile, "Stunden je Kategorie und Tag", 8)
    tage = [d.datum for d in a.tagesdateien]
    _kopfzeile(
        blatt, zeile,
        ["Kategorie"] + [f"{_kurztag(t)} {t:%d.%m.}" for t in tage] + ["Summe"],
    )
    zeile += 1
    matrix_erste = zeile
    bereich_datum = _bereich(D_DATUM, detail_letzte)

    # Unsichtbare Kriteriumszeile mit echten Datumswerten unterhalb der Matrix
    kriterium_zeile = matrix_erste + len(a.kategorien) + 2

    for kategorie in a.kategorien:
        _text(blatt, zeile, 1, kategorie, fett=True).border = RAHMEN
        for i in range(len(tage)):
            spalte = get_column_letter(2 + i)
            zelle = _text(
                blatt, zeile, 2 + i,
                f"=SUMIFS({bereich_std},{bereich_kat},$A{zeile},"
                f"{bereich_datum},{spalte}${kriterium_zeile})",
                format=FMT_STD,
            )
            zelle.border = RAHMEN
        ende = get_column_letter(1 + len(tage))
        _text(blatt, zeile, 2 + len(tage),
              f"=SUM(B{zeile}:{ende}{zeile})", fett=True,
              format=FMT_STD).border = RAHMEN
        zeile += 1

    matrix_letzte = zeile - 1
    _text(blatt, zeile, 1, "Gesamt", fett=True).fill = PatternFill(
        "solid", fgColor=FARBE_SUMME)
    for i in range(len(tage) + 1):
        spalte = get_column_letter(2 + i)
        zelle = _text(
            blatt, zeile, 2 + i,
            f"=SUM({spalte}{matrix_erste}:{spalte}{matrix_letzte})",
            fett=True, format=FMT_STD,
        )
        zelle.fill = PatternFill("solid", fgColor=FARBE_SUMME)
    zeile += 2

    # Kriteriumszeile (echte Datumswerte für die SUMIFS oben).
    _text(blatt, kriterium_zeile, 1,
          "Kriteriumszeile der Matrix – bitte nicht löschen:")
    blatt.cell(kriterium_zeile, 1).font = Font(name=SCHRIFT, size=8,
                                               italic=True, color="808080")
    for i, tag in enumerate(tage):
        zelle = _text(blatt, kriterium_zeile, 2 + i, tag, format=FMT_DATUM)
        zelle.font = Font(name=SCHRIFT, size=8, color="808080")
    zeile = max(zeile, kriterium_zeile + 2)

    # Grundlagen und Hinweise
    zeile = _titel(blatt, zeile, "Grundlagen dieser Auswertung", 8)
    grundlagen = [
        "Datenquelle: Tabellenblatt \"AWL\" der Tagesdateien, Zeilen 11–359 "
        "(Spalte I = Anwesenheit, Spalte H = Iststunden).",
        "Die AWL erfasst nur gearbeitete Stunden. Für Abwesenheitstage sind "
        "dort 0 Stunden hinterlegt.",
        "Die Abwesenheitsstunden werden deshalb aus den Sollstunden je Tag "
        "berechnet (Spalte L im Blatt \"Details\", gelb hinterlegt).",
        f"Standard-Sollstunden: {a.konfig.standard_sollstunden:.2f} h/Tag. "
        + ("Ist für einen Mitarbeiter kein Wert hinterlegt, wird der "
           "Durchschnitt seiner gearbeiteten Tage dieser KW verwendet."
           if a.konfig.durchschnitt_als_fallback
           else "Der Durchschnitts-Fallback ist deaktiviert."),
        "Bei Teiltag-Codes (Arbeit und Krank) gilt: "
        "Abwesenheitsstunden = Sollstunden − bereits erfasste Iststunden.",
        "Sollstunden im Blatt \"Details\" ändern ⇒ alle Summen rechnen neu.",
    ]
    for text in grundlagen:
        zelle = _text(blatt, zeile, 1, "• " + text)
        zelle.alignment = Alignment(wrap_text=False)
        zeile += 1

    if a.hinweise:
        zeile += 1
        zeile = _titel(blatt, zeile, "Hinweise zum Dateibestand", 8)
        for text in a.hinweise:
            zelle = _text(blatt, zeile, 1, "• " + text)
            zelle.fill = PatternFill("solid", fgColor=FARBE_HINWEIS)
            zeile += 1

    zeile += 1
    zeile = _titel(blatt, zeile, "Ausgewertete Dateien", 8)
    _kopfzeile(blatt, zeile, ["Datum", "Wochentag", "Datei"])
    blatt.column_dimensions["C"].width = 60
    zeile += 1
    for datei in a.tagesdateien:
        _text(blatt, zeile, 1, datei.datum, format=FMT_DATUM)
        _text(blatt, zeile, 2, WOCHENTAGE[datei.datum.weekday()])
        _text(blatt, zeile, 3, datei.pfad.name)
        zeile += 1


# ------------------------------------------------------------ Mitarbeiter ---

def _mitarbeiter_blatt(mappe: Workbook, a: Wochenauswertung,
                       detail_letzte: int) -> None:
    blatt = mappe.create_sheet(BLATT_MITARBEITER)

    kopf = ["P-Id", "Mitarbeiter", "MA-Nr.", "tätig in", "Sollstunden/Tag",
            "Quelle Sollstunden", "Gearbeitete Std.", "Arbeitstage"]
    breiten = [10, 30, 10, 16, 14, 18, 15, 12]
    for kategorie in a.kategorien:
        kopf += [f"{kategorie} Std.", f"{kategorie} Tage"]
        breiten += [13, 13]
    kopf += ["Abwesenheit Std. gesamt"]
    breiten += [20]

    _kopfzeile(blatt, 1, kopf, breiten)

    bereich_name = _bereich(D_NAME, detail_letzte)
    bereich_kat = _bereich(D_KATEGORIE, detail_letzte)
    bereich_std = _bereich(D_ABW_STD, detail_letzte)
    bereich_tage = _bereich(D_TAGE, detail_letzte)

    zeile = 2
    for m in a.mitarbeiter:
        _text(blatt, zeile, 1, m.p_id)
        _text(blatt, zeile, 2, m.name)
        _text(blatt, zeile, 3, m.anmeldung)
        _text(blatt, zeile, 4, m.taetig_in)
        _text(blatt, zeile, 5, m.sollstunden, format=FMT_STD)
        _text(blatt, zeile, 6, m.sollstunden_quelle)
        _text(blatt, zeile, 7, m.gearbeitete_stunden, format=FMT_STD)
        _text(blatt, zeile, 8, m.arbeitstage)

        spalte = 9
        for kategorie in a.kategorien:
            kat_zelle = f'"{kategorie}"'
            _text(blatt, zeile, spalte,
                  f"=SUMIFS({bereich_std},{bereich_name},$B{zeile},"
                  f"{bereich_kat},{kat_zelle})", format=FMT_STD)
            _text(blatt, zeile, spalte + 1,
                  f"=SUMIFS({bereich_tage},{bereich_name},$B{zeile},"
                  f"{bereich_kat},{kat_zelle})", format=FMT_TAGE)
            spalte += 2

        _text(blatt, zeile, spalte,
              f"=SUMIF({bereich_name},$B{zeile},{bereich_std})",
              fett=True, format=FMT_STD)
        zeile += 1

    letzte = zeile - 1
    if letzte >= 2:
        _text(blatt, zeile, 2, "Summe:", fett=True)
        for s in range(7, spalte + 1):
            buchstabe = get_column_letter(s)
            zelle = _text(blatt, zeile, s,
                          f"=SUM({buchstabe}2:{buchstabe}{letzte})",
                          fett=True, format=FMT_STD)
            zelle.fill = PatternFill("solid", fgColor=FARBE_SUMME)
        blatt.auto_filter.ref = f"A1:{get_column_letter(spalte)}{letzte}"

    blatt.freeze_panes = "C2"


# ------------------------------------------------------------- Alle Codes ---

def _codes_blatt(mappe: Workbook, a: Wochenauswertung) -> None:
    blatt = mappe.create_sheet(BLATT_CODES)
    _kopfzeile(
        blatt, 1,
        ["Code", "Beschreibung", "Kategorie in dieser Auswertung",
         "Einträge (Tage)", "betroffene Mitarbeiter", "erfasste Iststunden"],
        [10, 32, 28, 16, 22, 20],
    )
    zeile = 2
    for c in a.codes:
        _text(blatt, zeile, 1, c.code, fett=True)
        _text(blatt, zeile, 2, c.beschreibung)
        _text(blatt, zeile, 3, c.kategorie)
        _text(blatt, zeile, 4, c.tage)
        _text(blatt, zeile, 5, c.mitarbeiter)
        _text(blatt, zeile, 6, c.iststunden, format=FMT_STD)
        if c.kategorie == "- nicht gewertet -":
            for s in range(1, 7):
                blatt.cell(zeile, s).font = Font(name=SCHRIFT, size=10,
                                                 color="808080")
        zeile += 1

    zeile += 1
    _text(blatt, zeile, 1,
          "Dieses Blatt listet jeden in der KW vorgekommenen Anwesenheitscode. "
          "So ist erkennbar, dass keine Abwesenheit unbemerkt herausfällt.")
    blatt.cell(zeile, 1).font = Font(name=SCHRIFT, size=9, italic=True)
    blatt.freeze_panes = "A2"


# ----------------------------------------------------------- Konfiguration ---

def _konfig_blatt(mappe: Workbook, a: Wochenauswertung) -> None:
    blatt = mappe.create_sheet(BLATT_KONFIG)
    for spalte, breite in enumerate([34, 30, 34], start=1):
        blatt.column_dimensions[get_column_letter(spalte)].width = breite

    zeile = _titel(blatt, 1, "Verwendete Konfiguration", 3)
    zeile += 1

    _text(blatt, zeile, 1, "Standard-Sollstunden je Tag", fett=True)
    _text(blatt, zeile, 2, a.konfig.standard_sollstunden, format=FMT_STD)
    _text(blatt, zeile, 3, "greift, wenn kein anderer Wert ermittelbar ist")
    zeile += 1

    _text(blatt, zeile, 1, "Durchschnitt als Rückfallwert", fett=True)
    _text(blatt, zeile, 2,
          "Ja" if a.konfig.durchschnitt_als_fallback else "Nein")
    _text(blatt, zeile, 3,
          "Ø der gearbeiteten Stunden desselben Mitarbeiters in dieser KW")
    zeile += 2

    zeile = _titel(blatt, zeile, "Sollstunden je Mitarbeiter", 3)
    if a.konfig.sollstunden_je_mitarbeiter:
        _kopfzeile(blatt, zeile, ["P-Id", "Sollstunden/Tag", ""])
        zeile += 1
        for p_id, stunden in sorted(
            a.konfig.sollstunden_je_mitarbeiter.items()
        ):
            _text(blatt, zeile, 1, p_id)
            _text(blatt, zeile, 2, float(stunden), format=FMT_STD)
            zeile += 1
    else:
        _text(blatt, zeile, 1,
              "Keine individuellen Sollstunden hinterlegt – siehe "
              "konfiguration.json.")
        zeile += 1
    zeile += 1

    zeile = _titel(blatt, zeile, "Zuordnung Anwesenheitscode → Kategorie", 3)
    _kopfzeile(blatt, zeile, ["Code", "Beschreibung (AWL)", "Kategorie"])
    zeile += 1
    for code in sorted(CODE_BESCHREIBUNG):
        kategorie = a.konfig.kategorie(code)
        _text(blatt, zeile, 1, code, fett=bool(kategorie))
        _text(blatt, zeile, 2, CODE_BESCHREIBUNG[code])
        _text(blatt, zeile, 3, kategorie or "– nicht gewertet –")
        if not kategorie:
            for s in range(1, 4):
                blatt.cell(zeile, s).font = Font(name=SCHRIFT, size=10,
                                                 color="808080")
        zeile += 1
    zeile += 1

    zeile = _titel(blatt, zeile, "Teiltag-Codes", 3)
    _text(blatt, zeile, 1, ", ".join(a.konfig.teiltag_codes) or "keine")
    _text(blatt, zeile, 2,
          "Abwesenheitsstunden = Sollstunden − Iststunden")
    zeile += 2

    zeile = _titel(blatt, zeile, "Annahmen", 3)
    annahmen = [
        "Die Anwesenheitscodes stammen aus der Auswahlliste AWL!DD9:DE30 der "
        "gelieferten Tagesdatei.",
        "In der AWL sind Abwesenheitstage stets mit 0 Iststunden erfasst; "
        "eine Sollstunden-Angabe je Mitarbeiter enthält die Datei nicht.",
        "Die Sollstunden sind daher eine Annahme dieser Auswertung und in "
        "konfiguration.json bzw. im Blatt \"Details\" (gelb) änderbar.",
        "Liegen für einen Tag mehrere Dateien vor, wird die zuletzt "
        "geänderte verwendet (Korrekturfassung).",
        "Die Kalenderwoche wird nach ISO 8601 aus AWL!D6 bestimmt.",
    ]
    for text in annahmen:
        _text(blatt, zeile, 1, "• " + text)
        zeile += 1


def _kurztag(datum) -> str:
    """Deutsche Wochentagsabkürzung, unabhängig vom Gebietsschema."""
    return WOCHENTAGE[datum.weekday()][:2]


def _bereich(spalte: int, letzte_zeile: int) -> str:
    """Absoluter Bereich einer Detailspalte, z. B. Details!$O$2:$O$57."""
    buchstabe = get_column_letter(spalte)
    return (f"'{BLATT_DETAILS}'!${buchstabe}${ERSTE_DETAILZEILE}"
            f":${buchstabe}${letzte_zeile}")
