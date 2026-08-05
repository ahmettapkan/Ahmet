"""Tests der KW-Auswertung."""

from __future__ import annotations

import datetime as dt
import json
import os
import time

import pytest
from openpyxl import load_workbook

from awl_auswertung import (
    AWLFehler,
    Konfiguration,
    bericht_schreiben,
    nach_kalenderwochen_gruppieren,
    tagesdatei_lesen,
    tagesdateien_lesen,
    woche_auswerten,
)
from awl_auswertung.auswertung import (
    QUELLE_DURCHSCHNITT,
    QUELLE_KONFIG,
    QUELLE_STANDARD,
)
from awl_auswertung.cli import main
from tests.hilfsmittel import awl_datei_schreiben

MONTAG = dt.date(2026, 7, 27)  # KW 31/2026


def woche_anlegen(ordner):
    """Eine vollständige Woche Mo–Fr mit typischen Fällen."""
    # (P-Id, Name, MA-Nr., Code, Iststunden)
    tage = {
        MONTAG: [
            ("100", "Alt, Anna", "H100", "A", 8.0),
            ("200", "Berg, Bernd", "H200", "K2", 0.0),
            ("300", "Cerny, Carla", "H300", "U2", 0.0),
            ("400", "Dorn, Dirk", "H400", "EX", 0.0),
        ],
        MONTAG + dt.timedelta(days=1): [
            ("100", "Alt, Anna", "H100", "A", 7.0),
            ("200", "Berg, Bernd", "H200", "K2", 0.0),
            ("300", "Cerny, Carla", "H300", "U2", 0.0),
            ("400", "Dorn, Dirk", "H400", "FU", 0.0),
        ],
        MONTAG + dt.timedelta(days=2): [
            ("100", "Alt, Anna", "H100", "AK", 3.0),  # Teiltag: 3 h gearbeitet
            ("200", "Berg, Bernd", "H200", "A", 8.0),
            ("300", "Cerny, Carla", "H300", "U2", 0.0),
            ("400", "Dorn, Dirk", "H400", "KA", 0.0),
        ],
        MONTAG + dt.timedelta(days=3): [
            ("100", "Alt, Anna", "H100", "Ft", 0.0),
            ("200", "Berg, Bernd", "H200", "Ft", 0.0),
            ("300", "Cerny, Carla", "H300", "Ft", 0.0),
            ("400", "Dorn, Dirk", "H400", "Ft", 0.0),
        ],
        MONTAG + dt.timedelta(days=4): [
            ("100", "Alt, Anna", "H100", "A", 8.0),
            ("200", "Berg, Bernd", "H200", "UU", 0.0),
            ("300", "Cerny, Carla", "H300", "A", 6.0),
            ("400", "Dorn, Dirk", "H400", "A", 8.0),
        ],
    }
    for datum, zeilen in tage.items():
        awl_datei_schreiben(ordner / f"AWL_{datum:%d.%m.%Y}.xlsx", datum, zeilen)
    return ordner


# ------------------------------------------------------------- Einlesen ---

def test_liest_kopfdaten_und_zeilen(tmp_path):
    pfad = awl_datei_schreiben(
        tmp_path / "tag.xlsx", MONTAG,
        [("100", "Alt, Anna", "H100", "K2", 0.0)],
    )
    datei = tagesdatei_lesen(pfad)

    assert datei.datum == MONTAG
    assert datei.projekt == "TEDi Kamen"
    assert datei.kostenstelle == "2100"
    assert datei.vertragsart == "Werkvertrag"
    assert datei.jahr_kw == (2026, 31)
    assert len(datei.eintraege) == 1
    assert datei.eintraege[0].name == "Alt, Anna"
    assert datei.eintraege[0].code == "K2"


def test_ueberspringt_leere_vorratszeilen(tmp_path):
    """Ungenutzte Zeilen liefern über die AWL-Formeln ", " und #N/A."""
    pfad = awl_datei_schreiben(
        tmp_path / "tag.xlsx", MONTAG,
        [("100", "Alt, Anna", "H100", "A", 8.0)],
        fuellzeilen=25,
    )
    assert len(tagesdatei_lesen(pfad).eintraege) == 1


def test_fehlendes_awl_blatt(tmp_path):
    from openpyxl import Workbook

    mappe = Workbook()
    mappe.active.title = "Irgendwas"
    mappe.save(tmp_path / "falsch.xlsx")

    with pytest.raises(AWLFehler, match="AWL"):
        tagesdatei_lesen(tmp_path / "falsch.xlsx")


