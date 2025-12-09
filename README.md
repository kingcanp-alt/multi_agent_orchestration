# Multi-Agent Orchestration Demo

Paper-Analyzer mit drei Orchestrierungs-Varianten:
- **LangChain**: Sequenziell (Reader - Summarizer - Critic - Integrator)
- **LangGraph**: Expliziter Graph mit DOT-Visualisierung
- **DSPy**: Deklarativ mit optionalem Teleprompting (Few-Shot-Bootstrap)

---

## Workshop-Teilnehmer: Super einfacher Start!

**Einfachste Methode:** Doppelklick auf `run.bat` (Windows) oder `run.sh` (Mac/Linux)!

### Schritt 1: Code herunterladen
- GitHub-Repo klonen ODER ZIP-Datei entpacken

### Schritt 2: Doppelklick-Start
- **Windows:** Doppelklick auf `run.bat`
- **Mac/Linux:** Doppelklick auf `run.sh` (oder: `chmod +x run.sh && ./run.sh`)

**Das war's!** Die App öffnet sich automatisch im Browser (1-2 Minuten beim ersten Mal).

**Einzige manuelle Sache:** API-Key in `.env` eintragen (falls beim Start erstellt wurde)

**Detaillierte Anleitung:** Siehe `docs/teilnehmer/START_HIER.md`

**Workshop-Dokumentation:** Siehe `docs/teilnehmer/` für alle Teilnehmer-Dokumente

---

## Quickstart (Detailliert)

1) **Python 3.9+ installieren** (falls nicht vorhanden)
   ```bash
   python --version  # Sollte 3.9+ sein
   ```

2) **Virtual Environment erstellen:**
   ```bash
   python -m venv venv           # oder py -3 -m venv venv (Windows)
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

3) **Abhängigkeiten installieren:**
   ```bash
   pip install -r requirements.txt
   ```

4) **API-Key konfigurieren:**
   
   Kopiere `.env.example` zu `.env`:
   ```bash
   cp .env.example .env
   ```
   
   Dann `.env` bearbeiten und deinen OpenAI API-Key eintragen:
   ```
   OPENAI_API_KEY=sk-dein-api-key-hier
   ```
   
   **Wo bekomme ich einen API-Key?**
   - [OpenAI Platform](https://platform.openai.com/api-keys)
   - Oder fragt eure Workshopleiter

5) **App starten:**
   ```bash
   streamlit run app.py
   ```
   
   Die App öffnet sich automatisch unter http://localhost:8501

---

## Nutzung
- Lade PDF/TXT hoch, die App erstellt einen abschnittsbasierten Analyse-Kontext (Budget konfigurierbar).
- Wähle Pipeline (LangChain/LangGraph/DSPy) und Modell/Parameter in der Sidebar.
- Button "Starten" führt die gewählte Pipeline aus.
- Button "Alle Pipelines vergleichen" führt LC/LG/DSPy nacheinander aus und zeigt Metriken/Outputs nebeneinander.
- Button "DSPy Teleprompt Gain" vergleicht DSPy-Base vs. Teleprompting (Dev-Set nötig).
- Expander "Telemetry (CSV)" zeigt gesammelte Laufzeiten pro Engine (`telemetry.csv`).
- Optionales W&B-Logging aktivierbar via Env `WANDB_ENABLED=1` (Projekt/Entity per `WANDB_PROJECT`/`WANDB_ENTITY`).

---

## DSPy
- Aktivierbar über Sidebar-Checkbox "DSPy optimieren" (Teleprompting), nutzt `eval/dev.jsonl` als Dev-Set.
- Falls `dspy-ai` oder `litellm` fehlen, führt die App einen Stub aus und warnt im UI.

---

## Evaluierung
- `eval_runner.py` führt ein Dev-Set über alle Pipelines aus und berechnet ein einfaches unigram-F1 zwischen Kontext und Summary.

---

## Struktur

### Code
- `agents/`: Einzel-Agenten (Reader, Summarizer, Critic, Integrator)
- `workflows/`: Pipelines für LangChain, LangGraph, DSPy
- `eval/`: Dev-Set für DSPy Teleprompting
- `telemetry.py`: CSV-Logging
- `utils.py`: Text-Normalisierung und Abschnittslogik
- `llm.py`: LLM-Konfiguration

### Dokumentation
- `docs/teilnehmer/`: Dokumentation für Workshop-Teilnehmer
  - `START_HIER.md`: Einstiegspunkt für Teilnehmer
  - `TEILNEHMER_SKRIPT.md`: Hauptskript mit allen Aufgaben
  - `CODE_EXPERIMENTE.md`: Code-Snippets zum Kopieren
- `docs/moderatoren/`: Dokumentation für Workshop-Moderatoren
  - `WORKSHOP_LEITFADEN.md`: Hauptdatei mit Zeitplan
  - `WORKSHOP_CHECKLIST.md`: Vorbereitung und Checklisten
  - `WORKSHOP_CODE_BEREITSTELLUNG.md`: Code-Verteilung
- `README.md`: Projekt-Übersicht (diese Datei)

### Start-Skripte
- `run.bat`: Windows Start-Skript (Doppelklick-Start)
- `run.sh`: Mac/Linux Start-Skript (Doppelklick-Start)

---

## Workshop-Informationen

**Für Teilnehmer:**
- Start: Siehe `docs/teilnehmer/START_HIER.md`
- Workshop-Skript: Siehe `docs/teilnehmer/TEILNEHMER_SKRIPT.md`

**Für Moderatoren:**
- Workshop-Leitfaden: Siehe `docs/moderatoren/WORKSHOP_LEITFADEN.md`
- Checkliste: Siehe `docs/moderatoren/WORKSHOP_CHECKLIST.md`
