# Code Experimente

Diese Datei liefert kurze Code Beispiele, die ihr direkt übernehmen oder anpassen könnt.

## 1. Summarizer kürzer oder länger machen
- Datei: `app/agents/summarizer.py`
- Sucht das Prompt in Zeile 10 und passt den Text an (z. B. „very brief“ oder „detailed“).
- Ergebnis: GPT erzeugt eine kürzere oder längere Zusammenfassung.

## 2. Critic um Klarheit erweitern
- Datei: `app/agents/critic.py`
- Erweitert die Rubric um „Clarity“ und schreibt das Ausgabeformat entsprechend neu.
- Ergebnis: Der Critic gibt zusätzlich einen Klarheitswert aus.

## 3. LangChain Reihenfolge testen
- Datei: `app/workflows/langchain_pipeline.py`
- Führt den Critic vor dem Summarizer aus (Summary als leere Zeichenkette).
- Ergebnis: Ihr seht, dass die Reihenfolge die Logik bricht und warum LangChain die Abhängigkeiten nicht automatisch steuert.

## 4. Translator Node zu LangGraph hinzufügen
- Datei: `app/workflows/langgraph_pipeline.py`
- a) PipelineState: neues Feld `summary_de` hinzufügen.
- b) Neue Funktion `_execute_translator_node`, die eine Dummy Übersetzung erstellt.
- c) Node zum Graph ergänzen und Kanten anpassen:
  - `graph.add_node("translator", _execute_translator_node)`
  - `graph.add_edge("summarizer", "translator")`
  - `graph.add_edge("translator", "critic")`
- Ergebnis: Der Graph zeigt den neuen Schritt und ihr seht ihn in der Visualisierung.

## 5. Conditional Edge in LangGraph
- Datei: `app/workflows/langgraph_pipeline.py`
- Neue Funktion `should_skip_quality(state)` entscheidet anhand der Summary Länge, ob `quality` übersprungen wird.
- Ersetzt `graph.add_edge("critic", "quality")` durch `graph.add_conditional_edges("critic", should_skip_quality)` und stellt sicher, dass `quality` und `judge` verbunden bleiben.
- Ergebnis: Kurze Summaries überspringen `quality`, der Graph verzweigt sich.

## 6. DSPy Signature variieren
- Datei: `app/workflows/dspy_pipeline.py`
- Passt die Beschreibung der `Summarize`-Signature an (z. B. „focused on RESULTS“, „very brief summary“).
- DSPy erstellt automatisch den Prompt neu.

## 7. Ziel Länge als Input für DSPy
- `Summarize`-Signature um `TARGET_LENGTH` erweitern (InputField mit Beschreibung).
- In den `forward`-Methoden `target_length` übergeben und in der Pipeline `self.summarizer(notes, "short")` nutzen.
- Ergebnis: Ihr steuert die Länge über einen Parameter.

## Tipps
1. Speichern, dann testen.
2. Bei Syntaxfehlern auf Einrückungen und Anführungszeichen achten.
3. App neu starten, wenn Änderungen nicht wirken.
4. Nur eine Änderung pro Test.
5. Backup der Original Dateien behalten.
