# Schritt-für-Schritt-Anleitung

Ermittlung der Kranken-, Urlaubs- und Feiertagsstunden einer Kalenderwoche
aus den täglichen AWL-Dateien.

Die Anleitung ist für Windows geschrieben. Unter macOS/Linux sind die
Befehle identisch, nur die Pfade sehen anders aus.

---

## Teil A — Einrichtung (nur einmal nötig)

### Schritt 1: Python installieren

1. <https://www.python.org/downloads/> öffnen und den gelben Knopf
   **„Download Python"** anklicken.
2. Die heruntergeladene Datei starten.
3. **Wichtig:** Im ersten Fenster unten das Häkchen bei
   **„Add python.exe to PATH"** setzen — sonst findet Windows Python später
   nicht.
4. Auf **„Install Now"** klicken und den Assistenten durchlaufen lassen.

Prüfen, ob es geklappt hat: Windows-Taste drücken, `cmd` eingeben, Enter.
Im schwarzen Fenster tippen:

```
python --version
```

Es muss eine Versionsnummer erscheinen, z. B. `Python 3.12.4`. Kommt
stattdessen eine Fehlermeldung, war das Häkchen aus Punkt 3 nicht gesetzt —
Python noch einmal installieren.

### Schritt 2: Das Projekt auf den Rechner holen

Das Projekt liegt im Git-Repository `ahmettapkan/Ahmet` im Zweig
`claude/automation-sick-vacation-holidays-p0x2nw`.

**Ohne Git-Kenntnisse:** Auf GitHub den Zweig auswählen, dann
**Code → Download ZIP**, und die ZIP-Datei entpacken, z. B. nach:

```
C:\AWL-Auswertung
```

**Mit Git:**

```
git clone https://github.com/ahmettapkan/Ahmet.git C:\AWL-Auswertung
cd C:\AWL-Auswertung
git checkout claude/automation-sick-vacation-holidays-p0x2nw
```

In diesem Ordner müssen anschließend liegen: der Ordner `awl_auswertung`,
die Datei `konfiguration.json` und die Datei `requirements.txt`.

### Schritt 3: Die benötigte Bibliothek installieren

Eingabeaufforderung öffnen und eingeben:

```
cd C:\AWL-Auswertung
pip install -r requirements.txt
```

Am Ende erscheint `Successfully installed openpyxl-…`. Damit ist die
Einrichtung abgeschlossen.

---

## Teil B — Der wöchentliche Ablauf

### Schritt 4: Einen Ordner für die Woche anlegen

Legen Sie je Kalenderwoche einen Ordner an und kopieren Sie **alle
Tagesdateien dieser Woche** hinein — die Originale, unverändert:

```
C:\AWL-Auswertung\Wochen\KW31
    2100_TEDi_Kamen_AWL_27.07.2026.xlsm
    2100_TEDi_Kamen_AWL_28.07.2026.xlsm
    2100_TEDi_Kamen_AWL_29.07.2026.xlsm
    2100_TEDi_Kamen_AWL_30.07.2026.xlsm
    2100_TEDi_Kamen_AWL_31.07.2026.xlsm
```

Hinweise dazu:

- **Die Dateinamen sind egal.** Das Datum wird aus der Zelle `D6` des
  Blattes „AWL" gelesen, nicht aus dem Namen.
- **Korrekturfassungen dürfen mit im Ordner liegen.** Gibt es zu einem Tag
  mehrere Dateien, wird automatisch die zuletzt geänderte genommen und im
  Bericht vermerkt.
- **Ihre Dateien werden nur gelesen, nie verändert.**
- Es dürfen auch mehrere Wochen in einem Ordner liegen — dann entsteht je
  Kalenderwoche ein eigener Bericht.

### Schritt 5: Die Auswertung starten

**Variante A — mit Doppelklick (am einfachsten)**

1. Im Ordner `C:\AWL-Auswertung` die Datei **`Auswertung_starten.bat`**
   doppelklicken.
