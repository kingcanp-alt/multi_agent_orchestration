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
3. LangGraph: Graph prüfen, Conditional Edge testen, Schwellenwerte anpassen (15 min)
4. DSPy: Signatures anpassen, Teleprompting verstehen (15 min)
5. Vergleich & Fragen (3 min)

## Vorbereitungen
- Streamlit App per Doppelklick auf `scripts/launchers/run.*` starten oder manuell `python -m streamlit run app/app.py`
- Editor öffnen und folgende Dateien laden:
  - `app/agents/reader.py`
  - `app/agents/summarizer.py`
  - `app/agents/critic.py`
  - `app/workflows/langchain_pipeline.py`
  - `app/workflows/langgraph_pipeline.py`
  - `app/workflows/dspy_pipeline.py`
- Optional: `docs/participants/CODE_EXPERIMENTE.md` für schnelle Beispiele verwenden
- Testdokument hochladen (PDF oder TXT, 2-3 Seiten)

---

## Teil 1: LangChain verstehen

### Was passiert?
- Die Pipeline läuft strikt sequenziell: Reader → Summarizer → Critic → Integrator
- Jeder Agent führt sich erst aus, wenn der vorherige fertig ist
- Abhängigkeiten entstehen durch die Reihenfolge, nicht durch explizite Verbindungen
- Die Funktion `run_pipeline` in `app/workflows/langchain_pipeline.py` steuert den Ablauf

### Aufgabe 1: Prompt ändern
- Öffnet `app/agents/summarizer.py` und sucht `SUMMARIZER_PROMPT` (ca. Zeile 11)
- Der Prompt ist als Template definiert. Ändert z. B. die Anweisung in Zeile 12:
  - Statt "Produce a concise scientific summary" → "Produce a very brief scientific summary (max 100 words)"
  - Oder: "Produce a detailed scientific summary (300-500 words)"
- Speichert die Datei und führt LangChain erneut aus
- Beobachtet, wie sich die Summary Länge verändert

### Aufgabe 2: Critic Rubric erweitern
- Öffnet `app/agents/critic.py`
- Sucht `CRITIC_PROMPT` (ca. Zeile 13)
- Die Rubric hat aktuell 4 Kategorien: "Makes sense", "Accuracy", "Coverage", "Details" (Zeilen 22-25)
- Fügt eine neue Kategorie hinzu, z. B. "Clarity" oder "Relevance"
- Ergänzt dafür auch den Abschnitt `OUTPUT FORMAT` (Zeilen 26-30), damit der Critic den neuen Score liefert
- Beispiel:
  ```
  "SCORING (0-5 integers):\n"
  "- Makes sense: logical flow, no contradictions.\n"
  "- Accuracy: claims supported by NOTES.\n"
  "- Coverage: objective covered, method covered, results covered, limitations covered.\n"
  "- Details: important details included.\n"
  "- Clarity: clear and easy to understand.\n\n"  # NEU
  "OUTPUT FORMAT:\n"
  "Makes sense: <0-5>\n"
  "Accuracy: <0-5>\n"
  "Coverage: <0-5>\n"
  "Details: <0-5>\n"
  "Clarity: <0-5>\n"  # NEU
  ```
- Startet die Pipeline neu und schaut, welche Werte ausgegeben werden

### Aufgabe 3: Reihenfolge testen
- Öffnet `app/workflows/langchain_pipeline.py`
- Sucht die Funktion `run_pipeline` (Zeile 21)
- Die Reihenfolge ist: Reader (Zeile 47) → Summarizer (Zeile 54) → Critic (Zeile 60) → Integrator (Zeile 67)
- Versucht, den Critic-Aufruf VOR den Summarizer zu verschieben (Summary Parameter zunächst leer setzen)
- Startet die Pipeline und beobachtet, warum das nicht funktioniert oder welche Fehlermeldung erscheint
- Das zeigt, warum die Reihenfolge wichtig ist

### Aufgabe 4: Reader Prompt anpassen
- Öffnet `app/agents/reader.py`
- Sucht `READER_PROMPT` (ca. Zeile 11)
- Der Prompt extrahiert strukturierte Notizen. Ändert z. B. die Anweisung für "Results" (Zeile 20-21)
- Testet, ob sich die extrahierten Metriken ändern

---

## Teil 2: LangGraph erweitern

