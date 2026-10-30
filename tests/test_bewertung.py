import pytest

from bewertung import artikel_liste, bewerte, erstelle_rangliste, normalisiere


def angebot(lieferant, artikelnr="A1", preis=2.0, lieferzeit=10, qualitaet=3, treue=95.0, reklamation=1.0):
    return {
        "lieferant": lieferant,
        "artikelnr": artikelnr,
        "artikel": f"Artikel {artikelnr}",
        "einzelpreis_eur": preis,
        "lieferzeit_tage": lieferzeit,
        "qualitaet": qualitaet,
        "liefertreue_prozent": treue,
        "reklamationsquote_prozent": reklamation,
    }


def test_normalisiere_hoch_ist_besser():
    assert normalisiere([10, 20, 30], "hoch") == [0.0, 0.5, 1.0]


def test_normalisiere_niedrig_wird_gespiegelt():
    assert normalisiere([10, 20, 30], "niedrig") == [1.0, 0.5, 0.0]


def test_normalisiere_gleiche_werte_alle_eins():
    assert normalisiere([5, 5, 5], "niedrig") == [1.0, 1.0, 1.0]


def test_bester_lieferant_in_allen_kriterien_gewinnt():
    angebote = [
        angebot("Schlecht", preis=3.0, lieferzeit=20, qualitaet=1, treue=80.0, reklamation=5.0),
        angebot("Gut", preis=1.0, lieferzeit=2, qualitaet=5, treue=99.0, reklamation=0.1),
    ]
    rangliste = erstelle_rangliste(bewerte(angebote), "A1")
    assert [a["lieferant"] for a in rangliste] == ["Gut", "Schlecht"]
    assert rangliste[0]["score"] == pytest.approx(1.0)
    assert rangliste[1]["score"] == pytest.approx(0.0)
    assert [a["rang"] for a in rangliste] == [1, 2]


def test_gewichte_entscheiden_bei_zielkonflikt():
    # Billig gewinnt nur den Preis (40 %), Schnell alles andere (60 %)
    angebote = [
        angebot("Billig", preis=1.0, lieferzeit=20, qualitaet=1, treue=80.0, reklamation=5.0),
        angebot("Schnell", preis=3.0, lieferzeit=2, qualitaet=5, treue=99.0, reklamation=0.1),
    ]
    rangliste = erstelle_rangliste(bewerte(angebote), "A1")
    assert rangliste[0]["lieferant"] == "Schnell"
    assert rangliste[1]["score"] == pytest.approx(0.4)


def test_verglichen_wird_nur_innerhalb_eines_artikels():
    angebote = [
        angebot("Teuer A1", artikelnr="A1", preis=5.0),
        angebot("Billig A1", artikelnr="A1", preis=1.0),
        angebot("Einziger A2", artikelnr="A2", preis=99.0),
    ]
    bewerte(angebote)
    # Allein in seiner Gruppe: in jedem Kriterium der beste
    assert angebote[2]["score"] == pytest.approx(1.0)
    assert [a["lieferant"] for a in erstelle_rangliste(angebote, "A1")] == ["Billig A1", "Teuer A1"]


def test_artikel_liste_sortiert_nach_nummer():
    angebote = [angebot("x", artikelnr="B2"), angebot("y", artikelnr="A1")]
    assert list(artikel_liste(angebote)) == ["A1", "B2"]
