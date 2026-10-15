"""Zentrale Einstellungen – kein anderes Modul enthält feste Werte."""

DATEI = "daten/angebote.csv"
ZIELWAEHRUNG = "EUR"

# Welche Spalten zählen, wie stark, und ob hoch oder niedrig besser ist
KRITERIEN = {
    "einzelpreis_eur":           {"gewicht": 0.40, "besser": "niedrig"},
    "lieferzeit_tage":           {"gewicht": 0.20, "besser": "niedrig"},
    "qualitaet":                 {"gewicht": 0.20, "besser": "hoch"},
    "liefertreue_prozent":       {"gewicht": 0.10, "besser": "hoch"},
    "reklamationsquote_prozent": {"gewicht": 0.10, "besser": "niedrig"},
}

# Notfall-Kurse (1 Einheit Fremdwährung = x EUR), falls die API nicht erreichbar ist
FALLBACK_KURSE = {"EUR": 1.0, "CZK": 0.0411, "PLN": 0.2291, "CHF": 1.0718}

API_URL = "https://api.frankfurter.app/latest"# config.py - Einstellungen und Kriterien (Max) 
