# AWL-Auswertung: Kranken-, Urlaubs- und Feiertagsstunden je Kalenderwoche

Wertet die täglichen AWL-Dateien (Tabellenblatt **AWL**) einer Kalenderwoche
aus und schreibt Kranken-, Urlaubs- und Feiertagsstunden als Excel-Bericht.

Die Tagesdateien werden dabei **nur gelesen und nie verändert**.

> **Zum ersten Einrichten und für den wöchentlichen Ablauf:
> [ANLEITUNG.md](ANLEITUNG.md)** — Schritt für Schritt, von der
> Python-Installation bis zum fertigen Bericht. Unter Windows genügt danach
> ein Doppelklick auf `Auswertung_starten.bat`.

---

## Schnellstart

```bash
pip install -r requirements.txt

# alle Tagesdateien eines Ordners auswerten
python -m awl_auswertung ./KW31 -k konfiguration.json
```

Ergebnis im aktuellen Ordner, z. B.
`AWL_Auswertung_2100_KW31_2026.xlsx`, und auf der Konsole:

```
KW 31/2026  (27.07.2026 – 31.07.2026, 5 Tagesdatei(en))
    Krank                    64.00 Std.     8.00 Tage
    Urlaub                   96.00 Std.    12.00 Tage
    Feiertag                256.00 Std.    32.00 Tage
```

### Weitere Aufrufe

```bash
# einzelne Dateien statt eines Ordners, eigener Zielordner
python -m awl_auswertung Mo.xlsm Di.xlsm Mi.xlsm -z ./Auswertungen

# Ordner mit mehreren Wochen: erzeugt je Kalenderwoche einen Bericht
python -m awl_auswertung ./AWL-Archiv

# daraus nur eine bestimmte Woche
python -m awl_auswertung ./AWL-Archiv --kw 31 --jahr 2026
```

| Option | Bedeutung |
|---|---|
| `-z`, `--ziel` | Zielordner für die Berichte (Standard: aktueller Ordner) |
| `-k`, `--konfiguration` | JSON-Datei mit Sollstunden und Kategorien |
| `--kw`, `--jahr` | nur diese Kalenderwoche auswerten |
| `-q`, `--still` | keine Konsolenausgabe |

Liegen für einen Tag **mehrere Dateien** vor (z. B. eine Korrekturfassung),
wird automatisch die zuletzt geänderte verwendet und im Bericht vermerkt.
Excel-Sperrdateien (`~$…`) werden übersprungen.

---

## Wie die Stunden ermittelt werden

### Was in der AWL steht

| AWL-Zelle | Inhalt |
|---|---|
| `D6` | Datum der Tagesdatei → daraus die Kalenderwoche (ISO 8601) |
| `G1` / `J1` / `N1` | Projekt / Kostenstelle / Vertragsart |
| Zeilen 11–359 | eine Zeile je Mitarbeiter |
| Spalte `C` / `D` / `E` | P-Id / Name / MA-Nr. |
| Spalte `H` | tatsächlich gearbeitete Stunden (dezimal) |
| Spalte `I` | Anwesenheitscode aus der Liste `AWL!DD9:DE30` |

### Wichtige Einschränkung der Datenquelle

**Die AWL enthält keine Sollstunden.** An Abwesenheitstagen steht in Spalte `H`
immer `0`. Die AWL sagt also *dass* jemand krank war oder Urlaub hatte, aber
nicht, *wie viele Stunden* dafür anzusetzen sind.

Die Abwesenheitsstunden sind deshalb eine **Annahme** dieser Auswertung. Sie
wird in dieser Rangfolge gebildet:

1. **Konfiguration** – ein für die P-Id hinterlegter Wert in
   `sollstunden_je_mitarbeiter`.
2. **Ø der KW** – der Durchschnitt der Stunden, die derselbe Mitarbeiter in
   derselben Kalenderwoche tatsächlich gearbeitet hat (Code `A` oder `AS`).
   Abschaltbar über `durchschnitt_als_fallback`.
3. **Standardwert** – `standard_sollstunden` (Vorgabe 8,0 h).

