# Workshop-Skript für Teilnehmer
## Multi-Agent Workflow Orchestration mit LangChain, LangGraph & DSPy

Workshop-Dauer: 60 Minuten  
Voraussetzungen: Computer mit Browser, Zugriff auf die Streamlit-App und den Code

**Kurzer Überblick:** Ihr lernt drei Frameworks kennen und experimentiert direkt mit dem Code. Ihr ändert Prompts, fügt Nodes hinzu und seht, wie sich das Verhalten ändert. Das zeigt euch die Unterschiede zwischen den Frameworks praktisch.


### Was lernt ihr heute?

Am Ende des Workshops könnt ihr:
- **Verstehen**, was Multi-Agent Orchestration ist und warum man es braucht
- **Erklären**, wie LangChain, LangGraph und DSPy sich unterscheiden
- **Code anpassen** in allen drei Frameworks und die Auswirkungen sehen
- **Entscheiden**, welches Framework für welchen Use Case passt
- **Einen neuen Node** zu LangGraph hinzufügen
- **Signatures** in DSPy anpassen
- **Prompts** in LangChain/LangGraph ändern

**Wie lernt ihr das?** Nicht nur durch Zuhören, sondern durch praktische Experimente. Ihr ändert Code, seht sofort die Auswirkungen, und versteht dadurch die Unterschiede viel besser als durch reine Theorie.

**Warum ist das wichtig?** In der Praxis müsst ihr entscheiden, welches Framework ihr für ein Projekt nutzt. Durch die praktischen Experimente versteht ihr die Trade-offs besser.

---

## Workshop-Plan (Überblick)

- **5 Min:** Setup - App öffnen, Code vorbereiten
- **10 Min:** Einführung - Konzepte verstehen
- **12 Min:** LangChain - Sequenzielle Pipeline, Prompts ändern
- **15 Min:** LangGraph - Graph-Pipeline, neue Nodes hinzufügen  
- **15 Min:** DSPy - Deklarative Pipeline, Signatures anpassen
- **3 Min:** Vergleich und Abschluss

---

## Vor dem Start (5 Minuten)

### App öffnen und Code vorbereiten

Öffnet die Streamlit-App im Browser. Falls ihr lokal arbeitet, startet `streamlit run app.py` im Terminal. Die App öffnet sich automatisch unter http://localhost:8501.

Öffnet die Code-Dateien in eurem Editor:
- `agents/reader.py` - Reader-Agent
- `agents/summarizer.py` - Summarizer-Agent
- `agents/critic.py` - Critic-Agent
- `workflows/langchain_pipeline.py` - LangChain Pipeline
- `workflows/langgraph_pipeline.py` - LangGraph Pipeline
- `workflows/dspy_pipeline.py` - DSPy Pipeline

Falls ihr keinen Code-Zugriff habt, nutzt die App ohne Code-Änderungen. Die Aufgaben mit Code sind optional, aber empfehlenswert, um die Unterschiede wirklich zu verstehen.

**Tipp:** Falls ihr Hilfe beim Code-Ändern braucht, schaut in `CODE_EXPERIMENTE.md` - dort sind alle Code-Snippets zum Kopieren vorbereitet.

Ladet ein Testdokument hoch (2-3 Seiten PDF oder TXT).

---

## Teil 1: Einführung (10 Minuten)

### Was ist Multi-Agent Orchestration?

Multi-Agent Orchestration bedeutet die strukturierte Koordination mehrerer LLM-Agenten in einer Pipeline. Statt eines einzelnen großen Prompts wird die Aufgabe auf spezialisierte Agenten verteilt.

**Warum macht man das?** Ein einzelner großer Prompt ist oft schwer zu kontrollieren und zu debuggen. Wenn man die Aufgabe aufteilt, kann jeder Agent sich auf eine Sache konzentrieren. Das ist wie in einer Fabrik: Jeder Arbeiter macht einen spezifischen Schritt, am Ende kommt ein fertiges Produkt heraus. Ein einzelner Arbeiter, der alles macht, ist weniger effizient.

**Das Beispiel-System:** Ein Research Paper Analyzer, der wissenschaftliche Paper analysiert. Statt einem großen Prompt "Analysiere dieses Paper" nutzt er vier spezialisierte Agenten:
- **Reader:** Extrahiert strukturierte Notizen aus dem Dokument. Dieser Agent konzentriert sich darauf, wichtige Informationen (Methoden, Ergebnisse, etc.) herauszuziehen und in einem strukturierten Format zu organisieren.
- **Summarizer:** Erstellt eine Zusammenfassung aus den Notizen. Dieser Agent nimmt die strukturierten Notizen und formuliert sie in einen lesbaren Text um.
- **Critic:** Bewertet die Qualität der Summary. Dieser Agent prüft, ob die Summary korrekt ist, vollständig ist, und ob sie die wichtigsten Punkte abdeckt.
- **Integrator:** Erstellt eine finale Meta-Summary, die alles zusammenführt. Dieser Agent kombiniert Summary und Critic-Bewertung zu einem finalen Ergebnis.

### Warum drei verschiedene Frameworks?

Die drei Frameworks unterscheiden sich grundlegend in ihrem Ansatz:

- **LangChain:** Sequenziell und einfach zu verwenden. Wie eine Kette: Schritt 1, dann Schritt 2, dann Schritt 3. Einfach zu verstehen, aber nicht sehr flexibel. Gut für schnelle Prototypen.

- **LangGraph:** Graph-basierte Struktur für Transparenz. Wie ein Flussdiagramm: Ihr seht genau, wie die Daten fließen, welche Schritte wann ausgeführt werden. Höhere Flexibilität, könnt Nodes hinzufügen, Conditional Logic nutzen. Gut für komplexe Workflows.

- **DSPy:** Deklarativ und selbstoptimierend. Ihr beschreibt nur, was erreicht werden soll, nicht wie. Das Framework findet automatisch die besten Prompts. Gut für Optimierung und Reproduzierbarkeit.

