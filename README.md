# Multi-Agent Orchestration Demo

Paper-Analyzer mit drei Orchestrierungs-Varianten:
- **LangChain**: Sequenziell (Reader → Summarizer → Critic → Integrator)
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

**Detaillierte Anleitung:** Siehe `START_HIER.md`

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

## Nutzung
- Lade PDF/TXT hoch, die App erstellt einen abschnittsbasierten Analyse-Kontext (Budget konfigurierbar).
- Wähle Pipeline (LangChain/LangGraph/DSPy) und Modell/Parameter in der Sidebar.
- Button "Starten" führt die gewählte Pipeline aus.
- Button "Alle Pipelines vergleichen" führt LC/LG/DSPy nacheinander aus und zeigt Metriken/Outputs nebeneinander.
- Button "DSPy Teleprompt Gain" vergleicht DSPy-Base vs. Teleprompting (Dev-Set nötig).
- Expander "Telemetry (CSV)" zeigt gesammelte Laufzeiten pro Engine (`telemetry.csv`).
- Optionales W&B-Logging aktivierbar via Env `WANDB_ENABLED=1` (Projekt/Entity per `WANDB_PROJECT`/`WANDB_ENTITY`).

## DSPy
- Aktivierbar über Sidebar-Checkbox "DSPy optimieren" (Teleprompting), nutzt `eval/dev.jsonl` als Dev-Set.
- Falls `dspy-ai` oder `litellm` fehlen, führt die App einen Stub aus und warnt im UI.

## Evaluierung
- `eval_runner.py` führt ein Dev-Set über alle Pipelines aus und berechnet ein einfaches unigram-F1 zwischen Kontext und Summary.

## Struktur
- `agents/`: Einzel-Agenten (Reader, Summarizer, Critic, Integrator)
- `workflows/`: Pipelines für LangChain, LangGraph, DSPy
- `telemetry.py`: CSV-Logging
- `utils.py`: Text-Normalisierung und Abschnittslogik

