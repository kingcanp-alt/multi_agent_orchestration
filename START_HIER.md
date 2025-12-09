# START HIER - Workshop-Teilnehmer

## Willkommen zum Workshop!

Einfachste Methode: Doppelklick auf `run.bat` (Windows) oder `run.sh` (Mac/Linux).

---

## Super einfach: Doppelklick-Start

### Windows:
1. Doppelklick auf `run.bat`
2. Warte bis der Browser sich öffnet (1-2 Minuten beim ersten Mal)
3. Fertig

### Mac/Linux:
1. Doppelklick auf `run.sh` (oder im Terminal: `chmod +x run.sh && ./run.sh`)
2. Warte bis der Browser sich öffnet (1-2 Minuten beim ersten Mal)
3. Fertig

Was passiert automatisch:
- Das Skript prüft Python
- Das Skript erstellt Virtual Environment (falls nötig)
- Das Skript installiert Abhängigkeiten
- Das Skript erstellt `.env` Datei (falls nötig)
- Die App startet im Browser

Einzige manuelle Sache: API-Key in `.env` eintragen (falls noch nicht geschehen)

---

## API-Key einrichten (einmalig)

Falls beim Start eine Meldung kommt, dass das Skript `.env` erstellt hat:

1. Öffne die Datei `.env` in einem Text-Editor
2. Trage deinen API-Key ein:
   ```
   OPENAI_API_KEY=sk-dein-api-key-hier
   ```
3. Speichere die Datei
4. Starte die App nochmal (Doppelklick auf `run.bat` / `run.sh`)

Wo bekomme ich einen API-Key?
- Fragt eure Workshopleiter - oft stellen sie einen bereit
- Oder: [OpenAI Platform](https://platform.openai.com/api-keys)

---

## Prüfung: Funktioniert alles?

1. Doppelklick auf run.bat/run.sh - Terminal-Fenster öffnet sich
2. "App startet jetzt im Browser!" erscheint - Gut
3. Browser öffnet sich - Gut
4. Ihr seht die App - Gut
5. Ihr könnt ein PDF hochladen - Perfekt

---

## Hilfe bei Problemen

### Windows: "Python nicht gefunden"
- Lösung: Python installieren: [python.org/downloads](https://www.python.org/downloads/)
- Wichtig: Bei Installation "Add Python to PATH" ankreuzen

### Mac/Linux: "Permission denied"
- Lösung: Im Terminal:
  ```bash
  chmod +x run.sh
  ./run.sh
  ```

### "API Key nicht gefunden"
- `.env` Datei öffnen und prüfen, ob API-Key drin steht
- Format: `OPENAI_API_KEY=sk-...`
- Keine Leerzeichen um das `=`

### Port bereits belegt
- Andere Streamlit-App schließen
- Oder in `run.bat` / `run.sh` Port ändern

### Installation dauert lange
- Normal beim ersten Mal. 1-2 Minuten
- Beim zweiten Mal geht es schneller (Dependencies sind schon da)

---

## Weiterführende Informationen

- Workshop-Skript: `TEILNEHMER_SKRIPT.md` - Alle Aufgaben und Experimente
- Code-Experimente: `CODE_EXPERIMENTE.md` - Code-Snippets zum Kopieren

---

## Was kommt jetzt?

Nach dem Start könnt ihr:
1. Die App nutzen und die drei Frameworks testen
2. Code-Experimente durchführen (siehe `TEILNEHMER_SKRIPT.md`)
3. Prompts ändern, Nodes hinzufügen, Signatures anpassen

Viel Erfolg beim Workshop.

---

## Alternative: Manueller Start (falls Doppelklick nicht funktioniert)

Falls der Doppelklick-Start nicht funktioniert, könnt ihr auch manuell starten:

1. Terminal öffnen im Projektordner
2. Setup:
   ```bash
   # Windows:
   py -3 -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   
   # Mac/Linux:
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. App starten:
   ```bash
   streamlit run app.py
   ```

Aber: Der Doppelklick-Start ist viel einfacher.
