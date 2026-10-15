"""Rechnet Fremdwährungen per Wechselkurs-API in Euro um."""

import requests
from config import API_URL, FALLBACK_KURSE, ZIELWAEHRUNG


def hole_kurse(waehrungen):
    """Holt aktuelle Kurse von der Frankfurter API (EZB-Kurse).

    Gibt z. B. {"EUR": 1.0, "CZK": 0.0411, ...} zurück
    -> 1 Einheit Fremdwährung = x EUR.
    Ist die API nicht erreichbar, werden die FALLBACK_KURSE aus config.py genutzt.
    """
    # EUR selbst muss nicht abgefragt werden
    fremd = [w for w in waehrungen if w != ZIELWAEHRUNG]

    try:
        antwort = requests.get(
            API_URL,
            params={"from": ZIELWAEHRUNG, "to": ",".join(fremd)},
            timeout=10,
        )
        antwort.raise_for_status()  # wirft Fehler bei 404, 500 usw.
        daten = antwort.json()
        rates = daten["rates"]  # z. B. {"CZK": 24.357, ...}  (1 EUR = x CZK)

        # Umdrehen: 1 CZK = 1 / 24.357 EUR
        kurse = {waehrung: 1 / kurs for waehrung, kurs in rates.items()}
        kurse[ZIELWAEHRUNG] = 1.0

        print(f"✓ Wechselkurse vom {daten['date']} geladen (EZB).")
        return kurse

    except (requests.RequestException, KeyError, ValueError) as fehler:
        print(f"⚠ Wechselkurs-API nicht erreichbar ({fehler}) – nutze Notfall-Kurse.")
        return FALLBACK_KURSE


def rechne_in_euro(angebote, kurse):
    """Ergänzt jedes Angebot um einzelpreis_eur, gesamtpreis_eur und kurs."""
    for angebot in angebote:
        waehrung = angebot["waehrung"]

        if waehrung not in kurse:
            print(
                f"⚠ Unbekannte Währung '{waehrung}' bei {angebot['lieferant']} – übersprungen."
            )
            continue

        kurs = kurse[waehrung]
        angebot["kurs"] = round(kurs, 6)
        angebot["einzelpreis_eur"] = round(angebot["einzelpreis"] * kurs, 4)
        angebot["gesamtpreis_eur"] = round(angebot["gesamtpreis"] * kurs, 2)

    return angebote


if __name__ == "__main__":
    # Schnelltest:  python waehrung.py
    kurse = hole_kurse(["CZK", "PLN", "CHF"])
    print(kurse)

    test = [
        {
            "lieferant": "Test s.r.o.",
            "einzelpreis": 56.87,
            "gesamtpreis": 28435.0,
            "waehrung": "CZK",
        },
        {
            "lieferant": "Test GmbH",
            "einzelpreis": 2.10,
            "gesamtpreis": 1050.0,
            "waehrung": "EUR",
        },
    ]
    for a in rechne_in_euro(test, kurse):
        print(
            f"{a['lieferant']:<15} {a['einzelpreis']:>8} {a['waehrung']}  ->  "
            f"{a['einzelpreis_eur']:>6} EUR   (gesamt {a['gesamtpreis_eur']} EUR)"
        )