**Warum ist das wichtig?** Jeder Ansatz hat Vor- und Nachteile. Im Workshop seht ihr durch praktische Experimente, wann welcher Ansatz sinnvoll ist.

---

## Teil 2: LangChain Sequential Pipeline (12 Minuten)

### Aufgabe 2.1: Pipeline ausführen und verstehen

**Schwierigkeitsgrad: Einfach**

**Was macht ihr?** Ihr führt die LangChain-Pipeline aus und schaut euch an, wie sie im Code strukturiert ist.

**Schritt 1: Pipeline ausführen**
Führt die LangChain-Pipeline in der App aus: Wählt "LangChain" als Pipeline in der Sidebar, klickt auf "Starten", beobachtet die Ergebnisse.

**Was passiert?** Die App lädt euer Dokument, sendet es an die Pipeline, und die Pipeline führt die vier Agenten nacheinander aus. Ihr seht die Ergebnisse in verschiedenen Tab-Reitern: Strukturierte Notizen, Summary, Critic-Bewertung, und finale Meta-Summary.

**Schritt 2: Code verstehen**
Öffnet `workflows/langchain_pipeline.py` und schaut euch die Funktion `run_pipeline` an (Zeilen 17-81).

**Was ihr seht:**
Die Pipeline führt die Agenten sequenziell aus:
```python
structured_notes = run_reader(analysis_context)
summary = run_summarizer(structured_notes)
critic_result = run_critic(notes=structured_notes, summary=summary)
meta_summary = run_integrator(notes=structured_notes, summary=summary, critic=critic_text)
```

**Wie funktioniert das?**
- Der Code ruft `run_reader()` mit dem Dokument-Text auf und bekommt strukturierte Notizen zurück
- Der Code übergibt diese Notizen an `run_summarizer()`, der eine Summary erstellt
- Der Code übergibt Notizen und Summary an `run_critic()`, der die Qualität bewertet
- Der Code übergibt alles (Notizen, Summary, Critic) an `run_integrator()`, der die finale Meta-Summary erstellt

**Warum ist das wichtig?** Jeder Schritt wartet auf den vorherigen. Das ist einfach zu verstehen - es ist wie ein Rezept: Zuerst kochst du die Nudeln, dann machst du die Sauce, dann mischt du alles zusammen. Aber es ist auch limitiert: Du kannst nicht die Sauce anfangen, bevor die Nudeln fertig sind, auch wenn sie unabhängig voneinander sind.

**Was ist der Nachteil?** Wenn ein Schritt fehlschlägt, bricht die ganze Pipeline ab. Es gibt keine Möglichkeit für Conditional Logic (z.B. "wenn Critic schlecht bewertet, wiederhole Summarizer"). Und die Abhängigkeiten sind implizit - ihr seht sie nicht explizit im Code.

### Aufgabe 2.2: Agenten-Prompts anpassen

**Schwierigkeitsgrad: Mittel**

**Was macht ihr?** Ihr ändert einen Prompt direkt im Code und seht sofort die Auswirkung. Das zeigt euch, wie einfach es ist, LangChain-Pipelines anzupassen.

**Was ist ein Prompt?** Ein Prompt ist die Anweisung, die dem LLM gegeben wird. Das ist wie eine Aufgabe, die ihr einem Mitarbeiter stellt: "Schreibe eine Zusammenfassung von 200-300 Wörtern" ist anders als "Schreibe eine kurze Zusammenfassung von 50-100 Wörtern". Der LLM führt die Anweisung aus, und das Ergebnis ist entsprechend unterschiedlich.

**Schritt 1: Prompt finden**
Öffnet `agents/summarizer.py`. Schaut euch den `SUMMARIZER_PROMPT` an (Zeile 9-15).

**Was steht da?** Der Prompt ist in einer Variable gespeichert. Er sagt dem LLM: "Erstelle eine wissenschaftliche Zusammenfassung von 200-300 Wörtern aus den strukturierten Notizen. Deckt ab: Objective, Method, Results, Limitations, Takeaways."

**Schritt 2: Prompt ändern**
Ändert die Wortanzahl-Anforderung im Prompt. Aktuell steht dort:
```
"Produce a concise scientific summary (200-300 words)"
```

Ändert es zu:
```
"Produce a very brief scientific summary (50-100 words)"
```

**Warum ändern wir das?** Um zu sehen, wie die Ausgabe sich ändert. Wenn wir die Wortanzahl reduzieren, sollte die Summary kürzer werden. Das zeigt euch, dass ihr direkt die Prompts kontrollieren könnt.

**Schritt 3: Speichern und Testen**
Speichert die Datei. 

**Wichtig:** Die App lädt Code-Änderungen automatisch neu, aber manchmal dauert das ein paar Sekunden. Falls die Änderung nicht sichtbar wird:
1. Wartet 10 Sekunden und führt die Pipeline erneut aus
2. Falls immer noch nicht: Startet die App neu (im Terminal Strg+C, dann `streamlit run app.py`)
3. Falls lokal: Prüft, ob Python die Datei neu geladen hat (manche Editoren speichern nicht automatisch)

Führt die Pipeline nochmal aus mit demselben Dokument. 

**Was hat sich geändert?** Die Summary sollte deutlich kürzer sein. Warum? Weil der LLM jetzt die Anweisung hat, nur 50-100 Wörter zu schreiben statt 200-300. Das zeigt euch: In LangChain kontrolliert ihr die Prompts direkt. Was im Prompt steht, bestimmt, was der LLM macht.

**Was lernt ihr daraus?** LangChain ist einfach anpassbar. Ihr ändert den Prompt, speichert, und die Änderung wirkt sich sofort aus. Das ist der Vorteil von expliziten Prompts - ihr seht genau, was passiert, und könnt es direkt kontrollieren.

**Schwierigkeitsgrad: Schwer - Critic-Rubric erweitern**

