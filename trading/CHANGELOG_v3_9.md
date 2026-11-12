# RP Struktur & Zonen – Hotfix v3.9

Stand: 12.11.2026 · Phase 0 des Umbaus nach Blueprint 701

## Was geändert wurde

| Nr. | Stelle im Skript | Vorher (v3.8) | Nachher (v3.9) |
|---|---|---|---|
| 1 | `f_trend` (Bias Daily / 4H / 1H) | Gegenbruch = Schluss unter dem letzten Zwischentief (Pivot 5/5). Jeder tiefere Rücksetzer setzte den Bias auf „laufende Wende“ = KEIN TRADE. | Gegenbruch nur unter dem **geschützten Tief** (Ursprung des letzten Impulses = Fib 1). Bei jedem BOS wandert das geschützte Tief auf das Rücksetzer-Tief. Bestätigungslogik HH+HL unverändert. |
| 2 | `f_htfZone` (1H-Suchzone, ADX) | Zonen-Trend kippte bei jedem 1H-Schluss unter ein Zwischentief sofort auf Short, die Long-Fib-Zone verschwand. | Kippt erst bei Schluss unter Fib 1 (`ll`) bzw. über Fib 1 (`lh`). |
| 3 | Chart-Struktur ab 15M | CHoCH am letzten Swing, dadurch Fib-Wechsel im Rücksetzer. | CHoCH nur gegen geschütztes Hoch/Tief. Im 1–5M-Entry-Chart bleibt der frühe CHoCH am letzten Swing erhalten (gewollt). |
| 4 | Dashboard „Kipp“-Zeilen | Zeigten das letzte Zwischentief. | Zeigen das geschützte Tief/Hoch. |

Neue Eingaben (beide standardmäßig an):

- **Trend-Bias → „Bias & 1H-Zone: Wende nur unter Fib 1“** – aus = Verhalten v3.8, für A/B-Vergleich.
- **Marktstruktur → „Chart ab 15M: CHoCH nur gegen geschütztes Hoch/Tief“**.

Nicht geändert: Confluence, Qualität, Supply & Demand, FVG, Muster, CVD, Statistik, Journal, Alarme.

## Einstellungen für den Test (3M-Chart)

| Einstellung | Wert |
|---|---|
| Fibonacci des letzten Impulses | an |
| Virtuelle Trade-Statistik im Dashboard | an |
| Kipp-Level im Dashboard | an |
| 15M-Zonen zusätzlich | an |
| Mindest-Setup-Qualität | C |
| Filter-Details anzeigen | an |
| Alles andere | Standard |

## Abnahme Phase 0

1. v3.9 als neues Skript im Pine-Editor speichern, v3.8 parallel behalten.
2. Beide auf demselben 3M-Chart (Gold) laden, Dashboard-Positionen unterschiedlich wählen.
3. Vergleich über 2–3 Handelstage: Zeile „Bias Daily · 4H · 1H“ und „Offene Filter“.
   - Erwartung v3.9: Bias bleibt im Rücksetzer stehen, „Offene Filter“ zeigt Fenster/Impuls/Zone statt „Bias/Struktur“.
   - Erwartung Statistik: v3.9 zählt deutlich mehr virtuelle Trades als v3.8.
4. Replay-Prüfung nach der Anleitung (5 Fälle) mit v3.9 wiederholen.
5. Kompilierfehler bitte mit Zeilennummer und Meldung zurückmelden.

## Risiken

- 🟡 Trendwenden im Bias werden später erkannt (erst unter Fib 1). Gewollt, da der Blueprint den SL genau dort setzt.
- 🟡 Skript wurde ohne TradingView-Compiler geändert. Syntax wurde geprüft, ein Kompilierlauf steht aus.
- 🟢 Rechenkerne (Zonen, Confluence, Statistik) unverändert.
