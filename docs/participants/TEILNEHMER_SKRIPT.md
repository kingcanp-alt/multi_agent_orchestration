# Workshop Skript für Teilnehmer

## Was wir heute machen

Ihr experimentiert heute mit drei verschiedenen Frameworks, die alle denselben Workflow steuern: Reader → Summarizer → Critic → Integrator. Am Ende versteht ihr:
- Was Multi Agent Orchestrierung ist und warum sie nützlich ist
- Wie sich LangChain, LangGraph und DSPy unterscheiden
- Wie kleine Code-Änderungen das Verhalten beeinflussen
- Wie ihr selbst neue Funktionen hinzufügen könnt

## Zeitplan (60 Minuten)
1. Setup & Einführung (5-10 min)
2. LangChain: Prompts anpassen und verstehen, wie sequenzielle Pipelines funktionieren (12 min)
3. LangGraph: Graph-Struktur erkunden und Conditional Flows testen (15 min)
4. DSPy: Signatures anpassen und Teleprompting ausprobieren (15 min)
5. Vergleich & Diskussion (3 min)

## Vorbereitung

**App starten:**
- Doppelklick auf `scripts/launchers/run.bat` (Windows) oder `run.sh` (Mac/Linux)
- Oder manuell: `python -m streamlit run app/app.py`

**Dateien öffnen:**
- `app/agents/reader.py` - Extrahiert Notizen aus Papers
- `app/agents/summarizer.py` - Erstellt Zusammenfassungen
- `app/agents/critic.py` - Bewertet die Qualität
- `app/workflows/langchain_pipeline.py` - Sequenzielle Pipeline
- `app/workflows/langgraph_pipeline.py` - Graph-basierte Pipeline
- `app/workflows/dspy_pipeline.py` - Deklarative Pipeline

**Testdokument bereit:**
- PDF oder TXT mit 2-3 Seiten (z. B. ein wissenschaftliches Paper)

---

## Teil 1: LangChain verstehen

### Was ist LangChain?

LangChain führt die Agenten **nacheinander** aus, wie eine Kette. Jeder Schritt wartet, bis der vorherige fertig ist. Das ist einfach, aber unflexibel - wenn etwas schiefgeht, gibt es keine automatische Wiederholung.

**Warum das wichtig ist:** Ihr seht hier die einfachste Form der Orchestrierung. Perfekt zum Einstieg, aber begrenzt in den Möglichkeiten.

### Aufgabe 1: Prompt anpassen

**Was passiert:** Der Summarizer bekommt eine Anweisung, wie er zusammenfassen soll. Wenn ihr diese ändert, ändert sich auch die Ausgabe.

**So geht's:**
1. Öffnet `app/agents/summarizer.py`
2. Sucht `SUMMARIZER_PROMPT` (ca. Zeile 11)
3. In Zeile 12 steht: `"Produce a concise scientific summary..."`
4. Ändert es zu: `"Produce a very brief scientific summary (max 100 words)..."`
5. Speichern und LangChain erneut ausführen

**Was ihr seht:** Die Summary wird deutlich kürzer. Das zeigt, wie direkt Prompts das Ergebnis beeinflussen.

### Aufgabe 2: Critic erweitern

**Was passiert:** Der Critic bewertet die Summary nach 4 Kategorien. Ihr fügt eine fünfte hinzu, um zu sehen, wie einfach man Bewertungskriterien anpassen kann.

**So geht's:**
1. Öffnet `app/agents/critic.py`
2. Sucht `CRITIC_PROMPT` (ca. Zeile 13)
3. Nach Zeile 25 fügt hinzu: `"- Clarity: clear and easy to understand.\n\n"`
4. Nach Zeile 30 fügt hinzu: `"Clarity: <0-5>\n"`
5. Pipeline neu starten

**Was ihr seht:** Der Critic gibt jetzt auch einen Klarheitswert aus. Das zeigt, wie einfach man Bewertungskriterien erweitern kann.