**Was ist ein Rubric?** Ein Rubric ist eine Bewertungsmatrix. Stellt euch vor, ihr bewertet eine Hausarbeit: Ihr habt Kategorien wie "Inhalt", "Struktur", "Sprache" und vergibt Punkte von 0-5 für jede Kategorie. Genau das macht der Critic-Agent - er bewertet die Summary nach verschiedenen Kategorien.

**Was macht ihr?** Ändert den Critic-Prompt in `agents/critic.py`. Der Critic bewertet aktuell nach einem Rubric mit vier Kategorien: Coherence, Groundedness, Coverage, Specificity. Ihr fügt eine fünfte Kategorie hinzu: Clarity (Klarheit).

**Warum?** Um zu sehen, dass ihr die Bewertungskriterien selbst definieren könnt. Wenn euch eine andere Kategorie wichtig ist, könnt ihr sie einfach hinzufügen.

**Schritt-für-Schritt:**
1. Findet die Zeile mit "RUBRIC (0-5 integers):" (Zeile 13). Das ist die Definition des Bewertungsschemas.
2. Fügt eine neue Kategorie hinzu, z.B.:
```
"- Clarity: how easy is it to understand.\n"
```
Das fügt eine neue Bewertungskategorie hinzu.

3. Fügt auch die Ausgabe hinzu (Zeile 19-22). Dort steht, was der LLM ausgeben soll:
```
"Clarity: <0-5>\n"
```
Das sagt dem LLM, dass es auch einen Clarity-Score ausgeben soll.

4. Speichert und führt die Pipeline aus.

**Was seht ihr?** In der Critic-Ausgabe sollte jetzt auch "Clarity: X" stehen, wobei X eine Zahl von 0-5 ist. Das zeigt euch, dass ihr die Bewertungskriterien selbst definieren könnt.

### Aufgabe 2.3: Reihenfolge ändern - Abhängigkeiten verstehen

**Schwierigkeitsgrad: Mittel**

**Was macht ihr?** Ihr ändert die Reihenfolge der Agenten-Aufrufe und seht, was passiert. Das zeigt euch die impliziten Abhängigkeiten in LangChain.

**Was sind Abhängigkeiten?** Abhängigkeiten bedeuten, dass ein Agent die Ausgabe eines anderen Agenten braucht. Der Summarizer braucht die Notes vom Reader. Der Critic braucht sowohl Notes als auch Summary. Das ist wie beim Kochen: Ihr könnt nicht den Kuchen backen, bevor ihr den Teig gemacht habt.

**Warum ist das wichtig?** In LangChain seht ihr diese Abhängigkeiten nicht explizit. Sie sind nur implizit durch die Reihenfolge der Aufrufe gegeben. Wenn ihr die Reihenfolge ändert, kann es kaputt gehen, aber LangChain warnt euch nicht davor.

**Schritt 1: Aktuelle Reihenfolge verstehen**
Öffnet `workflows/langchain_pipeline.py`. Findet die Zeilen 33-52, wo die Agenten aufgerufen werden.

Aktuell ist die Reihenfolge: Reader → Summarizer → Critic → Integrator

**Warum diese Reihenfolge?**
- Reader braucht nur das Dokument
- Summarizer braucht die Notes vom Reader
- Critic braucht Notes UND Summary
- Integrator braucht Notes, Summary UND Critic-Bewertung

**Schritt 2: Reihenfolge ändern (Experiment)**
Was passiert, wenn ihr Critic vor Summarizer ausführt? Ändert die Zeilen so:
```python
critic_result = run_critic(notes=structured_notes, summary="")  # Leere Summary
summary = run_summarizer(structured_notes)
meta_summary = run_integrator(...)
```

**Was macht ihr?** Ihr ruft den Critic mit einer leeren Summary auf. Der Critic kann dann keine sinnvolle Bewertung machen, weil er keine Summary zum Bewerten hat.

**Schritt 3: Pipeline ausführen**
Führt die Pipeline aus. Was passiert?

**Was seht ihr?** Die Pipeline läuft, aber die Critic-Bewertung ist sinnlos, weil sie auf einer leeren Summary basiert. Der Critic kann nicht richtig bewerten, wenn er keine Summary hat.

**Warum funktioniert das nicht richtig?** Die Agenten haben Abhängigkeiten, die in LangChain nicht explizit definiert sind. LangChain zeigt euch nicht, dass der Critic die Summary braucht - ihr müsst es selbst wissen. Wenn ihr die Reihenfolge ändert, kann es kaputt gehen, aber ihr bekommt keine Warnung.

**Was lernt ihr daraus?** Das ist ein Nachteil von LangChain: Die Abhängigkeiten sind implizit. In LangGraph werdet ihr sehen, dass die Abhängigkeiten explizit durch Edges definiert sind - dann könnt ihr so einen Fehler nicht so leicht machen.

---

## Teil 3: LangGraph Multi-Agent Workflow (15 Minuten)

### Aufgabe 3.1: Graph-Pipeline verstehen

**Schwierigkeitsgrad: Einfach**

**Was macht ihr?** Ihr führt die LangGraph-Pipeline aus und seht die Graph-Visualisierung. Dann schaut ihr euch an, wie der Graph im Code definiert ist.

**Was ist ein Graph?** Ein Graph ist eine visuelle Darstellung von Knoten (Nodes) und Verbindungen (Edges). Stellt euch vor, ihr plant eine Reise: Die Städte sind die Nodes, die Straßen sind die Edges. Genau so funktioniert LangGraph: Die Agenten sind Nodes, die Verbindungen zwischen ihnen sind Edges.

**Warum ist das besser?** Ihr seht genau, wie die Daten fließen. In LangChain seht ihr das nicht - da ist es nur eine Liste von Funktionsaufrufen. In LangGraph seht ihr die Struktur visuell.

**Schritt 1: Pipeline ausführen**
Führt die LangGraph-Pipeline in der App aus. Wählt "LangGraph" als Pipeline, klickt auf "Starten".

**Was passiert?** Die Pipeline läuft, und ihr seht die Graph-Visualisierung. Das ist ein Diagramm, das zeigt: Input → Retriever → Reader → Summarizer → Critic → Quality → Judge → Integrator → Output.

