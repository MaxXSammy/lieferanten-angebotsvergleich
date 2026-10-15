"""Ausgabe der Rangliste als Tabelle und als Diagramm."""

import pandas as pd
import matplotlib.pyplot as plt


def zeige_tabelle(rangliste):
    """Gibt die Rangliste als Tabelle im Terminal aus."""
    df = pd.DataFrame(rangliste)          # Liste von Dictionaries -> Tabelle
    df.index = df.index + 1               # Platz 1, 2, 3 statt 0, 1, 2
    df.index.name = "Platz"
    df = df.rename(columns={
        "lieferant": "Lieferant",
        "preis": "Preis (€)",
        "lieferzeit_tage": "Lieferzeit (Tage)",
        "qualitaet": "Qualität (1-5)",
        "score": "Score",
    })
    print("\nLieferanten-Rangliste")
    print(df.to_string())


def zeige_diagramm(rangliste):
    """Zeigt die Scores als Balkendiagramm und speichert es als rangliste.png."""
    df = pd.DataFrame(rangliste)
    df = df.iloc[::-1]                    # umdrehen, damit Platz 1 oben steht

    farben = ["grey"] * len(df)
    farben[-1] = "green"                  # Gewinner grün hervorheben

    ax = df.plot.barh(x="lieferant", y="score", color=farben, legend=False)
    ax.set_title("Lieferanten-Angebotsvergleich")
    ax.set_xlabel("Score (höher = besser)")
    ax.set_ylabel("")

    plt.tight_layout()
    plt.savefig("rangliste.png")
    print("Diagramm gespeichert: rangliste.png")
    plt.show()


if __name__ == "__main__":
    # Schnelltest mit Beispieldaten:  python bericht.py
    from testdaten import BEISPIEL_RANGLISTE
    zeige_tabelle(BEISPIEL_RANGLISTE)
    zeige_diagramm(BEISPIEL_RANGLISTE)
