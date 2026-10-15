"""Lieferanten-Angebotsvergleich – verbindet alle Module.

Start:
    python main.py                                  -> nutzt die Datei aus config.py
    python main.py daten/angebote_fehlerhaft.csv    -> andere Datei testen
"""

import sys

from config import DATEI
from daten_laden import lade_angebote, pruefe_daten, zeige_fehler
from waehrung import hole_kurse, rechne_in_euro
from bewertung import bewerte, erstelle_rangliste, artikel_liste
from bericht import zeige_tabelle, zeige_diagramm
from ki_zusammenfassung import erstelle_empfehlung


def kompakt(rangliste):
    """Reduziert die Rangliste auf die wichtigsten Felder für Tabelle und KI."""
    return [
        {
            "lieferant": a["lieferant"],
            "land": a["land"],
            "preis": round(a["einzelpreis_eur"], 2),
            "lieferzeit_tage": a["lieferzeit_tage"],
            "qualitaet": a["qualitaet"],
            "liefertreue_prozent": a["liefertreue_prozent"],
            "score": round(a["score"], 2),
        }
        for a in rangliste
    ]


def ersatz_empfehlung(rangliste):
    """Einfache Empfehlung ohne KI – falls die API nicht erreichbar ist."""
    erster = rangliste[0]
    text = (
        f"Empfehlung: {erster['lieferant']} (Score {erster['score']}) – "
        f"{erster['preis']:.2f} € je Einheit,{erster['lieferzeit_tage']} Tage Lieferzeit, "
        f"Qualität {erster['qualitaet']}/5."
    )
    if len(rangliste) > 1:
        zweiter = rangliste[1]
        text += f" Alternative: {zweiter['lieferant']} (Score {zweiter['score']})."
    print("\nEmpfehlung (ohne KI):\n" + text)
    return text


def waehle_artikel(artikel):
    """Zeigt alle Artikel und lässt den Nutzer einen auswählen. Gibt None bei 'q' zurück."""
    nummern = list(artikel)
    print("\nVerfügbare Artikel:")
    for i, nr in enumerate(nummern, start=1):
        print(f"  {i:>2}) {nr}  {artikel[nr]}")

    while True:
        eingabe = input("\nArtikel wählen (Nummer, q = beenden): ").strip().lower()
        if eingabe == "q":
            return None
        if eingabe.isdigit() and 1 <= int(eingabe) <= len(nummern):
            return nummern[int(eingabe) - 1]
        print("Bitte eine Zahl aus der Liste eingeben.")


def main():
    pfad = sys.argv[1] if len(sys.argv) > 1 else DATEI
    print("=" * 60)
    print(" Lieferanten-Angebotsvergleich")
    print("=" * 60)

    # 1. Laden & prüfen
    print(f"\n[1] Lade {pfad} …")
    gueltige, fehlerhafte = pruefe_daten(lade_angebote(pfad))
    if fehlerhafte:
        zeige_fehler(fehlerhafte)
    if not gueltige:
        print("Keine gültigen Angebote – Programm beendet.")
        return

    # 2. Währungen umrechnen (API)
    print("\n[2] Hole Wechselkurse …")
    kurse = hole_kurse(sorted({a["waehrung"] for a in gueltige}))
    rechne_in_euro(gueltige, kurse)

    # 3. Bewerten
    print("\n[3] Bewerte Angebote …")
    bewerte(gueltige)
    print(f"✓ {len(gueltige)} Angebote bewertet.")

    # 4.–6. Artikel wählen, Rangliste, Diagramm, KI – beliebig oft
    artikel = artikel_liste(gueltige)
    while True:
        artikelnr = waehle_artikel(artikel)
        if artikelnr is None:
            print("Tschüss!")
            break

        rangliste = kompakt(erstelle_rangliste(gueltige, artikelnr))
        print(f"\n{artikelnr} – {artikel[artikelnr]}  ({len(rangliste)} Angebote)")

        zeige_tabelle(rangliste)
        zeige_diagramm(rangliste)

        empfehlung = erstelle_empfehlung(rangliste[:5])  # Top 5 reichen der KI
        if not empfehlung:
            ersatz_empfehlung(rangliste)


if __name__ == "__main__":
    main()  # main.py - verbindet alle Module (gemeinsam)