### Struktur ansehen
- LangGraph definiert Nodes und Edges in `app/workflows/langgraph_pipeline.py`
- Die Funktion `_build_langgraph_workflow` (Zeile 297) zeigt die Graph-Struktur
- Nodes: retriever, reader, summarizer, critic_node, integrator
- Conditional Edge: `_critic_post_path` entscheidet, ob zurück zum Summarizer oder weiter zum Integrator

### Aufgabe 1: Conditional Flow verstehen
- Öffnet `app/workflows/langgraph_pipeline.py`
- Sucht die Funktion `_critic_post_path` (Zeile 185)
- Diese Funktion entscheidet basierend auf `critic_score` und `critic_loops`:
  - Wenn `critic_score < 0.5` und `loops < max_loops` → zurück zum Summarizer
  - Sonst → weiter zum Integrator
- Der Schwellenwert ist aktuell `0.5` (Zeile 208)
- Ändert den Schwellenwert auf `0.7` oder `0.3` und beobachtet, wie sich das Verhalten ändert
- Testet mit verschiedenen Dokumenten

### Aufgabe 2: Max Loops anpassen
- In `_critic_post_path` wird `max_critic_loops` aus der Config gelesen (Zeile 204)
- Standard ist 2 (siehe `app/app.py` Zeile 191)
- Ändert den Default in `app/app.py` auf 0 oder 3
- Startet LangGraph neu und beobachtet, ob mehr/fewer Loops auftreten
- Die Visualisierung zeigt die Loops im Graph

### Aufgabe 3: Graph Visualisierung ansehen
- Die Funktion `_generate_graph_visualization_dot` (Zeile 232) erstellt die Graph-Darstellung
- Sie zeigt die Nodes mit Timings und Scores
- Führt LangGraph aus und schaut euch den Graph im UI an
- Beobachtet, wie sich der Graph ändert, wenn ein Loop auftritt

### Aufgabe 4: Timeout anpassen
- Die Funktion `_execute_with_timeout` (Zeile 69) schützt vor hängenden LLM-Aufrufen
- Standard-Timeout ist 45 Sekunden (siehe `run_pipeline` Zeile 342)
- Ändert den Timeout auf 30 oder 60 Sekunden
- Testet mit einem sehr langen Dokument

---

## Teil 3: DSPy anpassen

### Signatures variieren
- DSPy nutzt `dspy.Signature`, z. B. `class Summarize(dspy.Signature)` in `app/workflows/dspy_pipeline.py` (Zeile 127)
- Die Signature beschreibt Input/Output, DSPy erzeugt automatisch den Prompt

### Aufgabe 1: Summarize Signature anpassen
- Öffnet `app/workflows/dspy_pipeline.py`
- Sucht `class Summarize` (Zeile 127)
- Die Beschreibung in der Docstring (Zeilen 128-132) steuert, wie DSPy den Prompt erzeugt
- Ändert z. B. "Produce a concise scientific summary" zu "Produce a very brief summary (max 100 words)"
- Oder: "Produce a detailed summary focusing on methodology"
- Startet DSPy und beobachtet, wie sich der generierte Prompt ändert

### Aufgabe 2: Critique Signature erweitern
- Sucht `class Critique` (Zeile 136)
- Die Rubric ist in der Docstring definiert (Zeilen 137-147)
- Fügt eine neue Bewertungskategorie hinzu, z. B. "Clarity" oder "Relevance"
- Aktualisiert das Format entsprechend
- Testet, ob die neue Kategorie in der Ausgabe erscheint

### Aufgabe 3: Zusätzlichen Input ergänzen
- Sucht `class SummarizerM` (Zeile 185)
- Die `forward`-Methode (Zeile 197) nimmt aktuell nur `notes` oder `NOTES`
- Fügt einen Parameter `target_length: str = "medium"` hinzu
- Erweitert die `Summarize` Signature um ein InputField `TARGET_LENGTH`
- In der `forward`-Methode übergebt `target_length` an `self.gen`
- In `PaperPipeline.forward` (Zeile 235) könnt ihr dann `self.summarizer(NOTES=notes, TARGET_LENGTH="short")` aufrufen
- Startet DSPy und seht, wie die Länge gesteuert werden kann

