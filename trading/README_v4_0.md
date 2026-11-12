# RP Struktur & Zonen v4.0.1 – Blueprint 701 als Setup-Lebenszyklus

Stand: 12.11.2026 · Phase 1 (Kern) · Datei `RP_Struktur_Zonen_v4_0.pine`

**v4.0.1:** Eine laufende Wende (↓? / ↑?) im Daily zählt als Richtung, sobald der 4H sie bestätigt hat, im 4H entsprechend mit dem 1H. Neue Eingabe „Laufende Wende zählt, wenn der nächsttiefere Zeitrahmen sie bestätigt“ (Standard an). Grund: Im Live-Test blockierte ein Daily „↓?“ bei bestätigtem 4H ↓ und 1H ↓ jedes Setup.

## Was v4 anders macht als v3.x

| Thema | v3.8 / v3.9 | v4.0 |
|---|---|---|
| Struktur | drei verschiedene Trendlogiken (Bias, 1H-Zone, Chart) | **eine Funktion** `f_struct` für Daily, 4H, 1H und Chart; Gegenbruch nur am Impulsursprung (Fib 1) |
| Bias | Daily, 4H, 1H müssen gleich sein; 1H-Rücksetzer = KEIN TRADE | **Daily + 4H** bestimmen die Richtung, 1H ist Kontext. Nur eine **bestätigte** 1H-Gegenwende blockiert |
| Suchzone | Fib-Zone des 1H aus eigener Logik | Fib 0,5–1 direkt aus dem 1H-Impuls derselben Strukturfunktion, plus Demand/Supply als Objekte |
| Confluence | am Fib-Band des 3M-Impulses (im Entry-Chart übersprungen) | **an der 1H-Suchzone** gemessen (Blueprint Punkt 3 + 4), im Zonen-Chart am Chart-Impuls |
| Setup | eine Zeile mit 14 Und-Bedingungen | **Lebenszyklus** 0 KEIN SETUP → 1 WARTEN → 2 KONTAKT → 3 BESTÄTIGT → 4 BEREIT → 5 AKTIV → 6 BEENDET, jeder Rückfall mit Grund |
| Dashboard | Filterliste | **Checkliste des Skills „setup-check-701“**, 8 Zeilen mit ✅/❌, dazu Phase, Status, Qualität, Limits, Statistik |
| Limits | Tageslimit nach Anzahl Verluste | **Tageslimit −2 R, Wochenlimit −5 R** (Blueprint) |
| Alarme | Freitext | festes Feldformat `RP4 \| Markt \| TF \| Phase … \| Entry \| SL \| TP \| CRV \| Q \| Conf \| Session` |

Übernommen und unverändert: Supply-&-Demand-Methode, Liquiditätsabgriffe, Umkehrmuster, CVD-Divergenz, FVG, Key Levels, Handelsfenster, News-Sperre, virtuelle Statistik, Journal.

## Dashboard ↔ Checkliste

| Zeile | Blueprint-Punkt | Grün wenn |
|---|---|---|
| 1 Bias | Bias Daily/4H/1H einheitlich | Daily + 4H bestätigt gleich, keine bestätigte 1H-Gegenwende |
| 2 Struktur Chart | Struktur Chart „passt“ | Chart-Struktur in Bias-Richtung |
| 3 Zone im Trendkontext | Zone markiert (Fib 0,5–1, Demand/Supply) | 1H-Fib-Zone in Bias-Richtung und/oder frische Demand/Supply vorhanden |
| 4 Zwei Faktoren | mindestens zwei Faktoren überschneiden sich | Fib + mindestens „Mindest-Faktoren“ weitere (Demand/Supply, PDH/PDL, Asia, VWAP, FVG) |
| 5 Preis in / nahe Zone | Preis in oder nahe der Zone | Entry-Chart: Kontakt innerhalb der letzten N Kerzen. Zonen-Chart: Kurs im Fib-Band |
| 6 CHoCH 1–5M | Strukturwechsel in Bias-Richtung | Phase ≥ 3, CHoCH (oder BOS-Folgeimpuls) aus der Suchzone heraus |
| 7 Handelsfenster · News | Fenster aktiv, keine News-Sperre | London 09–11 / New York 14:30–17:00, keine Sperre |
| 8 Entry · SL · TP · CRV | SL/TP definiert, CRV ≥ 1:3 | Plan aus dem CHoCH-Impuls, CRV erreicht |