**Schritt 2: Code verstehen**
Öffnet `workflows/langgraph_pipeline.py`. Schaut euch die Funktion `_build_langgraph_workflow` an (Zeilen 186-204).

**Was ihr seht:**
Der Graph wird explizit aufgebaut:
```python
graph = StateGraph(PipelineState)
graph.add_node("reader", _execute_reader_node)
graph.add_node("summarizer", _execute_summarizer_node)
graph.add_edge("reader", "summarizer")
```

**Was bedeutet das?**
- `StateGraph(PipelineState)`: Erstellt einen Graph mit einem State-Objekt. Der State enthält alle Daten, die zwischen den Nodes fließen (Notes, Summary, etc.).
- `graph.add_node("reader", _execute_reader_node)`: Fügt einen Node hinzu. "reader" ist der Name, `_execute_reader_node` ist die Funktion, die ausgeführt wird.
- `graph.add_edge("reader", "summarizer")`: Fügt eine Verbindung hinzu. Das bedeutet: Nach dem Reader kommt der Summarizer.

**Warum ist das wichtig?** Die Struktur ist explizit sichtbar. Ihr könnt sehen, welche Nodes es gibt und wie sie verbunden sind. Das macht es einfacher zu verstehen, zu debuggen und zu erweitern.

**Was ist der Unterschied zu LangChain?** In LangChain sind die Abhängigkeiten implizit - ihr seht sie nur durch die Reihenfolge der Aufrufe. In LangGraph sind sie explizit - jede Edge zeigt eine Abhängigkeit an. Das macht es unmöglich, die Reihenfolge falsch zu machen (die Edges bestimmen die Reihenfolge).

### Aufgabe 3.2: Neuen Node hinzufügen - Graph erweitern

**Schwierigkeitsgrad: Mittel**

**Was macht ihr?** Ihr fügt einen neuen Node zum Graph hinzu. Das zeigt euch, wie einfach es ist, LangGraph-Pipelines zu erweitern.

**Warum einen Translator?** Stellt euch vor, ihr wollt die Summary ins Deutsche übersetzen. In LangChain müsstet ihr eine neue Funktion schreiben und sie in die richtige Reihenfolge einfügen - und hoffen, dass ihr keine Abhängigkeiten kaputt macht. In LangGraph fügt ihr einfach einen Node hinzu und verbindet ihn mit Edges.

**Wie funktioniert das?** Ein Node ist eine Funktion, die den State als Input bekommt, etwas damit macht, den State aktualisiert, und den State zurückgibt. Der State ist wie ein gemeinsames Notizbuch - alle Nodes lesen daraus und schreiben hinein.

**Schritt 1: Node-Funktion erstellen**
Findet die Funktion `_build_langgraph_workflow` (Zeile 186). Erstellt eine neue Node-Funktion davor (z.B. nach Zeile 161):

```python
def _execute_translator_node(state: PipelineState) -> PipelineState:
    """Graph-Knoten: Übersetzt die Summary ins Deutsche."""
    start_time = perf_counter()
    timeout_seconds = state.get("_timeout", 45)
    
    # Einfacher Translator (könnt ihr später verbessern)
    summary_en = state.get("summary", "") or ""
    summary_de = summary_en + " [Übersetzt]"  # Platzhalter - später könnt ihr einen echten LLM-Call machen
    
    state["summary_de"] = summary_de
    return state
```

**Was macht diese Funktion?**
- Sie bekommt den State (enthält alle Daten der Pipeline)
- Sie liest die Summary aus dem State
- Sie "übersetzt" sie (erstmal nur ein Platzhalter)
- Sie schreibt die übersetzte Summary zurück in den State
- Sie gibt den State zurück

**Schritt 2: Node zum Graph hinzufügen**
In `_build_langgraph_workflow`, nach Zeile 195, fügt hinzu:
```python
graph.add_node("translator", _execute_translator_node)
```

**Was bedeutet das?** Ihr registriert den Node im Graph. Jetzt weiß der Graph, dass es einen "translator" Node gibt.

**Schritt 3: Edges anpassen - Graph-Struktur ändern**
Wo soll der Translator sein? Nach dem Summarizer, vor dem Critic.

**Entfernt die alte Edge:**
```python
# graph.add_edge("summarizer", "critic")  # Diese Zeile auskommentieren
```

**Fügt neue Edges hinzu:**
```python
graph.add_edge("summarizer", "translator")
graph.add_edge("translator", "critic")
```

**Was bedeutet das?** Jetzt ist der Graph: Summarizer → Translator → Critic. Die Edges bestimmen die Reihenfolge. Der Graph weiß jetzt: Nach dem Summarizer kommt der Translator, nach dem Translator kommt der Critic.

**Schritt 4: State erweitern**
Fügt das neue Feld zum PipelineState hinzu (Zeile 24-39):
```python
summary_de: str
```

**Warum?** Der State muss alle Felder definieren, die die Nodes verwenden. Wenn der Translator `summary_de` in den State schreibt, muss das Feld im State-Typ definiert sein.

**Schritt 5: Pipeline ausführen**
Führt die Pipeline aus. Seht ihr den neuen Translator-Node im Graph?

**Was seht ihr?** In der Graph-Visualisierung sollte jetzt zwischen Summarizer und Critic der Translator erscheinen. Das zeigt euch, dass ihr die Struktur erfolgreich erweitert habt.

**Was lernt ihr daraus?** In LangGraph ist es einfach, neue Nodes hinzuzufügen. Ihr müsst nur: 1) Node-Funktion schreiben, 2) Node registrieren, 3) Edges anpassen, 4) State erweitern. Die Struktur ist explizit - ihr seht genau, wo der neue Node ist und wie er mit den anderen verbunden ist.

**Tipp:** Falls es Fehler gibt, prüft die Syntax. Der State muss alle Felder enthalten, die die Nodes verwenden. Und alle Edges müssen zu existierenden Nodes führen.

**Schwierigkeitsgrad: Schwer**

