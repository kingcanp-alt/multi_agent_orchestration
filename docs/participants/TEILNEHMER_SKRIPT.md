# Workshop Skript für Teilnehmer

## Ziel

- Ihr experimentiert mit drei Frameworks für den gleichen Multi Agent Workflow (Reader, Summarizer, Critic, Integrator) und versteht dadurch folgende Punkte:
- Was Multi Agent Orchestrierung ist und warum sie hilft
- Wie LangChain (Sequenziell), LangGraph (Graph) und DSPy (Deklarativ) sich unterscheiden
- Wie sich Code Anpassungen auf das Verhalten auswirken
- Wie ihr neue Nodes oder Signatures ergänzt

## Ablauf (60 Minuten)
1. Setup & Einführung (5-10 min)
2. LangChain: Pipeline ausführen, Prompts anpassen, Reihenfolge verstehen (12 min)
3. LangGraph: Graph prüfen, Node hinzufügen, Conditional Edge testen (15 min)
4. DSPy: Signatures anpassen, zusätzliche Inputs nutzen (15 min)
5. Vergleich & Fragen (3 min)

## Vorbereitungen
- Streamlit App per Doppelklick auf `launchers/run.*` starten oder manuell `python -m streamlit run app/app.py`
- Editor öffnen und folgende Dateien laden:
  - `app/agents/reader.py`
  - `app/agents/summarizer.py`
  - `app/agents/critic.py`
  - `app/workflows/langchain_pipeline.py`
  - `app/workflows/langgraph_pipeline.py`
  - `app/workflows/dspy_pipeline.py`
- Optional: `docs/participants/CODE_EXPERIMENTE.md` für schnelle Beispiele verwenden
- Testdokument hochladen (PDF oder TXT, 2-3 Seiten)

## Teil 1: LangChain verstehen
### Was passiert?
- Die Pipeline läuft strikt sequenziell: Reader → Summarizer → Critic → Integrator
- Jeder Agent führt sich erst aus, wenn der vorherige fertig ist
- Abhängigkeiten entstehen durch die Reihenfolge, nicht durch explizite Verbindungen

### Aufgabe: Prompt ändern
- Öffnet `app/agents/summarizer.py` und sucht den Prompt Text (ca. Zeile 9)
- Ändert die Anweisung, z. B. „very brief summary (50-100 words)“ statt „200-300 words“
- Speichert die Datei und führt LangChain erneut aus
- Beobachtet, wie sich die Summary Länge verändert

### Aufgabe: Critic Rubric erweitern
- Öffnet `app/agents/critic.py`
- Fügt unter der Rubric eine neue Kategorie hinzu, z. B. `Clarity` oder `Relevance`
- Ergänzt dafür auch den Abschnitt `OUTPUT FORMAT`, damit der Critic den neuen Score liefert
- Startet die Pipeline neu und schaut, welche Werte ausgegeben werden

### Aufgabe: Reihenfolge testen
- Öffnet `app/workflows/langchain_pipeline.py`
- Macht den Critic Aufruf vor den Summarizer (Summary Parameter zunächst leer)
- Startet die Pipeline und beobachtet, warum das nicht funktioniert oder welche Fehlermeldung erscheint
- Das zeigt, warum die Reihenfolge wichtig ist

## Teil 2: LangGraph erweitern
### Struktur ansehen
- LangGraph definiert Nodes und Edges in `app/workflows/langgraph_pipeline.py`
- Ihr seht, wie Inputs, Reader, Summarizer, Critic und Integrator verknüpft sind

### Aufgabe: Translator Node einfügen
1. PipelineState um ein Feld `summary_de` erweitern
2. Neue Funktion `_execute_translator_node`, die `summary` auf Deutsch simuliert
3. Node zum Graph mit `graph.add_node("translator", ...)` hinzufügen
4. Edges ändern:
   - `graph.add_edge("summarizer", "translator")`
   - `graph.add_edge("translator", "critic")`
5. Graph starten und prüfen:
   - Der neue Node sollte im Visual Tab auftauchen
   - Die Ausgabe zeigt `summary_de`

### Aufgabe: Conditional Edge testen
- Fügt eine Funktion `should_skip_quality(state)` hinzu (z. B. Summary kürzer als 100 Zeichen)
- Ersetzt `graph.add_edge("critic", "quality")` durch `graph.add_conditional_edges("critic", should_skip_quality)`
- Verbindet `quality` und `judge` weiterhin normal
- Bei kurzen Summaries sollte der Graph direkt zu `judge` springen

## Teil 3: DSPy anpassen
### Signatures variieren
- DSPy nutzt `dspy.Signature`, z. B. `class Summarize(dspy.Signature)`
- Ändert die Beschreibung (Short Summary, Fokus auf Results etc.) und beobachtet, wie DSPy den Prompt automatisch anpasst

### Zusätzlichen Input ergänzen
- Fügt `TARGET_LENGTH` als InputField hinzu (`short`, `medium`, `long`)
- In der `forward`-Methode den Parameter berücksichtigen und an `self.gen` übergeben
- In der Pipeline (`PaperPipeline.forward`) z. B. `self.summarizer(notes, "short")` aufrufen
- Startet DSPy und seht, wie die Länge gesteuert werden kann

## Teil 4: Zusammenfassung & Vergleich
- Vergleicht die drei Pipelines in der App mit verschiedenen Dokumenten
- Diskutiert:
  - Welche Pipeline ist einfacher zu verstehen?
  - Wo ist mehr Kontrolle nötig?
  - Wo lohnt sich automatische Optimierung?
- Dokumentiert wichtige Erkenntnisse und Fragen

## Fragen & Hilfe
- Nutzt `logs/telemetry.csv` (falls vorhanden) oder den Telemetry Tab für Laufzeiten
- Falls die App hängt: Strg+C im Terminal und neu starten
- Für Code Beispiele: `docs/participants/CODE_EXPERIMENTE.md`
