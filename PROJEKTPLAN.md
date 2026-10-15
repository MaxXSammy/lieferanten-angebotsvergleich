# 📋 Projektplan – Lieferanten-Angebotsvergleich

**Projekttag:** Freitag, 16.10.2026 · **Team:** Max & Jonas · **Zeit:** ca. 3–4 Std
**Thema:** Funktionen, Module & API-Anfragen

---

## 🎯 Ziel

Ein Python-Tool, das Lieferantenangebote aus einer CSV einliest, Fremdwährungen per **Wechselkurs-API** in Euro umrechnet, die Angebote **pro Artikel** nach mehreren Kriterien bewertet und eine Rangliste mit **KI-Empfehlung** ausgibt.

```
CSV  →  laden & prüfen  →  in EUR umrechnen (API)  →  bewerten  →  Rangliste + Diagramm  →  KI-Empfehlung (API)
```

---

## 📁 Projektstruktur

```
lieferanten-angebotsvergleich/
├── daten/
│   ├── angebote.csv              ← saubere Testdaten (170 Angebote, fiktiv)
│   └── angebote_fehlerhaft.csv   ← mit ~50 typischen Fehlern zum Testen
├── config.py                     ← Max
├── waehrung.py                   ← Max
├── bewertung.py                  ← Max
├── daten_laden.py                ← Jonas
├── bericht.py                    ← Jonas
├── ki_zusammenfassung.py         ← Jonas
├── main.py                       ← gemeinsam
├── requirements.txt              ← gemeinsam
├── .env.example                  ← gemeinsam (Vorlage, ohne echten Token!)
└── README.md                     ← gemeinsam
```

**Regel:** Jeder bearbeitet nur **seine eigenen Dateien**. So gibt es keine Git-Konflikte.

---

## 🔗 Die gemeinsame Schnittstelle (zuerst zusammen festlegen!)

Alle Module arbeiten mit einer **Liste von Dictionaries**. Jedes Modul ergänzt Felder:

```python
# nach daten_laden.py
{"angebots_id": "ANG-1001", "lieferant": "Morvenich Components s.r.o.", "land": "CZ",
 "artikelnr": "WG-10-001", "artikel": "Stahlwinkel 40x40x4 S235",
 "menge": 500, "einzelpreis": 56.87, "gesamtpreis": 28435.0, "waehrung": "CZK",
 "lieferzeit_tage": 12, "qualitaet": 2, "liefertreue_prozent": 94.5,
 "reklamationsquote_prozent": 2.15, ...}

# + nach waehrung.py
{..., "einzelpreis_eur": 2.26, "gesamtpreis_eur": 1131.71, "kurs": 0.0398}

# + nach bewertung.py
{..., "score": 0.83, "rang": 1}
```

⚠️ **Wichtig:** Verglichen wird immer nur **innerhalb desselben Artikels** (`artikelnr`) – Schrauben gegen Kartons zu vergleichen ergibt keinen Sinn.

---

## 👤 Max – Konfiguration, Währung & Bewertung

### `config.py`
Alle Einstellungen an einem Ort – kein anderer Code enthält feste Spaltennamen.

```python
DATEI = "daten/angebote.csv"
ZIELWAEHRUNG = "EUR"

KRITERIEN = {
    "einzelpreis_eur":           {"gewicht": 0.40, "besser": "niedrig"},
    "lieferzeit_tage":           {"gewicht": 0.20, "besser": "niedrig"},
    "qualitaet":                 {"gewicht": 0.20, "besser": "hoch"},
    "liefertreue_prozent":       {"gewicht": 0.10, "besser": "hoch"},
    "reklamationsquote_prozent": {"gewicht": 0.10, "besser": "niedrig"},
}

# Notfall-Kurse, falls die API nicht erreichbar ist
FALLBACK_KURSE = {"EUR": 1.0, "CZK": 0.0398, "PLN": 0.2336, "CHF": 1.064}
```

### `waehrung.py` – 🌐 API-Modul 1
| Funktion | Aufgabe |
|---|---|
| `hole_kurse(waehrungen)` | Fragt die Wechselkurs-API ab, gibt `{"CZK": 0.0398, ...}` zurück |
| `rechne_in_euro(angebote, kurse)` | Ergänzt `einzelpreis_eur`, `gesamtpreis_eur`, `kurs` |

**API:** Frankfurter API (EZB-Kurse, kostenlos, **kein Key nötig**) – Doku: https://frankfurter.dev
→ Vorher die URL im Browser testen und schauen, wie das JSON aussieht.

💡 **Hinweise:**
- `requests.get(url, params=..., timeout=10)` – an Timeout denken!
- Die API liefert Kurse *von* einer Währung *zu* anderen. Überlegt: Braucht ihr EUR→CZK oder CZK→EUR? (Tipp: `1 / kurs`)
- **Fehlerbehandlung:** Ist die API nicht erreichbar → `FALLBACK_KURSE` aus `config.py` nehmen und eine Warnung ausgeben. Das Programm darf **nie** abstürzen.
- Nur **einmal** pro Programmlauf abfragen, nicht für jede Zeile neu.

### `bewertung.py`
| Funktion | Aufgabe |
|---|---|
| `normalisiere(werte, besser)` | Skaliert eine Liste von Zahlen auf 0–1 (1 = am besten) |
| `bewerte(angebote, kriterien)` | Berechnet für jedes Angebot den `score` |
| `erstelle_rangliste(angebote, artikelnr)` | Filtert auf einen Artikel, sortiert nach Score, setzt `rang` |