### Aufgabe 3: Reihenfolge testen

**Was passiert:** LangChain hat keine automatische Abhängigkeitsprüfung. Wenn ihr die Reihenfolge ändert, bricht es - das zeigt die Grenzen sequenzieller Pipelines.

**So geht's:**
1. Öffnet `app/workflows/langchain_pipeline.py`
2. Sucht `run_pipeline` (Zeile 21)
3. Verschiebt Zeile 60 (Critic) VOR Zeile 54 (Summarizer)
4. Setzt `summary=""` im Critic-Aufruf
5. Pipeline starten

**Was ihr seht:** Entweder ein Fehler oder sinnlose Ausgabe. Das zeigt, warum die Reihenfolge bei LangChain so wichtig ist.

### Aufgabe 4: Reader anpassen

**Was passiert:** Der Reader extrahiert strukturierte Notizen. Wenn ihr die Anweisungen ändert, ändert sich, was extrahiert wird.

**So geht's:**
1. Öffnet `app/agents/reader.py`
2. Sucht `READER_PROMPT` (ca. Zeile 11)
3. Ändert die "Results"-Anweisung (Zeile 20-21), z. B. "extract at least 3 results"
4. Pipeline neu starten

**Was ihr seht:** Der Reader extrahiert mehr oder weniger Details, je nachdem was ihr ändert.

---

## Teil 2: LangGraph erweitern

### Was ist LangGraph?

LangGraph nutzt einen **Graph** mit Nodes und Edges. Der große Unterschied: Es gibt **bedingte Routen**. Wenn der Critic die Summary schlecht findet, kann der Graph zurück zum Summarizer springen und es nochmal versuchen.

**Warum das wichtig ist:** Ihr seht hier, wie man flexible Workflows baut, die auf Bedingungen reagieren können.

### Aufgabe 1: Conditional Flow verstehen

**Was passiert:** Die Funktion `_critic_post_path` entscheidet, ob zurück zum Summarizer oder weiter zum Integrator. Der Schwellenwert bestimmt, wie streng diese Entscheidung ist.

**So geht's:**
1. Öffnet `app/workflows/langgraph_pipeline.py`
2. Sucht `_critic_post_path` (Zeile 185)
3. In Zeile 208 steht: `if state["critic_score"] < 0.5`
4. Ändert es zu `0.7` (strenger) oder `0.3` (lockerer)
5. Pipeline neu starten

**Was ihr seht:** Bei 0.7 routet der Graph häufiger zurück, bei 0.3 seltener. Das zeigt, wie Schwellenwerte das Verhalten steuern.

### Aufgabe 2: Max Loops anpassen

**Was passiert:** LangGraph kann mehrmals zum Summarizer zurückkehren, wenn die Qualität schlecht ist. Ihr kontrolliert, wie oft das passieren darf.

**So geht's:**
1. Öffnet `app/app.py`
2. Sucht Zeile 191: `"max_critic_loops": 2`
3. Ändert es zu `0` (keine Loops) oder `5` (mehr Loops)
4. Pipeline neu starten

**Was ihr seht:** Bei 0 gibt es keine Wiederholungen, bei 5 kann es mehrfach versuchen. Die Visualisierung zeigt die Loops im Graph.

### Aufgabe 3: Graph Visualisierung

**Was passiert:** LangGraph erstellt automatisch eine Visualisierung des Workflows. Ihr seht live, welcher Pfad genommen wurde.

**So geht's:**
1. Führt LangGraph in der UI aus
2. Scrollt zum "Workflow Graph"
3. Beobachtet die Nodes und Edges
4. Wenn ein Loop auftritt, seht ihr die gestrichelte Linie zurück zum Summarizer

**Was ihr seht:** Eine visuelle Darstellung des Workflows mit Timings und Scores. Das macht den Unterschied zu LangChain deutlich.

### Aufgabe 4: Timeout anpassen