def test_fehlendes_datum(tmp_path):
    from openpyxl import Workbook

    mappe = Workbook()
    mappe.active.title = "AWL"
    mappe.save(tmp_path / "ohne_datum.xlsx")

    with pytest.raises(AWLFehler, match="Datum"):
        tagesdatei_lesen(tmp_path / "ohne_datum.xlsx")


def test_korrekturdatei_gewinnt(tmp_path):
    alt = awl_datei_schreiben(
        tmp_path / "AWL_27.07.2026.xlsx", MONTAG,
        [("100", "Alt, Anna", "H100", "A", 8.0)],
    )
    neu = awl_datei_schreiben(
        tmp_path / "AWL_27.07.2026_Korrektur.xlsx", MONTAG,
        [("100", "Alt, Anna", "H100", "K2", 0.0)],
    )
    # Änderungszeitpunkte eindeutig auseinanderziehen
    os.utime(alt, (time.time() - 600, time.time() - 600))
    os.utime(neu, None)

    dateien, hinweise = tagesdateien_lesen([tmp_path])

    assert len(dateien) == 1
    assert dateien[0].pfad.name == neu.name
    assert dateien[0].eintraege[0].code == "K2"
    assert any("Korrektur" in h for h in hinweise)


def test_excel_sperrdateien_werden_ignoriert(tmp_path):
    awl_datei_schreiben(
        tmp_path / "AWL_27.07.2026.xlsx", MONTAG,
        [("100", "Alt, Anna", "H100", "A", 8.0)],
    )
    (tmp_path / "~$AWL_27.07.2026.xlsx").write_bytes(b"kaputt")

    dateien, _ = tagesdateien_lesen([tmp_path])
    assert len(dateien) == 1


# ----------------------------------------------------------- Auswertung ---

def test_stunden_je_kategorie(tmp_path):
    """Feste 8 h Soll, damit die Erwartungswerte nachrechenbar bleiben."""
    dateien, _ = tagesdateien_lesen([woche_anlegen(tmp_path)])
    a = woche_auswerten(dateien, Konfiguration(durchschnitt_als_fallback=False))

    assert (a.jahr, a.kw) == (2026, 31)
    # Krank: Berg 2 volle Tage (16 h) + Alt Teiltag (8 - 3 = 5 h)
    assert a.stunden("Krank") == 21.0
    assert a.tage("Krank") == pytest.approx(2 + 5 / 8, abs=0.01)
    # Urlaub: Cerny Mo/Di/Mi
    assert a.stunden("Urlaub") == 24.0
    assert a.tage("Urlaub") == 3.0
    # Feiertag: alle vier am Donnerstag
    assert a.stunden("Feiertag") == 32.0
    assert a.tage("Feiertag") == 4.0
    assert a.stunden("Arbeitsunfall") == 8.0
    assert a.stunden("Urlaub unbezahlt") == 8.0


def test_nicht_gewertete_codes_bleiben_aussen_vor(tmp_path):
    dateien, _ = tagesdateien_lesen([woche_anlegen(tmp_path)])
    a = woche_auswerten(dateien, Konfiguration())

    gewertet = {z.code for z in a.abwesenheiten}
    assert "EX" not in gewertet and "FU" not in gewertet and "A" not in gewertet
    # im Codeblatt tauchen sie trotzdem auf
    codes = {c.code: c for c in a.codes}
    assert codes["EX"].kategorie == "- nicht gewertet -"
    assert codes["FU"].tage == 1


def test_teiltag_zieht_iststunden_ab(tmp_path):
    awl_datei_schreiben(
        tmp_path / "tag.xlsx", MONTAG,
        [("100", "Alt, Anna", "H100", "AK", 5.5)],
    )
    dateien, _ = tagesdateien_lesen([tmp_path])
    a = woche_auswerten(dateien, Konfiguration(standard_sollstunden=8.0))

    zeile = a.abwesenheiten[0]
    assert zeile.teiltag is True
    assert zeile.abwesenheitsstunden == 2.5
    assert zeile.tage == pytest.approx(2.5 / 8)


def test_teiltag_wird_nie_negativ(tmp_path):
    awl_datei_schreiben(
        tmp_path / "tag.xlsx", MONTAG,
        [("100", "Alt, Anna", "H100", "AK", 11.0)],
    )
    dateien, _ = tagesdateien_lesen([tmp_path])
    a = woche_auswerten(dateien, Konfiguration(standard_sollstunden=8.0))
    assert a.abwesenheiten[0].abwesenheitsstunden == 0.0