Macht den Translator richtig funktionsfähig. Nutzt einen LLM-Call wie die anderen Agenten. Schaut euch `_execute_summarizer_node` als Beispiel an (Zeile 78-85).

### Aufgabe 3.3: Conditional Edge hinzufügen

**Schwierigkeitsgrad: Schwer**

LangGraph erlaubt Conditional Edges - der Graph verzweigt sich basierend auf Bedingungen.

Findet die Zeile mit `graph.add_edge("critic", "quality")` (Zeile 200).

Statt einer direkten Edge könnt ihr eine Conditional Edge erstellen, die nur bei schlechter Qualität zum Integrator geht:

1. Erstellt eine Routing-Funktion (vor `_build_langgraph_workflow`):
```python
def should_repeat_critic(state: PipelineState) -> str:
    """Entscheidet, ob Critic wiederholt werden soll."""
    critic_text = state.get("critic", "") or ""
    
    # Einfache Bedingung: Wenn "Improvements:" im Critic-Text steht, wiederhole
    if "Improvements:" in critic_text and len(critic_text) > 100:
        return "repeat_critic"  # Zurück zum Critic
    else:
        return "quality"  # Weiter zu Quality
```

2. Ändert die Edge zu Conditional (in `_build_langgraph_workflow`, statt Zeile 200):
```python
graph.add_conditional_edges("critic", should_repeat_critic)
```

3. Fügt die entsprechenden Edges hinzu:
```python
graph.add_edge("repeat_critic", "critic")  # Zurück zum Critic
graph.add_edge("quality", "judge")  # Normale Route
```

Führt die Pipeline aus. Was passiert? Seht ihr, wie der Graph sich verzweigt?

**Tipp:** Conditional Edges sind mächtig, aber komplex. Startet mit einfachen Bedingungen.

---

## Teil 4: Unterschiede zwischen LangChain und LangGraph (10 Minuten)

### Aufgabe 4.1: Code-Vergleich - Warum ist LangGraph komplexer?

**Schwierigkeitsgrad: Mittel**

**Was macht ihr?** Ihr vergleicht die beiden Pipeline-Dateien direkt und versteht, warum LangGraph mehr Code hat, aber auch mächtiger ist.

**Warum vergleichen?** Beide Frameworks machen dasselbe - sie führen die gleichen Agenten aus. Aber wie sie es tun, ist unterschiedlich. Durch den Vergleich seht ihr die Trade-offs.

**Code-Vergleich:**

**LangChain** (`workflows/langchain_pipeline.py`, Zeilen 33-52):
```python
structured_notes = run_reader(analysis_context)
summary = run_summarizer(structured_notes)
critic_result = run_critic(notes=structured_notes, summary=summary)
meta_summary = run_integrator(notes=structured_notes, summary=summary, critic=critic_text)
```
- Einfache Funktionsaufrufe nacheinander - wie ein Rezept: Schritt 1, dann Schritt 2, dann Schritt 3
- Keine explizite Struktur - die Struktur ist implizit durch die Reihenfolge der Aufrufe gegeben
- Keine Fehlerbehandlung zwischen Schritten - wenn ein Schritt fehlschlägt, bricht die Pipeline ab
- Keine Möglichkeit für Conditional Logic - ihr könnt nicht sagen "wenn Kritik schlecht, wiederhole Summarizer"

**Warum ist das einfach?** Weniger Code, leichter zu verstehen. Ihr seht direkt, was passiert. Aber es ist auch limitiert - ihr könnt nicht viel kontrollieren.

**LangGraph** (`workflows/langgraph_pipeline.py`, Zeilen 186-204):
```python
graph = StateGraph(PipelineState)
graph.add_node("reader", _execute_reader_node)
graph.add_node("summarizer", _execute_summarizer_node)
graph.add_edge("reader", "summarizer")
```
- Expliziter Graph mit Nodes und Edges - die Struktur ist sichtbar und modifizierbar
- State wird explizit verwaltet - alle Daten werden in einem State-Objekt gespeichert, das zwischen Nodes fließt
- Timeout-Handling pro Node (Zeile 42-53) - jeder Node hat sein eigenes Timeout, falls etwas hängt
- Möglichkeit für Conditional Edges - ihr könnt den Graph verzweigen lassen basierend auf Bedingungen

**Warum ist das komplexer?** Mehr Code, mehr Konzepte (Graph, Nodes, Edges, State). Aber es ist auch mächtiger - ihr habt mehr Kontrolle und könnt komplexere Workflows bauen.

**Was ist der Trade-off?** Einfachheit vs. Mächtigkeit. LangChain ist einfacher, aber limitiert. LangGraph ist komplexer, aber flexibler.

**Was ist der Hauptunterschied?**

Öffnet beide Dateien nebeneinander. In LangChain seht ihr einfach:
```python
structured_notes = run_reader(analysis_context)
summary = run_summarizer(structured_notes)
```

In LangGraph seht ihr:
```python
graph.add_node("reader", _execute_reader_node)
graph.add_edge("reader", "summarizer")
```

Der Graph ist explizit definiert. Ihr könnt ihn visualisieren, modifizieren, erweitern.

### Aufgabe 4.2: Quality und Judge Nodes

**Schwierigkeitsgrad: Einfach**

Schaut euch die Quality- und Judge-Nodes in LangGraph an (Zeilen 113-148). Diese gibt es in LangChain nicht.

**Warum nicht?**

In LangChain müsstet ihr diese manuell nach dem Critic einfügen:
```python
# Das würde in LangChain so aussehen:
critic_result = run_critic(...)
quality_f1 = calculate_quality(notes, summary)  # Manuell
judge_score = get_judge_score(notes, summary)  # Manuell
meta_summary = run_integrator(...)
```

In LangGraph sind sie einfach Nodes im Graph. Ihr seht sie in der Visualisierung. Diese sind Teil der Struktur.

**Experiment:** Kommentiert die Quality- und Judge-Nodes in LangGraph aus (Zeilen 193-194 und 200-201 auskommentieren). Was passiert mit dem Graph?