**Was passiert:** Manchmal hängen LLM-Aufrufe. Ein Timeout verhindert, dass die ganze Pipeline blockiert.

**So geht's:**
1. Öffnet `app/workflows/langgraph_pipeline.py`
2. Sucht `run_pipeline` (Zeile 330)
3. In Zeile 342 steht: `timeout_seconds = int(config_dict.get("timeout", 45))`
4. Ändert `45` zu `30` (kürzer) oder `60` (länger)
5. Testet mit einem sehr langen Dokument

**Was ihr seht:** Bei langsameren Modellen oder langen Texten kann der Timeout wichtig sein, um nicht ewig zu warten.

---

## Teil 3: DSPy anpassen

### Was ist DSPy?

DSPy ist **deklarativ**. Statt Prompts zu schreiben, beschreibt ihr nur, was ihr wollt. DSPy erzeugt die Prompts automatisch. Noch besser: Mit Teleprompting kann DSPy die Prompts sogar optimieren.

**Warum das wichtig ist:** Ihr seht hier, wie man LLM-Pipelines baut, ohne sich um Prompt-Engineering kümmern zu müssen.

### Aufgabe 1: Signature anpassen

**Was passiert:** Die Signature beschreibt Input und Output. DSPy erzeugt daraus automatisch einen Prompt. Wenn ihr die Beschreibung ändert, ändert sich der generierte Prompt.

**So geht's:**
1. Öffnet `app/workflows/dspy_pipeline.py`
2. Sucht `class Summarize` (Zeile 127)
3. Ändert die Beschreibung (Zeile 128), z. B. "very brief summary (max 100 words)"
4. Pipeline neu starten

**Was ihr seht:** DSPy erzeugt einen neuen Prompt basierend auf eurer Beschreibung. Das ist der Vorteil deklarativer Ansätze.

### Aufgabe 2: Critique erweitern

**Was passiert:** Genau wie bei LangChain könnt ihr die Bewertungskriterien erweitern. Hier macht ihr es aber in der Signature statt im Prompt.

**So geht's:**
1. Sucht `class Critique` (Zeile 136)
2. Erweitert die Rubric in der Docstring (Zeile 137), z. B. fügt "Clarity" hinzu
3. Aktualisiert das Format entsprechend
4. Pipeline neu starten

**Was ihr seht:** Die neue Kategorie erscheint in der Ausgabe. Das zeigt, wie flexibel Signatures sind.

### Aufgabe 3: Zusätzlichen Parameter hinzufügen

**Was passiert:** Ihr fügt einen Parameter hinzu, um die Summary-Länge zu steuern. Das zeigt, wie man Signatures erweitert.

**So geht's:**
1. Sucht `class Summarize` (Zeile 127)
2. Fügt hinzu: `TARGET_LENGTH: str = dspy.InputField(desc="'short', 'medium', or 'long'")`
3. Erweitert `SummarizerM.forward` (Zeile 197) um `target_length` Parameter
4. Nutzt es in `PaperPipeline.forward` (Zeile 240): `target_length="short"`

**Was ihr seht:** Ihr könnt jetzt die Länge über einen Parameter steuern, ohne den Prompt direkt zu ändern.

### Aufgabe 4: Teleprompting ausprobieren

**Was passiert:** Teleprompting optimiert die Prompts automatisch mit Beispielen. Das ist der große Vorteil von DSPy.

**So geht's:**
1. In der UI: Settings → DSPy → "Enable Teleprompting" aktivieren
2. Stellt sicher, dass `dev-set/dev.jsonl` existiert
3. Führt DSPy mit und ohne Teleprompting aus
4. Vergleicht im "DSPy Optimization" Tab

**Was ihr seht:** Der F1-Gain zeigt, wie viel besser die optimierte Version ist. Das ist automatisches Prompt-Engineering.

### Aufgabe 5: Reader Signature anpassen

**Was passiert:** Genau wie beim Summarizer könnt ihr auch den Reader über die Signature steuern.