2. Den Pfad des Wochenordners eingeben, z. B. `Wochen\KW31`, und Enter
   drücken.

Noch schneller: den Wochenordner mit der Maus auf
`Auswertung_starten.bat` **ziehen und fallen lassen** — dann entfällt die
Eingabe.

**Variante B — über die Eingabeaufforderung**

```
cd C:\AWL-Auswertung
python -m awl_auswertung Wochen\KW31 -k konfiguration.json -z Auswertungen
```

Zur Bedeutung: `Wochen\KW31` ist der Ordner mit den Tagesdateien,
`-k konfiguration.json` sind Ihre Einstellungen, `-z Auswertungen` ist der
Zielordner für das Ergebnis.

### Schritt 6: Das Ergebnis prüfen

Im Fenster erscheint sofort die Zusammenfassung:

```
KW 31/2026  (27.07.2026 – 31.07.2026, 5 Tagesdatei(en))
    Krank                   180.00 Std.    22.50 Tage
    Urlaub                  256.00 Std.    32.00 Tage
    Feiertag                 64.00 Std.     8.00 Tage
    -> Auswertungen\AWL_Auswertung_2100_KW31_2026.xlsx
```

Kontrollieren Sie hier zwei Dinge:

1. **Stimmt die Anzahl der Tagesdateien?** Bei einer vollen Woche müssen es
   5 sein (bzw. 6 mit Samstag). Steht dort weniger, fehlt eine Datei im
   Ordner.
2. **Stimmt der Zeitraum?** Wenn nicht, hat eine Datei ein falsches Datum in
   Zelle `D6`.

### Schritt 7: Den Bericht öffnen

Die erzeugte Datei liegt im Ordner `Auswertungen`, z. B.
`AWL_Auswertung_2100_KW31_2026.xlsx`. Sie enthält fünf Blätter:

| Blatt | Wofür |
|---|---|
| **Übersicht** | Ihr Ergebnis: Summe je Kategorie und die Matrix Kategorie × Tag |
| **Je Mitarbeiter** | Wer wie viele Kranken-, Urlaubs- und Feiertagsstunden hat |
| **Details** | Eine Zeile je Abwesenheit — hier lässt sich alles nachvollziehen |
| **Alle Codes** | Jeder vorgekommene Anwesenheitscode, auch die nicht gewerteten |
| **Konfiguration** | Welche Einstellungen und Annahmen gegolten haben |

**Empfohlene Kontrolle beim ersten Mal:** Schauen Sie ins Blatt
**„Alle Codes"**. Dort steht jeder Code, der in der Woche vorkam, mit seiner
Zuordnung. Alles, was grau als „– nicht gewertet –" erscheint, fließt nicht
in die Stunden ein. Wenn dort ein Code auftaucht, der Ihrer Meinung nach
mitzählen müsste, siehe Schritt 9.

---

## Teil C — Die Sollstunden (der wichtigste Punkt)

### Schritt 8: Sollstunden je Mitarbeiter hinterlegen

**Warum das nötig ist:** Ihre AWL erfasst nur *gearbeitete* Stunden. An
einem Kranken- oder Urlaubstag steht in Spalte `H` immer `0`. Die Datei sagt
also *dass* jemand krank war, aber nicht, *wie viele Stunden* dafür
anzusetzen sind. Diese Zahl muss von außen kommen.

Das Werkzeug geht in dieser Reihenfolge vor:

1. **Konfiguration** — der Wert, den Sie unten hinterlegen. *Der genaue Weg.*
2. **Ø der KW** — der Durchschnitt der Stunden, die derselbe Mitarbeiter in
   derselben Woche tatsächlich gearbeitet hat. *Eine Schätzung.*
3. **Standardwert** — 8,0 Stunden. *Die Notlösung.*

Im Blatt „Details" zeigt die Spalte **„Quelle Sollstunden"** je Zeile an,
welche Stufe gegriffen hat. Solange dort „Standardwert" oder „Ø der KW"
steht, sind die Zahlen geschätzt.