---

## Teil 5: DSPy Self-Improving Pipeline (15 Minuten)

### Aufgabe 5.1: DSPy Base ausführen und Code verstehen

**Schwierigkeitsgrad: Einfach**

**Was macht ihr?** Ihr führt DSPy aus und versteht das deklarative Paradigma.

**Was ist deklarativ?** Deklarativ bedeutet "beschreibend". Ihr beschreibt nur, was erreicht werden soll, nicht wie. Das ist wie SQL: Ihr sagt "Zeige mir alle Kunden aus Berlin", aber ihr sagt nicht, wie die Datenbank das machen soll. Genau so funktioniert DSPy: Ihr beschreibt das Input und Output, aber nicht den exakten Prompt.

**Warum ist das anders?** In LangChain und LangGraph habt ihr gesehen, dass ihr explizite Prompts schreibt. In DSPy schreibt ihr nur Signatures - eine Beschreibung von Input und Output. DSPy generiert automatisch die besten Prompts basierend auf der Signature.

**Schritt 1: Pipeline ausführen**
Führt DSPy ohne Teleprompting in der App aus. Wählt "DSPy" als Pipeline, stellt sicher, dass "DSPy optimieren" deaktiviert ist, klickt auf "Starten".

**Was passiert?** Die Pipeline läuft ähnlich wie LangChain/LangGraph, aber im Hintergrund nutzt DSPy automatisch generierte Prompts.

**Schritt 2: Code verstehen - Signatures**
Öffnet `workflows/dspy_pipeline.py`. DSPy nutzt Signatures statt expliziter Prompts.

Schaut euch die Signatures an (Zeilen 80-104):
```python
class ReadNotes(dspy.Signature):
    """Return structured scientific notes from TEXT as per schema."""
    TEXT: str = dspy.InputField()
    NOTES: str = dspy.OutputField(desc="Structured notes per schema")
```

**Was bedeutet das?**
- `class ReadNotes(dspy.Signature)`: Definiert eine Signature. Eine Signature ist wie eine Spezifikation: "Diese Funktion soll Notes aus Text extrahieren."
- `TEXT: str = dspy.InputField()`: Das Input-Feld. Die Funktion bekommt einen Text.
- `NOTES: str = dspy.OutputField(...)`: Das Output-Feld. Die Funktion soll strukturierte Notizen zurückgeben.
- Die Beschreibung im Docstring sagt dem Framework, was gemacht werden soll.

**Was passiert darunter?** DSPy nimmt diese Signature und generiert automatisch einen Prompt. Ihr seht den Prompt nicht, aber DSPy hat ihn basierend auf der Signature erstellt.

**Vergleich:**
Schaut euch `agents/reader.py` an. Dort seht ihr den exakten Prompt:
```python
"You are a precise scientific note-taker. Work ONLY with the TEXT below. ..."
```

In DSPy ist nur die Signatur definiert - keine explizite Prompt-Instruktion. DSPy generiert den Prompt automatisch basierend auf der Signature-Beschreibung.

**Was ist der Vorteil?** Ihr müsst keine Prompts schreiben. Ihr beschreibt nur, was erreicht werden soll, und DSPy findet die beste Art, es zu erreichen. Das spart Zeit und kann zu besseren Ergebnissen führen.

**Was ist der Nachteil?** Ihr habt weniger Kontrolle über den exakten Prompt. Wenn ihr einen sehr spezifischen Prompt braucht, ist LangChain/LangGraph besser.

### Aufgabe 5.2: Signature anpassen - Deklaratives Paradigma verstehen

**Schwierigkeitsgrad: Mittel**

**Was macht ihr?** Ihr ändert eine Signature und seht, wie sich die Ausgabe ändert, ohne dass ihr einen expliziten Prompt ändern müsst.

**Wie funktioniert das?** Die Beschreibung in der Signature beeinflusst, wie DSPy den Prompt generiert. Wenn ihr "200-300 words" in "50-100 words" ändert, generiert DSPy automatisch einen anderen Prompt, der kürzere Summaries produziert.

**Schritt 1: Signature finden**
Findet die `Summarize` Signature in `workflows/dspy_pipeline.py` (Zeile 85-88):

```python
class Summarize(dspy.Signature):
    """Grounded 200-300 word summary from NOTES with takeaways."""
    NOTES: str = dspy.InputField()
    SUMMARY: str = dspy.OutputField()
```

**Was steht da?** Die Beschreibung sagt: "Erstelle eine gegründete Zusammenfassung von 200-300 Wörtern mit Takeaways aus den Notizen." DSPy nutzt diese Beschreibung, um einen Prompt zu generieren.

**Schritt 2: Beschreibung ändern**
Ändert die Beschreibung zu:
```python
"""Grounded 100-150 word very brief summary from NOTES with key points only."""
```

**Was ändert sich?** Jetzt sagt die Beschreibung "100-150 Wörter" statt "200-300 Wörter" und "very brief" und "key points only". DSPy wird basierend auf dieser neuen Beschreibung einen anderen Prompt generieren.

**Schritt 3: Testen**
Speichert die Datei und führt DSPy erneut aus mit demselben Dokument.

**Was hat sich geändert?** Die Summary sollte kürzer sein, auch wenn ihr den Prompt nicht direkt angepasst habt. Warum? Weil DSPy automatisch einen neuen Prompt generiert hat, der auf der geänderten Beschreibung basiert.

**Was lernt ihr daraus?** Das ist das deklarative Paradigma: Ihr beschreibt das Ziel ("100-150 Wörter, sehr kurz, nur Hauptpunkte"), nicht den Weg (den exakten Prompt). DSPy findet automatisch die beste Art, das Ziel zu erreichen.

**Vergleich mit LangChain:** In LangChain hättet ihr den expliziten Prompt ändern müssen: `"Produce a concise scientific summary (200-300 words)"` zu `"Produce a very brief scientific summary (50-100 words)"`. In DSPy ändert ihr nur die Beschreibung in der Signature, und das Framework macht den Rest.

