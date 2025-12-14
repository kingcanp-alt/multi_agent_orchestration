# START HIER - Workshop Teilnehmer

## Übersicht

Ihr seid in `docs/participants/`. Für den Start müsst ihr ins Projekt Root.

**Einfachste Methode:** Start per Doppelklick auf `launchers/run.bat` (Windows) oder `launchers/run.sh` (Mac/Linux).

---

## Was passiert beim Doppelklick?

1. Python wird geprüft.
2. Ein virtuelles Environment wird angelegt (falls nötig).
3. Abhängigkeiten werden installiert.
4. `.env` wird erstellt, wenn noch nicht vorhanden.
5. Streamlit startet die App im Browser.

**Einzige Aufgabe:** API Key in `.env` eintragen (wenn noch leer).

---

## API Key setzen

1. `.env` öffnen (nach dem ersten Start ist sie da).
2. API Key eintragen:
   ```
   OPENAI_API_KEY=sk-dein-api-key-hier
   ```
3. Datei speichern.
4. App neu starten (wieder Doppelklick auf das passende Script).

API Keys bekommt ihr vom Workshop Team oder auf https://platform.openai.com/api-keys.

---

## Funktionstest

- Doppelklick auf `launchers/run.*` öffnen das Terminal.
- Meldung „App startet jetzt im Browser“ erscheint.
- Browser öffnet sich, die App ist sichtbar.
- PDF hochladen funktioniert.

---

## Hilfe bei Problemen

**Windows: „Python nicht gefunden“**
- Python installieren: https://www.python.org/downloads/
- Wichtig: „Add Python to PATH“ anklicken.

**Mac/Linux: „Permission denied“**
- Terminal: `chmod +x launchers/run.sh && ./launchers/run.sh`

**„API Key nicht gefunden“**
- `.env` prüfen: `OPENAI_API_KEY=sk-...`
- Keine Leerzeichen um das `=`.

**Port belegt**
- Andere Streamlit App schließen oder Port in `launchers/run.*` ändern.

**Installation zu langsam**
- Beim ersten Start dauert es 1-2 Minuten.
- Danach geht es schneller.

---

## Was ihr danach machen könnt

1. Die App öffnen und Pipelines (LangChain, LangGraph, DSPy) ausprobieren.
2. Die Aufgaben im Workshop Skript (`TEILNEHMER_SKRIPT.md`) bearbeiten.
3. Die Code Beispiele (`CODE_EXPERIMENTE.md`) nutzen.

---

## Alternativ: Manueller Start

1. Terminal im Projekt Root öffnen (nicht in `docs/participants/`).
2. Virtual Environment:
   ```bash
   py -3 -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. App starten:
   ```bash
   python -m streamlit run app/app.py
   ```

Der Doppelklick Start bleibt der schnellste Weg.