**So hinterlegen Sie die echten Werte:**

1. Die Datei `konfiguration.json` mit dem Editor öffnen (Rechtsklick →
   *Öffnen mit* → *Editor*).
2. Den Abschnitt `sollstunden_je_mitarbeiter` ergänzen. Der Schlüssel ist
   die **P-Id aus Spalte C der AWL**, in Anführungszeichen:

```json
  "sollstunden_je_mitarbeiter": {
    "29910": 8.0,
    "18849": 7.5,
    "29704": 6.0
  },
```

Achten Sie darauf: Kommas zwischen den Zeilen, **kein** Komma nach der
letzten, und Dezimaltrennzeichen ist der **Punkt** (`7.5`, nicht `7,5`).

3. Speichern und die Auswertung erneut starten.

Das ist einmalige Pflege. Neue Mitarbeiter ergänzen Sie später einfach in
derselben Liste.

**Einzelfall schnell korrigieren, ohne die Konfiguration anzufassen:** Im
erzeugten Bericht im Blatt „Details" die **gelbe Spalte
„Sollstunden/Tag"** überschreiben. Übersicht und Mitarbeiterblatt rechnen
sofort neu, weil sie per Formel darauf zugreifen.

### Schritt 9: Kategorien anpassen (nur falls nötig)

In `konfiguration.json` steht, welcher Anwesenheitscode zu welcher Kategorie
zählt. Voreingestellt ist:

| Kategorie | Codes |
|---|---|
| Krank | `K2`, `AK`, `AKAS` |
| Urlaub | `U2` |
| Feiertag | `Ft` |
| Arbeitsunfall | `KA` |
| Urlaub unbezahlt | `UU` |

Soll z. B. `KA` (Arbeitsunfall) mit unter „Krank" laufen, ändern Sie im
Abschnitt `kategorien` die Zeile:

```json
    "KA": "Krank",
```

Soll ein bisher nicht gewerteter Code mitzählen — etwa `FA`
(Freizeitausgleich) —, fügen Sie ihn dort hinzu:

```json
    "FA": "Freizeitausgleich",
```

und tragen die neue Kategorie zusätzlich in `kategorie_reihenfolge` ein.

---

## Wenn etwas nicht funktioniert

| Meldung / Beobachtung | Ursache und Lösung |
|---|---|
| `python wird nicht als Befehl erkannt` | Beim Installieren fehlte das Häkchen „Add python.exe to PATH". Python neu installieren (Schritt 1). Alternativ `py` statt `python` schreiben. |
| `No module named openpyxl` | Schritt 3 wurde übersprungen: `pip install -r requirements.txt` ausführen. |
| `No module named awl_auswertung` | Sie stehen im falschen Ordner. Erst `cd C:\AWL-Auswertung`, dann den Befehl. |
| `Tabellenblatt 'AWL' fehlt` | Die Datei ist keine AWL-Tagesdatei — z. B. eine Abrechnung, die versehentlich im Ordner liegt. |
| `In Zelle AWL!D6 steht kein gültiges Datum` | In der Tagesdatei fehlt das Datum oder es steht als Text statt als Datum darin. |
| `Es wurden keine AWL-Dateien gefunden` | Der Ordner ist leer oder der Pfad ist falsch geschrieben. |
| `Permission denied` beim Schreiben | Der Bericht ist noch in Excel geöffnet. Excel schließen und erneut starten. |
| Eine Kategorie zeigt 0 Stunden | In der Woche kam kein passender Code vor — im Blatt „Alle Codes" nachsehen. |
| Alle Sollstunden sind glatt 8,00 | Es sind noch keine echten Werte hinterlegt (Schritt 8). |

---

## Kurzfassung für den Wochenrhythmus

Nach der einmaligen Einrichtung bleiben pro Woche drei Handgriffe:

1. Tagesdateien der KW in einen Ordner kopieren.
2. Ordner auf `Auswertung_starten.bat` ziehen.
3. Bericht im Ordner `Auswertungen` öffnen.