**Tipp:** Die Beschreibung in der Signature ist wichtig. Sie bestimmt, wie DSPy den Prompt generiert. Präzise Beschreibungen führen zu besseren automatisch generierten Prompts.

**Schwierigkeitsgrad: Schwer**

Fügt ein neues Feld zur Signature hinzu. Zum Beispiel:
```python
class Summarize(dspy.Signature):
    """Grounded 200-300 word summary from NOTES with takeaways."""
    NOTES: str = dspy.InputField()
    TARGET_LENGTH: str = dspy.InputField(desc="Target length: short, medium, or long")
    SUMMARY: str = dspy.OutputField()
```

Müsst ihr dann auch die Verwendung anpassen? Findet, wo `Summarize` verwendet wird (ca. Zeile 150-160). Müsst ihr dort `TARGET_LENGTH` übergeben?

### Aufgabe 5.3: Teleprompting aktivieren

**Schwierigkeitsgrad: Mittel**

Aktiviert "DSPy optimieren" in der App. Klickt auf "DSPy Teleprompt Gain". Das dauert 1-2 Minuten.

Während der Wartezeit: Überlegt euch, was passiert. DSPy testet verschiedene Prompts basierend auf dem Dev-Set (`eval/dev.jsonl`). Es evaluiert jeden Prompt und wählt die beste Variante.

Falls ihr Code-Zugriff habt, schaut euch an, wo Teleprompting aktiviert wird. Sucht nach "teleprompt" in `workflows/dspy_pipeline.py`. Seht ihr, wie es konfiguriert ist?

Nach Abschluss: Vergleicht Base vs. Teleprompt. Seht ihr den F1 Gain? Wie viel besser ist Teleprompt?

**Tipp:** Der F1 Gain zeigt die Verbesserung. Meist ist Teleprompt besser, aber langsamer - das ist ein Trade-off. DSPy hat automatisch bessere Prompts gefunden, ohne dass ihr sie manuell schreiben musstet.

**Schwierigkeitsgrad: Schwer**

Öffnet `eval/dev.jsonl`. Seht ihr die Struktur? Das Dev-Set enthält Beispiele mit Input und erwarteten Output. DSPy nutzt diese, um die besten Prompts zu finden.

Überlegt euch: Wie würdet ihr ohne DSPy die besten Prompts finden? Durch manuelles Ausprobieren. DSPy automatisiert diesen Prozess.

---

## Teil 6: Experimentieren und Vergleichen (8 Minuten)

### Aufgabe 6.1: Eigenes Experiment

**Schwierigkeitsgrad: Mittel**

Wählt eine der folgenden Aufgaben:

1. **Agent-Prompt anpassen:** Ändert einen Prompt in `agents/reader.py` oder `agents/summarizer.py`. Führt beide Pipelines (LangChain und LangGraph) aus. Sehen beide die Änderung? Warum ja/nein?

2. **Reihenfolge testen:** In LangGraph könnt ihr die Edge-Reihenfolge ändern. Was passiert, wenn ihr Quality VOR Critic ausführt? Ändert die Edges in `_build_langgraph_workflow`.

3. **State-Felder hinzufügen:** Fügt ein neues Feld zum PipelineState hinzu (z.B. `confidence_score: float`). Nutzt es in einem Node. Seht ihr es in den Ergebnissen?

### Aufgabe 6.2: Unterschiede durch Code-Änderungen sehen - Der entscheidende Test

**Schwierigkeitsgrad: Mittel**

**Was macht ihr?** Ihr macht ein Experiment, das den fundamentalen Unterschied zwischen den Frameworks zeigt.

**Das Experiment:** Ändert den Summarizer-Prompt in `agents/summarizer.py` (wie in Aufgabe 2.2). Ändert z.B. "200-300 words" zu "50-100 words". Führt dann alle drei Pipelines aus: LangChain, LangGraph und DSPy.

**Was erwartet ihr?**
- **LangChain:** Sollte die Änderung sehen, weil LangChain den Prompt direkt aus `agents/summarizer.py` liest.
- **LangGraph:** Sollte die Änderung auch sehen, weil LangGraph die gleichen Agent-Funktionen nutzt wie LangChain.
- **DSPy:** Sollte die Änderung NICHT sehen, weil DSPy seinen eigenen Prompt basierend auf der Signature generiert, nicht den expliziten Prompt nutzt.

**Führt das Experiment durch:**
1. Ändert den Prompt in `agents/summarizer.py`
2. Führt LangChain aus → Summary sollte kürzer sein
3. Führt LangGraph aus → Summary sollte kürzer sein
4. Führt DSPy aus → Summary bleibt bei der ursprünglichen Länge (oder ändert sich nur, wenn die Signature auch geändert wurde)

**Beobachtung:** Sehen LangChain und LangGraph die Änderung? Ja, beide nutzen denselben Agent-Code. Sieht DSPy die Änderung? Nein, DSPy generiert seinen eigenen Prompt basierend auf der Signature.

**Was bedeutet das?** Das zeigt den fundamentalen Unterschied: In LangChain/LangGraph kontrolliert ihr die Prompts direkt. Ihr schreibt einen Prompt, und der wird verwendet. In DSPy beschreibt ihr nur das Ziel (in der Signature), und das Framework generiert die Prompts automatisch. Die expliziten Prompts in `agents/summarizer.py` werden von DSPy ignoriert.

**Umgekehrtes Experiment:** Ändert die Summarize-Signature in DSPy (wie in Aufgabe 5.2). Ändert NICHT den Summarizer-Prompt in `agents/summarizer.py`. Führt alle drei aus.

**Was passiert?**
- **LangChain:** Keine Änderung, weil LangChain den Prompt aus `agents/summarizer.py` nutzt, nicht die Signature.
- **LangGraph:** Keine Änderung, aus demselben Grund.
- **DSPy:** Änderung sichtbar, weil DSPy die Signature nutzt, um den Prompt zu generieren.