💡 **Hinweise:**
- **Min-Max-Normalisierung:** `(wert - min) / (max - min)`. Bei `"besser": "niedrig"` umdrehen: `1 - ...`
- Sonderfall: Was passiert, wenn alle Werte gleich sind (`max - min == 0`)?
- Score = Summe aus `normalisierter_wert × gewicht` über alle Kriterien
- Normalisieren immer **pro Artikel**, nicht über die ganze Datei

---

## 👤 Jonas – Daten laden, Ausgabe & KI

### `daten_laden.py`
| Funktion | Aufgabe |
|---|---|
| `lade_angebote(pfad)` | Liest die CSV, gibt Liste von Dictionaries zurück |
| `pruefe_daten(angebote)` | Trennt in `(gueltige, fehlerhafte)` – mit Fehlergrund |

💡 **Hinweise:**
- `csv.DictReader` – an `encoding="utf-8"` denken (Umlaute!)
- Zahlen kommen als Text rein → mit `float()` / `int()` umwandeln, in `try/except`
- Mit `daten/angebote_fehlerhaft.csv` testen. Darin stecken u. a.: fehlende Werte, Dezimalkomma `3,58`, `€` im Preis, „ca. 2 Wochen" statt Zahl, negative Lieferzeit, Qualität 9, Liefertreue 140 %, Leerzeichen um Namen, doppelte Zeilen, uneinheitliche Währungen (`Euro`, `eur`, `Kč`)
- Ziel: Wie viele Fehler findet eure Prüfung? Ausgabe z. B. `152 gültig, 21 aussortiert`
- Optional reparieren statt aussortieren: `"3,58"` → `3.58`, `" Name "` → `"Name"`

### `bericht.py`
| Funktion | Aufgabe |
|---|---|
| `zeige_tabelle(rangliste)` | Gibt die Rangliste übersichtlich im Terminal aus |
| `zeige_diagramm(rangliste)` | Balkendiagramm der Scores (matplotlib) |
| `speichere_ergebnis(rangliste, pfad)` | *(optional)* als CSV/Excel speichern |

💡 **Hinweise:**
- Tabelle: f-Strings mit fester Breite, z. B. `f"{name:<35}{score:>6.2f}"`
- Diagramm: `plt.barh(...)` – liegende Balken sind bei langen Firmennamen besser lesbar
- Diagramm als PNG speichern (`plt.savefig`) → Screenshot fürs README!

### `ki_zusammenfassung.py` – 🌐 API-Modul 2
| Funktion | Aufgabe |
|---|---|
| `erstelle_prompt(rangliste)` | Baut aus den Top 3 einen kurzen Text für das Modell |
| `erstelle_empfehlung(rangliste)` | Schickt den Text an die KI-API, gibt die Empfehlung zurück |

💡 **Hinweise:**
- Den `HuggingFaceClient` aus Max' Projekt (Tag 7) wiederverwenden – Token liegt in der `.env`
- Achtung: Der kostenlose HF-Account hat kaum Credits → der Client hat einen **lokalen Fallback**
- **Fehlerbehandlung:** Klappt die KI nicht → einfache Text-Empfehlung ohne KI zurückgeben, z. B. *„Empfehlung: X (Score 0.83), günstigster Preis bei guter Qualität."* Das Programm läuft trotzdem durch.

---

## 🤝 Gemeinsam

### `main.py` – verbindet alles
```python
# 1. Daten laden & prüfen          → daten_laden
# 2. Kurse holen & umrechnen       → waehrung
# 3. Bewerten                      → bewertung
# 4. Artikel auswählen (input())   → z. B. alle Artikelnummern anzeigen
# 5. Rangliste + Diagramm          → bericht
# 6. KI-Empfehlung                 → ki_zusammenfassung
```

### `requirements.txt`
```
requests
python-dotenv
matplotlib
```

### `README.md` – für Recruiter!
- Was macht das Tool? (2–3 Sätze)
- Screenshot von Ausgabe + Diagramm
- Installation & Start
- Projektstruktur + wer was gebaut hat
- Hinweis: *Die Beispieldaten sind fiktiv.*

---

## ⏱️ Zeitplan

| Zeit | Was | Wer |
|---|---|---|
| 0:00 – 0:30 | Plan durchgehen, Schnittstelle bestätigen, leere Dateien anlegen & pushen | beide |
| 0:30 – 2:30 | Eigene Module bauen & einzeln testen | jeder für sich |
| 2:30 – 3:15 | `main.py` zusammenstecken, Fehler beheben | beide |
| 3:15 – 4:00 | README, Screenshots, letzter Push | beide |

**Wenn die Zeit knapp wird**, in dieser Reihenfolge weglassen: `speichere_ergebnis` → Diagramm → KI-Empfehlung. Der Kern (laden → umrechnen → bewerten → Rangliste) muss laufen.

---

## 🔀 Git-Workflow

```bash
git pull                                   # IMMER zuerst
# ... arbeiten ...
git add .
git commit -m "waehrung.py: Kurse per API abrufen"
git push
```

- Kleine, häufige Commits mit klarer Nachricht (`datei: was gemacht`)
- Vor jedem `push` ein `pull`
- **Nie die `.env` committen** – steht in der `.gitignore`

---

## ✅ Fertig, wenn …

- [ ] `python main.py` läuft ohne Absturz durch
- [ ] Fremdwährungen werden per API in EUR umgerechnet (mit Fallback ohne Internet)
- [ ] Fehlerhafte CSV wird erkannt, Programm läuft trotzdem
- [ ] Rangliste pro Artikel wird angezeigt
- [ ] KI-Empfehlung erscheint (oder Ersatztext)
- [ ] README mit Screenshot ist online
