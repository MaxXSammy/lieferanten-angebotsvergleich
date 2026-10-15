"""KI Kaufempfehlung zur Rangliste mit GPT-4o.
"""

import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # lädt den API-Key aus der .env

SYSTEM_PROMPT = (
    "Du bist ein Einkaufsberater. Du bekommst eine bewertete Rangliste "
    "von Lieferantenangeboten (Preis in Euro, Lieferzeit in Tagen, Qualität 1-5, "
    "Score 0-1, höher ist besser). Schreibe auf Deutsch eine kurze Empfehlung "
    "(maximal 5 Sätze): Welcher Lieferant sollte gewählt werden und warum, was "
    "spricht für die Alternative auf Platz 2, und gibt es einen Haken? "
    "Nutze nur die gelieferten Zahlen, erfinde nichts dazu."
)


def erstelle_empfehlung(rangliste):
    """Fragt GPT-4o nach einer Empfehlung und gibt sie aus."""
    try:
        client = OpenAI()
        antwort = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.3,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(rangliste, ensure_ascii=False)},
            ],
        )
        text = antwort.choices[0].message.content
        print("\nKI-Empfehlung:\n" + text)
        return text
    except Exception as fehler:
        print(f"\nFehler: Keine KI-Empfehlung möglich ({fehler})")
        return None


if __name__ == "__main__":
    # Schnelltest mit Beispieldaten:  python ki_zusammenfassung.py
    from testdaten import BEISPIEL_RANGLISTE
    erstelle_empfehlung(BEISPIEL_RANGLISTE)