**Was lernt ihr daraus?** LangChain und LangGraph nutzen explizite Prompts. DSPy generiert Prompts aus Signatures. Das ist ein fundamental unterschiedlicher Ansatz. Beide haben Vor- und Nachteile:
- **Explizite Prompts (LangChain/LangGraph):** Volle Kontrolle, aber ihr müsst die Prompts selbst schreiben und optimieren.
- **Signatures (DSPy):** Weniger Kontrolle über den exakten Prompt, aber das Framework optimiert automatisch.

### Aufgabe 6.3: Vergleich dokumentieren

**Schwierigkeitsgrad: Einfach**

Füllt die Entscheidungsmatrix aus basierend auf euren Experimenten:

| Kriterium | LangChain | LangGraph | DSPy |
|-----------|-----------|-----------|------|
| Struktur | linear | graph-basiert | deklarativ |
| Code-Änderungen | einfach | komplexer | sehr komplex |
| Prompt-Kontrolle | vollständig | vollständig | beschränkt (Signature) |
| Debugging | schwierig | einfach (Graph sichtbar) | schwierig |
| Erweiterbarkeit | limitiert | hoch | sehr hoch |
| Fehlerbehandlung | keine | pro Node | automatisch |
| Selbstoptimierung | Nein | Nein | Ja (Teleprompting) |

---

## Bonus-Aufgaben (falls Zeit bleibt)

### Bonus 1: Eigener Agent

**Schwierigkeitsgrad: Schwer**

Erstellt einen neuen Agent, z.B. einen "FactChecker", der prüft, ob die Summary Fakten aus den Notes korrekt wiedergibt.

1. Erstellt `agents/factchecker.py` basierend auf `agents/critic.py`
2. Fügt den Agent zur LangGraph-Pipeline hinzu als neuen Node
3. Fügt eine Edge vom Summarizer zum FactChecker hinzu
4. Führt die Pipeline aus

### Bonus 2: Parallele Ausführung

**Schwierigkeitsgrad: Schwer**

In LangGraph könnt ihr theoretisch Nodes parallel ausführen. Recherchiert, wie man das mit LangGraph macht. Kann man Reader und Summarizer parallel starten? Warum nicht?

---

## Zusammenfassung

Ihr habt Multi-Agent Orchestration praktisch erlebt:

- **LangChain:** Einfache sequenzielle Ausführung, leicht zu verstehen, Prompts direkt anpassbar, aber limitiert in der Flexibilität. Ihr habt gesehen, wie einfach es ist, einen Prompt zu ändern.

- **LangGraph:** Explizite Graph-Struktur, transparent und visuell sichtbar, erweiterbar (neue Nodes hinzufügen), Conditional Edges möglich, aber komplexer im Code. Ihr habt gesehen, wie die Struktur explizit im Code definiert ist.

- **DSPy:** Deklarative Definition, selbstoptimierend (Teleprompting), aber Framework-spezifisch und weniger Kontrolle über exakte Prompts. Ihr habt gesehen, wie Signatures das Ziel beschreiben, ohne explizite Prompts.

**Was ist der Hauptunterschied?**
- LangChain/LangGraph: Ihr kontrolliert Prompts direkt, seht genau, was passiert
- DSPy: Ihr beschreibt das Ziel, das Framework generiert die Prompts automatisch

**Die Code-Experimente zeigen:** LangChain ist direkt und einfach. LangGraph ist explizit und erweiterbar. DSPy ist deklarativ und selbstoptimierend.

Weitere Experimente: Ändert Prompts, fügt Nodes hinzu, testet verschiedene Graph-Strukturen, ändert Signatures. Das ist der beste Weg, die Unterschiede wirklich zu verstehen.

Bei Fragen wendet euch an das Workshop-Team oder schaut in die Code-Kommentare.

---

## Troubleshooting

### Code-Änderungen werden nicht übernommen

**Problem:** Ihr habt Code geändert, aber die App nutzt die alte Version.

**Lösung:**
1. Wartet 10 Sekunden nach dem Speichern - Streamlit lädt automatisch neu
2. Falls immer noch nicht: Startet die App neu
   - Im Terminal: Strg+C (Windows/Linux) oder Cmd+C (Mac)
   - Dann erneut: `streamlit run app.py`
3. Prüft, ob euer Editor wirklich gespeichert hat (manche Editoren speichern nicht automatisch)

### Syntax-Fehler

**Problem:** Die App zeigt einen Fehler nach Code-Änderung.

**Lösung:**
1. Prüft Einrückungen - Python ist empfindlich bei Tabs/Spaces (nutzt am besten nur Spaces)
2. Prüft Anführungszeichen - alle müssen geschlossen sein
3. Prüft Klammern - alle müssen geschlossen sein
4. Nutzt `CODE_EXPERIMENTE.md` für korrekte Code-Snippets zum Kopieren
5. Falls nichts hilft: Stellt die Datei wieder her (Git oder Backup)

### Pipeline läuft nicht

**Problem:** Die Pipeline startet nicht oder zeigt einen Fehler.

**Lösung:**
1. Prüft, ob ein Dokument hochgeladen wurde (muss mindestens 100 Zeichen haben)
2. Prüft, ob API-Key gesetzt ist (falls lokal)
3. Prüft die Terminal-Ausgabe für Fehlermeldungen
4. Schaut in die Hilfe-Sektion der App
5. Versucht ein kleineres Dokument

### DSPy nicht verfügbar

**Problem:** Warnung "DSPy ist nicht installiert".

**Lösung:**
- Das ist ok für die Demo. DSPy ist optional. Das Konzept ist wichtig, auch wenn die volle Funktionalität fehlt.
- Falls ihr DSPy nutzen wollt: `pip install dspy-ai litellm`

### Graph-Visualisierung nicht sichtbar

**Problem:** Bei LangGraph seht ihr keine Graph-Visualisierung.

**Lösung:**
- Scrollt nach unten unter den Ergebnissen
- Wartet, bis die Pipeline vollständig durchgelaufen ist
- Prüft, ob die Pipeline wirklich auf "LangGraph" gestellt ist