def test_sollstunden_rangfolge_konfiguration(tmp_path):
    dateien, _ = tagesdateien_lesen([woche_anlegen(tmp_path)])
    konfig = Konfiguration(sollstunden_je_mitarbeiter={"200": 6.0},
                           durchschnitt_als_fallback=False)
    a = woche_auswerten(dateien, konfig)

    berg = [z for z in a.abwesenheiten if z.p_id == "200" and z.code == "K2"]
    assert all(z.sollstunden == 6.0 for z in berg)
    assert all(z.sollstunden_quelle == QUELLE_KONFIG for z in berg)
    assert a.stunden("Krank") == pytest.approx(6.0 * 2 + 5.0)


def test_sollstunden_rangfolge_durchschnitt(tmp_path):
    """Cerny arbeitet nur am Freitag 6 h -> Urlaub wird mit 6 h bewertet."""
    dateien, _ = tagesdateien_lesen([woche_anlegen(tmp_path)])
    a = woche_auswerten(dateien, Konfiguration(durchschnitt_als_fallback=True))

    urlaub = [z for z in a.abwesenheiten if z.p_id == "300"]
    assert all(z.sollstunden == 6.0 for z in urlaub)
    assert all(z.sollstunden_quelle == QUELLE_DURCHSCHNITT for z in urlaub)
    assert a.stunden("Urlaub") == 18.0


def test_durchschnitt_gilt_auch_fuer_teiltage(tmp_path):
    """Alt arbeitet Mo/Di/Fr 8+7+8 h -> Soll 7,67 h, Teiltag 7,67 - 3 h."""
    dateien, _ = tagesdateien_lesen([woche_anlegen(tmp_path)])
    a = woche_auswerten(dateien, Konfiguration(durchschnitt_als_fallback=True))

    teiltag = next(z for z in a.abwesenheiten if z.code == "AK")
    assert teiltag.sollstunden == pytest.approx(23 / 3, abs=1e-4)
    assert teiltag.sollstunden_quelle == QUELLE_DURCHSCHNITT
    # Krank = Berg 2 x 8 h (Ø seines einen Arbeitstages) + Alt 7,67 - 3 h
    assert a.stunden("Krank") == pytest.approx(16 + 23 / 3 - 3, abs=0.01)


def test_sollstunden_rangfolge_standard(tmp_path):
    dateien, _ = tagesdateien_lesen([woche_anlegen(tmp_path)])
    a = woche_auswerten(
        dateien, Konfiguration(standard_sollstunden=7.5,
                               durchschnitt_als_fallback=False)
    )
    urlaub = [z for z in a.abwesenheiten if z.p_id == "300"]
    assert all(z.sollstunden == 7.5 for z in urlaub)
    assert all(z.sollstunden_quelle == QUELLE_STANDARD for z in urlaub)


def test_gemischte_wochen_werden_getrennt(tmp_path):
    awl_datei_schreiben(
        tmp_path / "a.xlsx", MONTAG,
        [("100", "Alt, Anna", "H100", "K2", 0.0)],
    )
    awl_datei_schreiben(
        tmp_path / "b.xlsx", MONTAG + dt.timedelta(days=7),
        [("100", "Alt, Anna", "H100", "U2", 0.0)],
    )
    dateien, _ = tagesdateien_lesen([tmp_path])
    gruppen = nach_kalenderwochen_gruppieren(dateien)

    assert sorted(gruppen) == [(2026, 31), (2026, 32)]
    with pytest.raises(ValueError, match="Kalenderwoche"):
        woche_auswerten(dateien, Konfiguration())


def test_mitarbeiterzeilen(tmp_path):
    dateien, _ = tagesdateien_lesen([woche_anlegen(tmp_path)])
    a = woche_auswerten(dateien, Konfiguration())

    alt = next(m for m in a.mitarbeiter if m.p_id == "100")
    assert alt.arbeitstage == 3           # Mo, Di, Fr (AK zählt nicht als A)
    assert alt.gearbeitete_stunden == 23.0
    assert len(a.mitarbeiter) == 4


# ------------------------------------------------------- Konfiguration ---

def test_konfiguration_aus_json(tmp_path):
    pfad = tmp_path / "k.json"
    pfad.write_text(json.dumps({
        "_kommentar": "wird ignoriert",
        "standard_sollstunden": 7.0,
        "kategorien": {"K2": "Krank"},
        "sollstunden_je_mitarbeiter": {"_beispiel": 9.0, "100": 4.0},
    }), encoding="utf-8")

    konfig = Konfiguration.laden(pfad)
    assert konfig.standard_sollstunden == 7.0
    assert konfig.kategorie("U2") is None
    assert konfig.sollstunden_override("100") == 4.0
    assert konfig.sollstunden_override("_beispiel") is None


