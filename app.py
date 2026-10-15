"""Weboberfläche für den Lieferanten-Angebotsvergleich.

Start:  streamlit run app.py
"""

import copy
import csv
import io

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from config import DATEI, KRITERIEN
from daten_laden import pruefe_daten
from waehrung import hole_kurse, rechne_in_euro
from bewertung import bewerte, erstelle_rangliste, artikel_liste
from ki_zusammenfassung import erstelle_empfehlung
from main import kompakt, ersatz_empfehlung

st.set_page_config(page_title="Angebotsvergleich", page_icon="📦", layout="wide")

BESCHRIFTUNG = {
    "einzelpreis_eur": "💶 Preis",
    "lieferzeit_tage": "🚚 Lieferzeit",
    "qualitaet": "⭐ Qualität",
    "liefertreue_prozent": "🎯 Liefertreue",
    "reklamationsquote_prozent": "⚠️ Reklamationsquote",
}
SPALTEN = {
    "rang": "Platz", "lieferant": "Lieferant", "land": "Land", "einzelpreis": "Preis",
    "waehrung": "Währung", "einzelpreis_eur": "Preis (€)", "gesamtpreis_eur": "Gesamt (€)",
    "lieferzeit_tage": "Lieferzeit (Tage)", "qualitaet": "Qualität",
    "liefertreue_prozent": "Liefertreue (%)", "reklamationsquote_prozent": "Reklamation (%)",
    "zertifizierung": "Zertifikate", "score": "Score",
}


# ---------- Daten & Kurse (mit Cache, damit nicht bei jedem Klick neu geladen wird) ---------- #
@st.cache_data(ttl=3600, show_spinner="Hole Wechselkurse von der EZB …")
def lade_kurse(waehrungen):
    return hole_kurse(list(waehrungen))


def lese_csv(text):
    return list(csv.DictReader(io.StringIO(text)))


# ---------- Seitenleiste ---------- #
with st.sidebar:
    st.header("📂 Daten")
    quelle = st.radio("Datenquelle", ["Beispieldaten", "Beispieldaten (fehlerhaft)", "Eigene CSV hochladen"])

    if quelle == "Eigene CSV hochladen":
        upload = st.file_uploader("CSV-Datei", type="csv")
        if upload is None:
            st.info("Bitte eine CSV-Datei hochladen.")
            st.stop()
        roh_text = upload.getvalue().decode("utf-8")
    else:
        pfad = DATEI if quelle == "Beispieldaten" else "daten/angebote_fehlerhaft.csv"
        with open(pfad, encoding="utf-8") as f:
            roh_text = f.read()

    st.header("⚖️ Gewichtung")
    st.caption("Wie wichtig ist dir welches Kriterium?")
    roh_gewichte = {
        spalte: st.slider(BESCHRIFTUNG.get(spalte, spalte), 0, 100, int(regel["gewicht"] * 100), step=5)
        for spalte, regel in KRITERIEN.items()
    }
    summe = sum(roh_gewichte.values())
    if summe == 0:
        st.error("Mindestens ein Kriterium braucht ein Gewicht > 0.")
        st.stop()

    # Gewichte auf 100 % normieren
    kriterien = {
        spalte: {"gewicht": wert / summe, "besser": KRITERIEN[spalte]["besser"]}
        for spalte, wert in roh_gewichte.items()
    }
    st.caption(" · ".join(f"{BESCHRIFTUNG[s].split()[-1]} {k['gewicht']:.0%}" for s, k in kriterien.items()))


# ---------- Verarbeitung: laden → prüfen → umrechnen → bewerten ---------- #
gueltige, fehlerhafte = pruefe_daten(lese_csv(roh_text))
if not gueltige:
    st.error("Keine gültigen Angebote in der Datei gefunden.")
    st.stop()

kurse = lade_kurse(tuple(sorted({a["waehrung"] for a in gueltige})))
gueltige = rechne_in_euro(copy.deepcopy(gueltige), kurse)
bewerte(gueltige, kriterien)
artikel = artikel_liste(gueltige)


