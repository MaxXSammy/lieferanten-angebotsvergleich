"""Rechnet Fremdwährungen per Wechselkurs-API in Euro um."""

import requests
from config import API_URL, FALLBACK_KURSE, ZIELWAEHRUNG


def hole_kurse(waehrungen):
    """Gibt z. B. {"EUR": 1.0, "CZK": 0.0411, ...} zurück (1 Fremdwährung = x EUR)."""
    # TODO 1: Die API mit requests.get() aufrufen
    #         params: from=ZIELWAEHRUNG, to= die Währungen mit Komma verbunden
    #         timeout nicht vergessen
    # TODO 2: Aus der Antwort .json() -> "rates" holen
    # TODO 3: Die API liefert EUR -> CZK (24.357). Du brauchst CZK -> EUR. Wie?
    # TODO 4: "EUR": 1.0 ergänzen
    # TODO 5: Alles in try/except – bei Fehler: Warnung ausgeben und FALLBACK_KURSE zurückgeben
    pass


def rechne_in_euro(angebote, kurse):
    """Ergänzt jedes Angebot um einzelpreis_eur, gesamtpreis_eur und kurs."""
    # TODO: Für jedes Angebot den passenden Kurs anhand von angebot["waehrung"] holen
    #       und die beiden Preise umrechnen (auf 2 Nachkommastellen runden)
    pass


if __name__ == "__main__":
    kurse = hole_kurse(["CZK", "PLN", "CHF"])
    print(kurse)

    test = [
        {
            "lieferant": "Test s.r.o.",
            "einzelpreis": 56.87,
            "gesamtpreis": 28435.0,
            "waehrung": "CZK",
        }
    ]
    print(
        rechne_in_euro(test, kurse)
    )  # erwartet: ca. 2.34 € / 1168 €# waehrung.py - Wechselkurs-API (Max)