def test_konfiguration_meldet_unbekannten_schluessel(tmp_path):
    pfad = tmp_path / "k.json"
    pfad.write_text(json.dumps({"sollstunde": 8}), encoding="utf-8")
    with pytest.raises(ValueError, match="Unbekannte Schlüssel"):
        Konfiguration.laden(pfad)


def test_konfiguration_meldet_ungueltige_stunden(tmp_path):
    pfad = tmp_path / "k.json"
    pfad.write_text(json.dumps({"standard_sollstunden": 0}), encoding="utf-8")
    with pytest.raises(ValueError, match="standard_sollstunden"):
        Konfiguration.laden(pfad)


# ------------------------------------------------------------- Bericht ---

def test_bericht_aufbau_und_werte(tmp_path):
    dateien, _ = tagesdateien_lesen([woche_anlegen(tmp_path)])
    a = woche_auswerten(dateien, Konfiguration(durchschnitt_als_fallback=False))
    ziel = bericht_schreiben(a, tmp_path / "bericht.xlsx")

    mappe = load_workbook(ziel)
    assert mappe.sheetnames[0] == "Übersicht"
    assert set(mappe.sheetnames) == {
        "Übersicht", "Je Mitarbeiter", "Details", "Alle Codes", "Konfiguration",
    }

    details = mappe["Details"]
    # eine Zeile je gewerteter Abwesenheit
    assert details.max_row >= len(a.abwesenheiten) + 1
    assert details.cell(1, 15).value == "Abwesenheitsstunden"
    # Stunden sind Formeln, keine festen Zahlen
    assert str(details.cell(2, 15).value).startswith("=")
    assert str(details.cell(2, 16).value).startswith("=")

    uebersicht = mappe["Übersicht"]
    kategorien = [uebersicht.cell(r, 1).value for r in range(1, 30)]
    assert "Krank" in kategorien and "Feiertag" in kategorien


def test_bericht_ohne_abwesenheiten(tmp_path):
    awl_datei_schreiben(
        tmp_path / "tag.xlsx", MONTAG,
        [("100", "Alt, Anna", "H100", "A", 8.0)],
    )
    dateien, _ = tagesdateien_lesen([tmp_path])
    a = woche_auswerten(dateien, Konfiguration())
    ziel = bericht_schreiben(a, tmp_path / "leer.xlsx")

    assert ziel.exists()
    assert a.abwesenheiten == []


# ----------------------------------------------------------------- CLI ---

def test_cli_schreibt_je_kw_einen_bericht(tmp_path, capsys):
    quellen = tmp_path / "quellen"
    woche_anlegen(quellen)
    awl_datei_schreiben(
        quellen / "naechste.xlsx", MONTAG + dt.timedelta(days=7),
        [("100", "Alt, Anna", "H100", "U2", 0.0)],
    )
    ziel = tmp_path / "ziel"

    assert main([str(quellen), "-z", str(ziel)]) == 0

    erzeugt = sorted(p.name for p in ziel.glob("*.xlsx"))
    assert erzeugt == [
        "AWL_Auswertung_2100_KW31_2026.xlsx",
        "AWL_Auswertung_2100_KW32_2026.xlsx",
    ]
    ausgabe = capsys.readouterr().out
    assert "KW 31/2026" in ausgabe and "Krank" in ausgabe


def test_cli_filtert_kalenderwoche(tmp_path):
    quellen = tmp_path / "quellen"
    woche_anlegen(quellen)
    awl_datei_schreiben(
        quellen / "naechste.xlsx", MONTAG + dt.timedelta(days=7),
        [("100", "Alt, Anna", "H100", "U2", 0.0)],
    )
    ziel = tmp_path / "ziel"

    assert main([str(quellen), "-z", str(ziel), "--kw", "32",
                 "--jahr", "2026"]) == 0
    assert [p.name for p in ziel.glob("*.xlsx")] == [
        "AWL_Auswertung_2100_KW32_2026.xlsx"
    ]


def test_cli_meldet_leere_kalenderwoche(tmp_path, capsys):
    quellen = tmp_path / "quellen"
    woche_anlegen(quellen)
    assert main([str(quellen), "-z", str(tmp_path), "--kw", "5"]) == 1
    assert "KW 5" in capsys.readouterr().err


def test_cli_meldet_fehlenden_pfad(tmp_path, capsys):
    assert main([str(tmp_path / "gibtsnicht")]) == 2
    assert "nicht gefunden" in capsys.readouterr().err
