# """Bewertet Angebote nach gewichteten Kriterien und erstellt Ranglisten."""

from config import KRITERIEN


def normalisiere(werte, besser):
    """Skaliert eine Liste von Zahlen auf 0–1 (1 = am besten).

    Min-Max-Normalisierung: (wert - min) / (max - min)
    Bei besser="niedrig" wird umgedreht, damit der kleinste Wert 1 bekommt.
    """
    minimum, maximum = min(werte), max(werte)

    # Sonderfall: alle Werte gleich -> keiner ist besser, alle bekommen 1
    if maximum == minimum:
        return [1.0] * len(werte)

    normiert = [(w - minimum) / (maximum - minimum) for w in werte]

    if besser == "niedrig":
        normiert = [1 - n for n in normiert]

    return normiert


def bewerte(angebote, kriterien=KRITERIEN):
    """Berechnet für jedes Angebot einen score (0–1).

    Verglichen wird immer nur innerhalb desselben Artikels (artikelnr),
    denn Schrauben gegen Kartons zu vergleichen ergibt keinen Sinn.
    """
    # 1) Angebote nach Artikel gruppieren
    gruppen = {}
    for angebot in angebote:
        gruppen.setdefault(angebot["artikelnr"], []).append(angebot)

    # 2) Pro Artikel jedes Kriterium normalisieren und gewichtet aufaddieren
    for gruppe in gruppen.values():
        for angebot in gruppe:
            angebot["score"] = 0.0

        for spalte, regel in kriterien.items():
            werte = [angebot[spalte] for angebot in gruppe]
            normiert = normalisiere(werte, regel["besser"])

            for angebot, n in zip(gruppe, normiert):
                angebot["score"] += n * regel["gewicht"]

        for angebot in gruppe:
            angebot["score"] = round(angebot["score"], 3)

    return angebote


def erstelle_rangliste(angebote, artikelnr):
    """Filtert auf einen Artikel, sortiert nach score und setzt den rang."""
    auswahl = [a for a in angebote if a["artikelnr"] == artikelnr]
    auswahl.sort(key=lambda a: a["score"], reverse=True)

    for platz, angebot in enumerate(auswahl, start=1):
        angebot["rang"] = platz

    return auswahl


def artikel_liste(angebote):
    """Gibt alle Artikel als {artikelnr: artikelname} zurück – z. B. für ein Auswahlmenü."""
    return {
        a["artikelnr"]: a["artikel"]
        for a in sorted(angebote, key=lambda a: a["artikelnr"])
    }


if __name__ == "__main__":
    # Schnelltest:  python bewertung.py
    test = [
        {
            "lieferant": "Billig s.r.o.",
            "artikelnr": "A1",
            "einzelpreis_eur": 1.80,
            "lieferzeit_tage": 20,
            "qualitaet": 2,
            "liefertreue_prozent": 82.0,
            "reklamationsquote_prozent": 4.1,
        },
        {
            "lieferant": "Solide GmbH",
            "artikelnr": "A1",
            "einzelpreis_eur": 2.10,
            "lieferzeit_tage": 6,
            "qualitaet": 4,
            "liefertreue_prozent": 96.5,
            "reklamationsquote_prozent": 0.8,
        },
        {
            "lieferant": "Premium AG",
            "artikelnr": "A1",
            "einzelpreis_eur": 2.60,
            "lieferzeit_tage": 3,
            "qualitaet": 5,
            "liefertreue_prozent": 99.0,
            "reklamationsquote_prozent": 0.3,
        },
    ]

    bewerte(test)
    for a in erstelle_rangliste(test, "A1"):
        print(f"{a['rang']}. {a['lieferant']:<15} Score {a['score']:.3f}")