Ein Screenshot des Dashboards kann direkt in den Skill „setup-check-701“ gegeben werden.

## Phasenlogik (Kurzfassung)

- **0 KEIN SETUP**: kein Bias, 1H-Gegenwende bestätigt, keine Suchzone oder Struktur gegen das Setup gekippt. Grund steht in „Status“.
- **1 WARTEN**: Bias und Suchzone vorhanden, Kurs noch nicht in der Zone.
- **2 KONTAKT**: Kurs hat die Suchzone berührt, Kontakt gilt N Kerzen (Standard 40).
- **3 BESTÄTIGT**: CHoCH im Entry-Chart in Bias-Richtung, Impulsursprung in der Zone. Fib des Impulses wird gezeichnet.
- **4 BEREIT**: Impulsextrem per Pivot bestätigt, alle Filter grün, Alarm „Setup bereit“ mit Plan. Verfällt nach N Kerzen ohne Entry.
- **5 AKTIV**: Entry 0,71 getroffen (virtuell), läuft bis TP oder SL. Konservativ: SL in derselben Kerze zählt als Verlust.
- **6 BEENDET**: Ergebnis in Statistik, Journal, Tages- und Wochen-R. Nächste Kerze zurück nach 1/2.

Ein BOS-Folgeimpuls in Zonennähe startet Phase 3 erneut (wie in v3.x), damit die Statistiken vergleichbar bleiben.

## Einstellungen für den Test

Standardwerte lassen. Für den Vergleich mit v3.9 auf demselben 3M-Chart: „Filter-Details anzeigen“ ist in v4 standardmäßig an, Dashboard-Position von v3.9 auf „Oben links“ stellen.

## Abnahme Phase 1

| Nr. | Prüfung | Erwartung |
|---|---|---|
| 1 | Skript kompiliert | keine Fehlermeldung. Falls doch: Zeile + Meldung zurückmelden |
| 2 | Zeile 1 im Rücksetzer | Bias bleibt LONG/SHORT, auch wenn der 1H „↓?“ zeigt |
| 3 | Zeile 3 + 5 | Fib-Zone des 1H wird im 3M als oranges Band gezeichnet, Zeile 5 springt bei Berührung auf „in der Suchzone“ |
| 4 | Phase | wechselt sichtbar 1 → 2 → 3 → 4 → 5 → 6, Status nennt bei Rückfall den Grund |
| 5 | Alarm „Setup bereit“ | enthält Entry, SL, TP, CRV, Qualität, Confluence, Session |
| 6 | Statistik nach 1 Woche | v4 zählt mindestens so viele virtuelle Trades wie v3.9, Trefferquote vergleichbar oder besser |

## Bekannte Grenzen (Phase 1)

- 🟡 Ohne TradingView-Compiler geschrieben. Syntax geprüft, Kompilierlauf steht aus.
- 🟡 Setup-Typ „15M-Limit“ (Limit an der 15M-Zone ohne 1–5M-Bestätigung) ist vorbereitet, aber erst Phase 2.
- 🟡 Positionsgröße in Lots, Korrelationshinweis und Journal-Export kommen in Phase 2/3.
- 🟢 Kein Repainting: höhere Zeitrahmen über abgeschlossene Kerzen, Phasenwechsel auf Kerzenbasis.

## Nächste Schritte

| Nr. | Aktion | Verantwortlich | Fällig |
|---|---|---|---|
| 1 | v3.9 und v4.0 in TradingView kompilieren, Fehler zurückmelden | Du | 13.11. |
| 2 | Beide eine Woche parallel auf Gold 3M laufen lassen, Statistik-Screenshots sammeln | Du | 20.11. |
| 3 | Phase 2: 15M-Limit, Risiko-Modul mit Lots, Limits | Ich | nach Freigabe |
| 4 | Phase 3: AMD-Kontext, Journal-Export für den Wochenreview | Ich | nach Phase 2 |