Welche Stufe je Zeile gegriffen hat, steht im Bericht in der Spalte
**„Quelle Sollstunden“**. Sind die tatsächlichen Sollstunden je Mitarbeiter
bekannt, gehören sie in Stufe 1 — dann sind die Zahlen exakt statt geschätzt.

### Kategorien

Standardzuordnung der Anwesenheitscodes (änderbar in `konfiguration.json`):

| Kategorie | Codes |
|---|---|
| Krank | `K2` (Krank), `AK` (Arbeit und Krank), `AKAS` |
| Urlaub | `U2` (bezahlter Urlaub) |
| Feiertag | `Ft` |
| Arbeitsunfall | `KA` |
| Urlaub unbezahlt | `UU` |

Alle übrigen Codes (`A`, `AS`, `EX`, `FU`, `FA`, `MS`, …) gelten **nicht** als
Abwesenheit im Sinne dieser Auswertung. Sie verschwinden aber nicht still:
das Blatt **„Alle Codes“** listet jeden in der Woche vorgekommenen Code mit
Anzahl und Zuordnung, sodass sichtbar bleibt, was gewertet wurde und was nicht.

### Teiltage

Bei `AK` / `AKAS` hat der Mitarbeiter einen Teil des Tages gearbeitet:

```
Abwesenheitsstunden = Sollstunden − bereits erfasste Iststunden   (nie < 0)
```

---

## Der erzeugte Bericht

| Blatt | Inhalt |
|---|---|
| **Übersicht** | Kopfdaten, Summe je Kategorie, Matrix Kategorie × Tag, Grundlagen, ausgewertete Dateien |
| **Je Mitarbeiter** | eine Zeile je Mitarbeiter mit Stunden und Tagen je Kategorie |
| **Details** | eine Zeile je Abwesenheit — die Rohdaten der Auswertung |
| **Alle Codes** | jeder vorgekommene Anwesenheitscode mit Zuordnung |
| **Konfiguration** | die verwendeten Einstellungen und alle Annahmen |

Der Bericht rechnet **live**: Übersicht und Mitarbeiterblatt greifen per
`SUMIF`/`SUMIFS` auf das Blatt „Details“ zu. Die **gelb hinterlegte Spalte
„Sollstunden/Tag“** im Blatt „Details“ ist die einzige Eingabegröße — wird ein
Wert dort geändert, rechnen alle Summen sofort neu. So lassen sich Einzelfälle
korrigieren, ohne die Konfiguration anzufassen.

---

## Konfiguration

`konfiguration.json` (Schlüssel mit führendem `_` sind Kommentare):

```json
{
  "standard_sollstunden": 8.0,
  "durchschnitt_als_fallback": true,
  "sollstunden_je_mitarbeiter": {
    "29910": 7.5
  },
  "kategorien": {
    "K2": "Krank",
    "U2": "Urlaub",
    "Ft": "Feiertag"
  },
  "teiltag_codes": ["AK", "AKAS"]
}
```

Der Schlüssel in `sollstunden_je_mitarbeiter` ist die **P-Id aus Spalte C der
AWL**, als Text in Anführungszeichen.

Ohne `-k` gelten die Standardwerte aus `awl_auswertung/konfig.py`.

---

## Tests

```bash
python -m pytest tests -q
```

Die Tests erzeugen AWL-Dateien im Aufbau der echten Tagesdatei (inklusive der
leeren Vorratszeilen, die dort als `", "` und `#N/A` auftauchen) und prüfen
Einlesen, Sollstunden-Rangfolge, Teiltagsrechnung, Korrekturdateien,
Wochentrennung sowie den erzeugten Bericht.

---

## Aufbau

```
awl_auswertung/
  einlesen.py    AWL-Tagesdateien lesen, Dubletten je Datum auflösen
  konfig.py      Codeliste, Kategorien, Sollstunden-Einstellungen
  auswertung.py  Aggregation einer Kalenderwoche
  bericht.py     Excel-Ausgabe
  cli.py         Kommandozeile
konfiguration.json
tests/
```