# ---------- Kopfbereich ---------- #
st.title("📦 Lieferanten-Angebotsvergleich")
st.caption("Angebote in EUR, CZK, PLN & CHF vergleichen – mit Live-Wechselkursen und KI-Empfehlung")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Gültige Angebote", len(gueltige))
k2.metric("Aussortiert", len(fehlerhafte))
k3.metric("Lieferanten", len({a["lieferant"] for a in gueltige}))
k4.metric("Artikel", len(artikel))

tab_rang, tab_uebersicht, tab_fehler, tab_kurse = st.tabs(
    ["🏆 Rangliste", "📋 Übersicht aller Artikel", f"❌ Aussortiert ({len(fehlerhafte)})", "💱 Wechselkurse"]
)

# ---------- Tab 1: Rangliste pro Artikel ---------- #
with tab_rang:
    artikelnr = st.selectbox(
        "Artikel", list(artikel), format_func=lambda nr: f"{nr} – {artikel[nr]}"
    )
    rangliste = erstelle_rangliste(gueltige, artikelnr)
    gewinner = rangliste[0]

    st.success(
        f"🏆 **Empfehlung: {gewinner['lieferant']}** ({gewinner['land']}) – "
        f"Score {gewinner['score']:.2f} · {gewinner['einzelpreis_eur']:.4g} € · "
        f"{gewinner['lieferzeit_tage']} Tage · Qualität {gewinner['qualitaet']}/5"
    )

    links, rechts = st.columns([3, 2])
    with links:
        df = pd.DataFrame(rangliste)[[s for s in SPALTEN if s in rangliste[0]]].rename(columns=SPALTEN)
        st.dataframe(df, hide_index=True, use_container_width=True)

    with rechts:
        top = rangliste[:10][::-1]
        fig, ax = plt.subplots(figsize=(5, 0.45 * len(top) + 1))
        farben = ["#9aa5b1"] * (len(top) - 1) + ["#2e7d32"]
        ax.barh([a["lieferant"] for a in top], [a["score"] for a in top], color=farben)
        ax.set_xlabel("Score (höher = besser)")
        ax.set_xlim(0, 1)
        ax.spines[["top", "right"]].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig)

    st.download_button(
        "⬇️ Rangliste als CSV",
        df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
        file_name=f"rangliste_{artikelnr}.csv",
        mime="text/csv",
    )

    st.subheader("🤖 KI-Empfehlung")
    if st.button("Empfehlung erstellen"):
        with st.spinner("Die KI denkt nach …"):
            top5 = kompakt(rangliste)[:5]
            text = erstelle_empfehlung(top5)
        if text:
            st.info(text)
        else:
            st.warning("KI nicht verfügbar – regelbasierte Empfehlung:")
            st.info(ersatz_empfehlung(kompakt(rangliste)))

# ---------- Tab 2: Gewinner je Artikel ---------- #
with tab_uebersicht:
    zeilen = []
    for nr, name in artikel.items():
        erster = erstelle_rangliste(gueltige, nr)[0]
        zeilen.append({
            "Artikel": f"{nr} – {name}", "Bester Lieferant": erster["lieferant"], "Land": erster["land"],
            "Preis (€)": round(erster["einzelpreis_eur"], 4), "Lieferzeit (Tage)": erster["lieferzeit_tage"],
            "Qualität": erster["qualitaet"], "Score": round(erster["score"], 2),
        })
    st.dataframe(pd.DataFrame(zeilen), hide_index=True, use_container_width=True)

# ---------- Tab 3: Aussortierte Angebote ---------- #
with tab_fehler:
    if fehlerhafte:
        st.dataframe(
            pd.DataFrame([
                {"Angebot": a["angebots_id"], "Lieferant": a.get("lieferant") or "(ohne Namen)",
                 "Grund": "; ".join(gruende)}
                for a, gruende in fehlerhafte
            ]),
            hide_index=True, use_container_width=True,
        )
    else:
        st.success("Alle Angebote sind gültig. 🎉")

# ---------- Tab 4: Wechselkurse ---------- #
with tab_kurse:
    st.caption("Quelle: Frankfurter API (offizielle EZB-Referenzkurse)")
    st.dataframe(
        pd.DataFrame([
            {"Währung": w, "1 Einheit = … €": round(k, 4), "1 € = …": round(1 / k, 4)}
            for w, k in sorted(kurse.items())
        ]),
        hide_index=True,
    )