### Aufgabe 4: Teleprompting verstehen
- DSPy kann Prompts automatisch optimieren mit Teleprompting
- Aktiviert "Enable Teleprompting" in der UI (Settings → DSPy)
- Stellt sicher, dass `dev-set/dev.jsonl` existiert
- Führt DSPy mit und ohne Teleprompting aus
- Vergleicht die Ergebnisse im "DSPy Optimization" Tab
- Beobachtet den F1-Gain und die Unterschiede in der Summary

### Aufgabe 5: Reader Signature anpassen
- Sucht `class ReadNotes` (Zeile 103)
- Die Docstring beschreibt, welche Felder extrahiert werden sollen
- Ändert z. B. die Anweisung für "Results" (Zeile 114-115)
- Testet, ob sich die extrahierten Notizen ändern

---

## Teil 4: Vergleich & Analyse

### Aufgabe 1: Laufzeit vergleichen
- Führt alle drei Pipelines mit demselben Dokument aus
- Nutzt den "Compare" Tab in der UI
- Vergleicht die Laufzeiten in der Tabelle
- Diskutiert: Welche Pipeline ist am schnellsten? Warum?

### Aufgabe 2: Qualität vergleichen
- Schaut euch die Critic-Scores für alle drei Pipelines an
- Vergleicht die Summaries und Meta-Summaries
- Diskutiert: Welche Pipeline produziert bessere Ergebnisse?

### Aufgabe 3: Telemetrie analysieren
- Öffnet den "CSV Telemetry Data" Expander in der UI
- Schaut euch die letzten Einträge an
- Analysiert die Laufzeiten pro Agent
- Identifiziert Bottlenecks

### Aufgabe 4: Code-Komplexität vergleichen
- Zählt die Zeilen in:
  - `langchain_pipeline.py` (ca. 136 Zeilen)
  - `langgraph_pipeline.py` (ca. 416 Zeilen)
  - `dspy_pipeline.py` (ca. 456 Zeilen)
- Diskutiert: Welche Pipeline ist am einfachsten zu verstehen? Welche bietet die meisten Möglichkeiten?

---

## Teil 5: Erweiterte Aufgaben (Optional)

### Aufgabe 1: Neuen Agent hinzufügen (LangChain)
- Erstellt eine neue Datei `app/agents/validator.py`
- Implementiert eine einfache Validierungsfunktion, die prüft, ob die Summary bestimmte Kriterien erfüllt
- Integriert sie in `langchain_pipeline.py` zwischen Summarizer und Critic
- Testet die neue Pipeline

### Aufgabe 2: Neuen Node hinzufügen (LangGraph)
- Fügt einen neuen Node in `langgraph_pipeline.py` hinzu, z. B. einen "Quality Check" Node
- Verbindet ihn im Graph zwischen Critic und Integrator
- Implementiert die Node-Funktion `_execute_quality_check_node`
- Aktualisiert `_build_langgraph_workflow` um den neuen Node
- Testet die neue Graph-Struktur

### Aufgabe 3: Neue Signature erstellen (DSPy)
- Erstellt eine neue Signature `class Validate(dspy.Signature)` in `dspy_pipeline.py`
- Implementiert ein `ValidatorM` Module
- Integriert es in `PaperPipeline`
- Testet die neue Pipeline

### Aufgabe 4: Error Handling verbessern
- Schaut euch `_create_error_response` in `langchain_pipeline.py` an (Zeile 115)
- Implementiert ähnliches Error Handling für LangGraph
- Testet mit leeren oder ungültigen Eingaben

---

## Zusammenfassung & Diskussion

- Vergleicht die drei Pipelines in der App mit verschiedenen Dokumenten
- Diskutiert:
  - Welche Pipeline ist einfacher zu verstehen?
  - Wo ist mehr Kontrolle nötig?
  - Wo lohnt sich automatische Optimierung?
  - Welche Trade-offs gibt es?
- Dokumentiert wichtige Erkenntnisse und Fragen

---

## Fragen & Hilfe

- Nutzt `telemetry.csv` (falls vorhanden) oder den Telemetry Tab für Laufzeiten
- Falls die App hängt: Strg+C im Terminal und neu starten
- Für Code Beispiele: `docs/participants/CODE_EXPERIMENTE.md`
- Bei Fehlern: Prüft die Terminal-Ausgabe für Fehlermeldungen
