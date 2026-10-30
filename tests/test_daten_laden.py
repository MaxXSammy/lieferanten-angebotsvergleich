import csv
from datetime import date
from pathlib import Path

import pytest

from daten_laden import _zu_datum, _zu_zahl, lade_angebote, pruefe_daten

DATEN = Path(__file__).resolve().parents[1] / "daten"


@pytest.mark.parametrize(
    "roh, erwartet",
    [("3,58", 3.58), ("1.240,50 €", 1240.5), (" 12 ", 12.0), ("2.5", 2.5)],
)
def test_zu_zahl_repariert_formate(roh, erwartet):
    assert _zu_zahl(roh) == erwartet


@pytest.mark.parametrize("roh", ["", "€", "ca. 2 Wochen", "auf Anfrage"])
def test_zu_zahl_lehnt_unsinn_ab(roh):
    with pytest.raises(ValueError):
        _zu_zahl(roh)


def test_zu_datum_akzeptiert_iso_und_deutsch():
    assert _zu_datum("2026-07-15") == date(2026, 7, 15)
    assert _zu_datum("15.07.2026") == date(2026, 7, 15)


def test_saubere_testdaten_sind_alle_gueltig():
    gueltige, fehlerhafte = pruefe_daten(lade_angebote(DATEN / "angebote.csv"))
    assert len(gueltige) == 170
    assert fehlerhafte == []


def test_fehlerhafte_testdaten_werden_mit_grund_aussortiert():
    gueltige, fehlerhafte = pruefe_daten(lade_angebote(DATEN / "angebote_fehlerhaft.csv"))
    assert (len(gueltige), len(fehlerhafte)) == (145, 28)
    gruende = {g for _, liste in fehlerhafte for g in liste}
    assert "doppelte Angebots-ID" in gruende
    assert "Lieferant fehlt" in gruende
    assert "Gesamtpreis ≠ Menge × Einzelpreis" in gruende


def test_schreibweisen_werden_vereinheitlicht(tmp_path):
    zeile = next(csv.DictReader(open(DATEN / "angebote.csv", encoding="utf-8")))
    zeile.update(waehrung="Kč", einheit="Stück", einzelpreis="56,87", angebotsdatum="10.09.2026")
    pfad = tmp_path / "eine_zeile.csv"
    with open(pfad, "w", encoding="utf-8", newline="") as datei:
        schreiber = csv.DictWriter(datei, fieldnames=zeile.keys())
        schreiber.writeheader()
        schreiber.writerow(zeile)

    gueltige, fehlerhafte = pruefe_daten(lade_angebote(pfad))
    assert fehlerhafte == []
    a = gueltige[0]
    assert (a["waehrung"], a["einheit"], a["einzelpreis"]) == ("CZK", "Stk", 56.87)
    assert a["angebotsdatum"] == date(2026, 9, 10)


def test_fehlende_datei_gibt_leere_liste(tmp_path):
    assert lade_angebote(tmp_path / "gibt_es_nicht.csv") == []
