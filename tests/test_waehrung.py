import pytest
import requests

import waehrung
from config import FALLBACK_KURSE


class Antwort:
    def __init__(self, daten):
        self._daten = daten

    def raise_for_status(self):
        pass

    def json(self):
        return self._daten


def test_kurse_werden_umgedreht(monkeypatch):
    monkeypatch.setattr(
        waehrung.requests, "get", lambda *a, **kw: Antwort({"date": "2026-10-30", "rates": {"CZK": 25.0}})
    )
    kurse = waehrung.hole_kurse(["EUR", "CZK"])
    assert kurse == {"CZK": pytest.approx(0.04), "EUR": 1.0}


def test_api_ausfall_nutzt_notfallkurse(monkeypatch):
    def kaputt(*a, **kw):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(waehrung.requests, "get", kaputt)
    assert waehrung.hole_kurse(["CZK"]) == FALLBACK_KURSE


def test_rechne_in_euro():
    angebote = [{"lieferant": "x", "einzelpreis": 50.0, "gesamtpreis": 5000.0, "waehrung": "CZK"}]
    a = waehrung.rechne_in_euro(angebote, {"CZK": 0.04, "EUR": 1.0})[0]
    assert (a["einzelpreis_eur"], a["gesamtpreis_eur"]) == (2.0, 200.0)


def test_unbekannte_waehrung_wird_uebersprungen():
    angebote = [{"lieferant": "x", "einzelpreis": 1.0, "gesamtpreis": 1.0, "waehrung": "USD"}]
    a = waehrung.rechne_in_euro(angebote, {"EUR": 1.0})[0]
    assert "einzelpreis_eur" not in a
