"""Lädt Angebote aus einer CSV, repariert typische Formatfehler und prüft die Daten."""

import csv
from datetime import datetime

# Spalten, die Zahlen sein müssen
KOMMAZAHLEN = [
    "einzelpreis",
    "gesamtpreis",
    "liefertreue_prozent",
    "reklamationsquote_prozent",
]
GANZZAHLEN = [
    "menge",
    "mindestbestellmenge",
    "lieferzeit_tage",
    "qualitaet",
    "zahlungsziel_tage",
]

# Uneinheitliche Schreibweisen -> einheitlicher Wert
WAEHRUNGEN = {
    "EUR": "EUR",
    "EURO": "EUR",
    "€": "EUR",
    "CZK": "CZK",
    "KČ": "CZK",
    "PLN": "PLN",
    "ZŁ": "PLN",
    "CHF": "CHF",
}
EINHEITEN = {"STK": "Stk", "STÜCK": "Stk", "ST": "Stk", "M": "m", "ROLLE": "Rolle"}


def lade_angebote(pfad):
    """Liest die CSV und gibt eine Liste von Dictionaries zurück (alle Werte noch als Text)."""
    try:
        with open(pfad, encoding="utf-8") as datei:
            return list(csv.DictReader(datei))
    except FileNotFoundError:
        print(f"❌ Datei nicht gefunden: {pfad}")
        return []


# ---------- Hilfsfunktionen zum Reparieren ------------------------------- #
def _zu_zahl(text):
    """'1.240,50 €' / '3,58' / ' 12 ' -> float. Wirft ValueError bei Unsinn wie 'ca. 2 Wochen'."""
    text = str(text).replace("€", "").strip()
    if not text:
        raise ValueError("leer")
    if "," in text and "." in text:  # deutsches Format 1.240,50
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", ".")  # 3,58 -> 3.58
    return float(text)


def _zu_datum(text):
    """Akzeptiert 2026-07-15 und 15.07.2026, gibt immer ISO-Format zurück."""
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(text.strip(), fmt).date()
        except ValueError:
            pass
    raise ValueError(f"unbekanntes Datum '{text}'")


# ---------- Hauptprüfung -------------------------------------------------- #
def pruefe_daten(angebote):
    """Repariert, was sich reparieren lässt, und sortiert den Rest aus.

    Gibt (gueltige, fehlerhafte) zurück.
    fehlerhafte ist eine Liste von (angebot, [gründe]).
    """
    gueltige, fehlerhafte = [], []
    gesehene_ids = set()

    for roh in angebote:
        a = {k: (v.strip() if isinstance(v, str) else v) for k, v in roh.items()}
        gruende = []

        # Duplikate
        if a["angebots_id"] in gesehene_ids:
            fehlerhafte.append((a, ["doppelte Angebots-ID"]))
            continue
        gesehene_ids.add(a["angebots_id"])

        # Pflichtfeld
        if not a["lieferant"]:
            gruende.append("Lieferant fehlt")

        # Zahlen umwandeln
        for spalte in KOMMAZAHLEN + GANZZAHLEN:
            try:
                zahl = _zu_zahl(a[spalte])
                a[spalte] = int(zahl) if spalte in GANZZAHLEN else zahl
            except ValueError:
                gruende.append(f"{spalte} ungültig ('{a[spalte]}')")

        # Einheitliche Schreibweisen
        a["waehrung"] = WAEHRUNGEN.get(a["waehrung"].upper(), a["waehrung"])
        if a["waehrung"] not in ("EUR", "CZK", "PLN", "CHF"):
            gruende.append(f"Währung unbekannt ('{a['waehrung']}')")
        a["einheit"] = EINHEITEN.get(a["einheit"].upper(), a["einheit"])

        # Datum
        try:
            a["angebotsdatum"] = _zu_datum(a["angebotsdatum"])
            a["gueltig_bis"] = _zu_datum(a["gueltig_bis"])
            if a["gueltig_bis"] < a["angebotsdatum"]:
                gruende.append("gültig_bis liegt vor dem Angebotsdatum")
        except ValueError as e:
            gruende.append(str(e))

        # Plausibilität (nur prüfen, wenn die Umwandlung geklappt hat)
        def ist_zahl(spalte):
            return isinstance(a[spalte], (int, float))

        if ist_zahl("einzelpreis") and a["einzelpreis"] <= 0:
            gruende.append("Preis muss > 0 sein")
        if ist_zahl("menge") and a["menge"] <= 0:
            gruende.append("Menge muss > 0 sein")
        if ist_zahl("lieferzeit_tage") and a["lieferzeit_tage"] < 0:
            gruende.append("negative Lieferzeit")
        if ist_zahl("qualitaet") and not 1 <= a["qualitaet"] <= 5:
            gruende.append(f"Qualität {a['qualitaet']} nicht zwischen 1 und 5")
        for spalte in ("liefertreue_prozent", "reklamationsquote_prozent"):
            if ist_zahl(spalte) and not 0 <= a[spalte] <= 100:
                gruende.append(f"{spalte} {a[spalte]} nicht zwischen 0 und 100")
        if (
            all(ist_zahl(s) for s in ("einzelpreis", "menge", "gesamtpreis"))
            and a["menge"] > 0
        ):
            erwartet = a["einzelpreis"] * a["menge"]
            if abs(a["gesamtpreis"] - erwartet) > erwartet * 0.01:  # 1 % Toleranz
                gruende.append("Gesamtpreis ≠ Menge × Einzelpreis")

        if gruende:
            fehlerhafte.append((a, gruende))
        else:
            gueltige.append(a)

    print(f"✓ {len(gueltige)} gültige Angebote, {len(fehlerhafte)} aussortiert.")
    return gueltige, fehlerhafte


def zeige_fehler(fehlerhafte):
    """Gibt die aussortierten Angebote mit Grund aus."""
    for angebot, gruende in fehlerhafte:
        name = angebot.get("lieferant") or "(ohne Namen)"
        print(f"  ✗ {angebot['angebots_id']}  {name:<35} {'; '.join(gruende)}")


if __name__ == "__main__":
    # Schnelltest:  python daten_laden.py
    for pfad in ("daten/angebote.csv", "daten/angebote_fehlerhaft.csv"):
        print(f"\n=== {pfad} ===")
        gueltige, fehlerhafte = pruefe_daten(lade_angebote(pfad))
        zeige_fehler(fehlerhafte)
