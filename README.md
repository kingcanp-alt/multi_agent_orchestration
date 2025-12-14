# Multi Agent Paper Analyzer

Wir orchestrieren denselben Workflow mit drei Frameworks:
- **LangChain**: Sequenziell (Reader → Summarizer → Critic → Integrator)
- **LangGraph**: Graph mit DOT Visualisierung für den Kontrollfluss
- **DSPy**: Deklarativ mit optionalem Teleprompting

---

## Schnell starten
- **Windows:** Doppelklick auf `launchers/run.bat`
- **Mac/Linux:** Doppelklick auf `launchers/run.sh` (oder `chmod +x launchers/run.sh && ./launchers/run.sh`)

Das Startskript prüft Python, legt ein virtuelles Environment an, installiert die Abhängigkeiten und startet Streamlit. Wenn `.env` neu angelegt wird, kommt eine kurze Erinnerung zum API-Key.

Mehr Details zur Einrichtung stehen in `docs/participants/START_HIER.md`.

---

## Checkliste für den Schnellstart
1. Python 3.9+ prüfen:
   ```bash
   python --version
   ```
2. Virtual Environment einrichten:
   ```bash
   python -m venv venv
   source venv/bin/activate    # Windows: venv\Scripts\activate
   ```
3. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```
4. API-Key setzen (falls noch nicht vorhanden):
   ```bash
   cp .env.example .env
   # dann OPENAI_API_KEY=sk-... eintragen
   ```
5. App starten:
   ```bash
   python -m streamlit run app/app.py
   ```

---

## Nutzung
- Datei hochladen (PDF/TXT) → strukturierte Notizen + Kontext
- Pipeline wählen (LangChain, LangGraph, DSPy) und Einstellungen anpassen
- „Starten“ führt die gewählte Pipeline aus
- „Alle Pipelines vergleichen“ zeigt Outputs und Metriken nebeneinander
- DSPy Teleprompt Gain vergleicht DSPy mit und ohne Teleprompting (Dev-Set erforderlich)
- Im Expander „Telemetry (CSV)“ stehen Laufzeitdaten

---

## Details zu DSPy
- Checkbox „DSPy optimieren“ aktiviert Teleprompting mit `dev-set/dev.jsonl`
- Das Dev-Set enthält nur wenige Beispiele und dient als Demo
- Fehlen `dspy-ai` oder `litellm`, läuft eine Platzhalter-Variante

---

## Evaluierung
- `app/eval_runner.py` wertet `dev-set/dev.jsonl` über alle Pipelines aus und berechnet ein einfaches unigram-F1

---

## Struktur
### Code
- `app/`: Anwendungscode
  - `app/app.py`: Streamlit-Frontend
  - `app/agents/`: Reader, Summarizer, Critic, Integrator
  - `app/workflows/`: Pipeline Definitionen
  - `app/eval_runner.py`: Dev Set Auswertung
  - `app/llm.py`: LLM Konfiguration
  - `app/telemetry.py`: Logging
  - `app/utils.py`: Text Vorverarbeitung
- `dev-set/`: Beispiel-Inputs für Teleprompting

### Dokumentation
- `docs/participants/`: Anleitungen für Teilnehmer
  - `START_HIER.md`
  - `TEILNEHMER_SKRIPT.md`
  - `CODE_EXPERIMENTE.md`
- `docs/moderators/`: Moderatorenunterlagen
- `project_overview.md`: Hintergrund & Design

### Startskripte
- `launchers/run.bat`: Windows Startskript
- `launchers/run.sh`: Mac/Linux Startskript

---

## Workshop Informationen
- Start: `docs/participants/START_HIER.md`
- Aufgaben & Experimente: `docs/participants/TEILNEHMER_SKRIPT.md`