**So geht's:**
1. Sucht `class ReadNotes` (Zeile 103)
2. Ändert die Anweisung für "Results" (Zeile 114-115)
3. Pipeline neu starten

**Was ihr seht:** Die extrahierten Notizen ändern sich basierend auf eurer Beschreibung.

---

## Teil 4: Vergleich & Analyse

### Aufgabe 1: Laufzeit vergleichen

**Was passiert:** Alle drei Pipelines machen dasselbe, aber unterschiedlich schnell. Das zeigt die Trade-offs zwischen den Ansätzen.

**So geht's:**
1. Führt alle drei Pipelines mit demselben Dokument aus
2. Nutzt den "Compare" Tab
3. Vergleicht die Laufzeiten

**Was ihr diskutiert:** Welche Pipeline ist am schnellsten? Warum? Was sind die Trade-offs?

### Aufgabe 2: Qualität vergleichen

**Was passiert:** Nicht nur die Geschwindigkeit, auch die Qualität kann sich unterscheiden.

**So geht's:**
1. Schaut euch die Critic-Scores an
2. Vergleicht die Summaries und Meta-Summaries
3. Welche gefällt euch am besten?

**Was ihr diskutiert:** Welche Pipeline produziert bessere Ergebnisse? Warum könnte das so sein?

### Aufgabe 3: Telemetrie analysieren

**Was passiert:** Die Telemetrie zeigt, wo die Zeit verbraucht wird. Das hilft, Bottlenecks zu finden.

**So geht's:**
1. Öffnet "CSV Telemetry Data" in der UI
2. Schaut euch die letzten Einträge an
3. Analysiert die Zeiten pro Agent

**Was ihr seht:** Welcher Agent braucht am längsten? Das zeigt, wo Optimierungen am meisten helfen würden.

### Aufgabe 4: Code-Komplexität vergleichen

**Was passiert:** Mehr Features bedeuten meist mehr Code. Aber ist das immer schlecht?

**So geht's:**
1. Zählt die Zeilen in den drei Pipeline-Dateien
2. Vergleicht die Komplexität

**Was ihr diskutiert:** Welche Pipeline ist am einfachsten zu verstehen? Welche bietet die meisten Möglichkeiten? Was ist wichtiger?

---

## Teil 5: Erweiterte Aufgaben (Optional)

Falls ihr schneller seid oder mehr experimentieren wollt:

### Neuen Agent hinzufügen (LangChain)
Erstellt einen Validator, der zwischen Summarizer und Critic prüft, ob die Summary bestimmte Kriterien erfüllt.

### Neuen Node hinzufügen (LangGraph)
Fügt einen "Quality Check" Node zwischen Critic und Integrator hinzu und verbindet ihn im Graph.

### Neue Signature erstellen (DSPy)
Erstellt eine `Validate` Signature und integriert sie in die Pipeline.

### Error Handling verbessern
Schaut euch an, wie LangChain mit Fehlern umgeht und implementiert ähnliches für LangGraph.

---

## Zusammenfassung

Ihr habt heute drei verschiedene Ansätze für denselben Workflow gesehen:
- **LangChain:** Einfach, sequenziell, gut zum Einstieg
- **LangGraph:** Flexibel, mit bedingten Routen, gut für komplexe Workflows
- **DSPy:** Deklarativ, mit automatischer Optimierung, gut wenn ihr euch nicht um Prompts kümmern wollt

**Diskutiert:**
- Welche Pipeline ist für welche Anwendungsfälle am besten?
- Was sind die Trade-offs?
- Was würdet ihr anders machen?

---

## Hilfe

- **App hängt:** Strg+C im Terminal, dann neu starten
- **Fehler:** Schaut ins Terminal, dort stehen die Fehlermeldungen
- **Code-Beispiele:** `docs/participants/CODE_EXPERIMENTE.md`
- **Telemetrie:** Nutzt den "CSV Telemetry Data" Expander für Laufzeiten
