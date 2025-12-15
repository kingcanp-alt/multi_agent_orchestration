# Code Experimente

Hier findet ihr konkrete Code-Beispiele, die ihr direkt ausprobieren könnt. Jedes Beispiel erklärt kurz, was passiert und warum es interessant ist.

---

## 1. Summarizer kürzer oder länger machen

**Datei:** `app/agents/summarizer.py`

**Warum:** Der Prompt steuert direkt, wie lang die Summary wird. Einfach zu testen und sofort sichtbar.

**So geht's:**
1. Sucht `SUMMARIZER_PROMPT` (Zeile 11)
2. Ändert Zeile 12:

```python
# Vorher:
"Produce a concise scientific summary from NOTES. Do not invent facts. Do not include citations.\n\n"

# Nachher (sehr kurz):
"Produce a very brief scientific summary (max 100 words) from NOTES. Do not invent facts. Do not include citations.\n\n"

# Oder (sehr lang):
"Produce a detailed scientific summary (300-500 words) from NOTES. Do not invent facts. Do not include citations.\n\n"
```

**Was passiert:** Die Summary wird deutlich kürzer oder länger. Das zeigt, wie direkt Prompts das Ergebnis beeinflussen.

---

## 2. Critic um Klarheit erweitern

**Datei:** `app/agents/critic.py`

**Warum:** Ihr seht, wie einfach man Bewertungskriterien hinzufügen kann. Das ist nützlich, wenn ihr spezifische Aspekte bewerten wollt.

**So geht's:**
1. Sucht `CRITIC_PROMPT` (Zeile 13)
2. Erweitert die Rubric (nach Zeile 25):

```python
"SCORING (0-5 integers):\n"
"- Makes sense: logical flow, no contradictions.\n"
"- Accuracy: claims supported by NOTES.\n"
"- Coverage: objective covered, method covered, results covered, limitations covered.\n"
"- Details: important details included. If metrics missing in SUMMARY but exist in NOTES, lower score sharply. If NOTES have no metrics, do not reward high details score.\n"
"- Clarity: clear and easy to understand, no jargon overload.\n\n"  # NEU
```

3. Erweitert das OUTPUT FORMAT (nach Zeile 30):

```python
"OUTPUT FORMAT:\n"
"Makes sense: <0-5>\n"
"Accuracy: <0-5>\n"
"Coverage: <0-5>\n"
"Details: <0-5>\n"
"Clarity: <0-5>\n"  # NEU
"Improvements:\n"
"- <short fix #1>\n"
"- <short fix #2>\n"
"- <optional fix #3>\n\n"
```

**Was passiert:** Der Critic gibt jetzt auch einen Klarheitswert aus. Das zeigt, wie flexibel das Bewertungssystem ist.

---

## 3. LangChain Reihenfolge testen

**Datei:** `app/workflows/langchain_pipeline.py`

**Warum:** Das zeigt die Grenzen sequenzieller Pipelines. Wenn die Reihenfolge falsch ist, funktioniert es nicht - und LangChain prüft das nicht automatisch.

**So geht's:**
1. Sucht die Funktion `run_pipeline` (Zeile 21)
2. Verschiebt den Critic-Aufruf VOR den Summarizer:

```python
# Vorher (korrekt):
summary = run_summarizer(structured_notes)
critic_result = run_critic(notes=structured_notes, summary=summary)

# Nachher (falsch):
critic_result = run_critic(notes=structured_notes, summary="")  # Leere Summary!
summary = run_summarizer(structured_notes)
```

**Was passiert:** Entweder ein Fehler oder sinnlose Ausgabe. Das zeigt, warum die Reihenfolge bei LangChain so wichtig ist und warum LangGraph mit bedingten Routen flexibler ist.

---

## 4. LangGraph Conditional Flow anpassen

**Datei:** `app/workflows/langgraph_pipeline.py`

**Warum:** Der Schwellenwert bestimmt, wie streng der Graph ist. Das ist der Kern von LangGraph - bedingte Entscheidungen.

**So geht's:**
1. Sucht die Funktion `_critic_post_path` (Zeile 185)
2. Ändert den Schwellenwert (Zeile 208):

```python
# Vorher:
if state["critic_score"] < 0.5 and loops < max_loops:

# Nachher (strenger - routet häufiger zurück):
if state["critic_score"] < 0.7 and loops < max_loops:

# Oder (lockerer - routet seltener zurück):
if state["critic_score"] < 0.3 and loops < max_loops:
```

**Was passiert:** Bei 0.7 wird häufiger zurückgeroutet (strenger), bei 0.3 seltener (lockerer). Die Visualisierung zeigt die Unterschiede im Graph.

---

## 5. LangGraph Max Loops ändern

**Datei:** `app/app.py`

**Warum:** Ihr kontrolliert, wie oft der Graph versuchen darf, eine bessere Summary zu erzeugen. Mehr Loops = mehr Versuche, aber auch mehr Zeit.

**So geht's:**
1. Sucht die Config-Definition (Zeile 191):

```python
# Vorher:
"max_critic_loops": 2,

# Nachher (keine Loops - wie LangChain):
"max_critic_loops": 0,

# Oder (mehr Loops - mehr Versuche):
"max_critic_loops": 5,
```

**Was passiert:** Bei 0 gibt es keine Wiederholungen (ähnlich wie LangChain), bei 5 kann es mehrfach versuchen. Die Visualisierung zeigt die Loops.

---

## 6. LangGraph Timeout anpassen

**Datei:** `app/workflows/langgraph_pipeline.py`

**Warum:** Manchmal hängen LLM-Aufrufe. Ein Timeout verhindert, dass die ganze Pipeline blockiert. Wichtig bei langsamen Modellen oder langen Texten.

**So geht's:**
1. Sucht die Funktion `run_pipeline` (Zeile 330)
2. Ändert den Timeout (Zeile 342):

```python
# Vorher:
timeout_seconds = int(config_dict.get("timeout", 45))

# Nachher (kürzer - bricht früher ab):
timeout_seconds = int(config_dict.get("timeout", 30))

# Oder (länger - wartet länger):
timeout_seconds = int(config_dict.get("timeout", 60))
```

**Was passiert:** Bei 30 Sekunden bricht es früher ab (gut für schnelle Tests), bei 60 wartet es länger (gut für langsame Modelle).

---

## 7. DSPy Signature variieren

**Datei:** `app/workflows/dspy_pipeline.py`

**Warum:** Das ist der Kern von DSPy - ihr beschreibt nur, was ihr wollt, und DSPy erzeugt den Prompt. Ändert ihr die Beschreibung, ändert sich der Prompt automatisch.

**So geht's:**
1. Sucht `class Summarize` (Zeile 127)
2. Ändert die Beschreibung (Zeile 128):

```python
# Vorher:
"""Produce a concise scientific summary from NOTES.
Cover in this order: Objective -> Method (what/how) -> Results (numbers if present; otherwise write exactly 'No quantitative metrics reported in provided text.')
-> Limitations -> 3-5 Practical Takeaways (bulleted).
Avoid speculation or citations. Do NOT invent metrics; if NOTES Results contains the exact sentence
'No quantitative metrics reported in provided text.', then the summary Results must use that exact sentence and contain no numbers."""

# Nachher (fokussiert auf Results):
"""Produce a very brief scientific summary (max 100 words) from NOTES, focusing primarily on RESULTS.
Include quantitative outcomes if present in NOTES. Otherwise write exactly 'No quantitative metrics reported in provided text.'
Avoid speculation or citations. Do NOT invent metrics."""

# Oder (fokussiert auf Method):
"""Produce a detailed scientific summary from NOTES, focusing primarily on METHODOLOGY.
Explain what techniques were used, how they were applied, and what tools/frameworks were involved.
Include Results if present, but emphasize the methodological approach."""
```

**Was passiert:** DSPy erzeugt automatisch einen neuen Prompt basierend auf eurer Beschreibung. Das ist der Vorteil deklarativer Ansätze - kein manuelles Prompt-Engineering nötig.

---

## 8. DSPy Critique Signature erweitern

**Datei:** `app/workflows/dspy_pipeline.py`

**Warum:** Genau wie bei LangChain könnt ihr Bewertungskriterien hinzufügen, aber hier macht ihr es in der Signature statt im Prompt.

**So geht's:**
1. Sucht `class Critique` (Zeile 136)
2. Erweitert die Rubric (Zeile 137):

```python
# Vorher:
"""Critique SUMMARY against NOTES. Judge for makes sense, accuracy, coverage, and details.
Return a rubric with scores 0-5 for each dimension, followed by improvement suggestions.
Format:
Makes sense: <0-5>
Accuracy: <0-5>
Coverage: <0-5>
Details: <0-5>
Improvements:
- <short fix #1>
- <short fix #2>
- <optional fix #3>"""

# Nachher (mit Clarity):
"""Critique SUMMARY against NOTES. Judge for makes sense, accuracy, coverage, details, and clarity.
Return a rubric with scores 0-5 for each dimension, followed by improvement suggestions.
Format:
Makes sense: <0-5>
Accuracy: <0-5>
Coverage: <0-5>
Details: <0-5>
Clarity: <0-5>
Improvements:
- <short fix #1>
- <short fix #2>
- <optional fix #3>"""
```

**Was passiert:** Die Critique enthält jetzt auch eine Klarheitsbewertung. Das zeigt, wie flexibel Signatures sind.

---

## 9. DSPy Target Length als Input hinzufügen

**Datei:** `app/workflows/dspy_pipeline.py`

**Warum:** Ihr fügt einen Parameter hinzu, um die Summary-Länge zu steuern. Das zeigt, wie man Signatures erweitert und Parameter nutzt.

**So geht's:**

**Schritt 1:** Erweitert `class Summarize` (Zeile 127):

```python
class Summarize(dspy.Signature):
    """Produce a scientific summary from NOTES.
    TARGET_LENGTH controls the desired length: 'short' (50-100 words), 'medium' (150-250 words), or 'long' (300-500 words).
    Cover in this order: Objective -> Method -> Results -> Limitations -> Takeaways.
    Avoid speculation or citations. Do NOT invent metrics."""
    NOTES: str = dspy.InputField(desc="Structured scientific notes")
    TARGET_LENGTH: str = dspy.InputField(desc="Desired length: 'short', 'medium', or 'long'")
    SUMMARY: str = dspy.OutputField(desc="Scientific summary")
```

**Schritt 2:** Erweitert `class SummarizerM.forward` (Zeile 197):

```python
def forward(self, notes: str = None, NOTES: str = None, target_length: str = "medium"):
    input_notes = NOTES if NOTES is not None else notes
    if input_notes is None:
        raise ValueError("Either 'notes' or 'NOTES' must be provided")
    out = self.gen(NOTES=input_notes, TARGET_LENGTH=target_length)
    return dspy.Prediction(SUMMARY=_sanitize(out.SUMMARY))
```

**Schritt 3:** Nutzt es in `PaperPipeline.forward` (Zeile 240):

```python
summary = self.summarizer(NOTES=notes, target_length="short").SUMMARY
```

**Was passiert:** Ihr könnt jetzt die Länge über einen Parameter steuern, ohne den Prompt direkt zu ändern. Das zeigt, wie flexibel Signatures sind.

---

## 10. Reader Prompt anpassen

**Datei:** `app/agents/reader.py`

**Warum:** Der Reader extrahiert strukturierte Notizen. Wenn ihr die Anweisungen ändert, ändert sich, was extrahiert wird.

**So geht's:**
1. Sucht `READER_PROMPT` (Zeile 11)
2. Ändert die Anweisung für "Results" (Zeile 20-21):

```python
# Vorher:
"Results:\n"
"<EITHER list quantitative outcomes as bullets OR write exactly: No quantitative metrics reported in provided text.>\n"

# Nachher (mehr Details):
"Results:\n"
"<EITHER list at least 3 quantitative outcomes as bullets with full context (model, dataset, metric, value) OR write exactly: No quantitative metrics reported in provided text.>\n"
```

**Was passiert:** Der Reader extrahiert mehr Details aus den Ergebnissen. Das zeigt, wie Prompts die Extraktion steuern.

---

## 11. Error Handling testen

**Datei:** `app/workflows/langchain_pipeline.py`

**Warum:** Ihr seht, wie die Pipeline mit ungültigen Eingaben umgeht. Wichtig für robuste Anwendungen.

**So geht's:**
1. In der UI: Leeres Textfeld oder sehr kurzen Text (< 100 Zeichen) hochladen
2. Pipeline starten
3. Beobachtet die Fehlerbehandlung (Zeile 40-43)

**Was passiert:** Die Pipeline gibt eine Fehlermeldung zurück statt abzustürzen. Das zeigt, wie Error Handling funktioniert.

---

## 12. Telemetrie analysieren

**Datei:** `telemetry.csv` (wird automatisch erstellt)

**Warum:** Die Telemetrie zeigt, wo die Zeit verbraucht wird. Das hilft, Bottlenecks zu finden und zu optimieren.

**So geht's:**
1. Führt mehrere Pipeline-Läufe aus
2. Öffnet `telemetry.csv` oder den "CSV Telemetry Data" Expander in der UI
3. Analysiert die Spalten:
   - `latency_s`: Gesamtlaufzeit
   - `reader_s`, `summarizer_s`, `critic_s`, `integrator_s`: Zeiten pro Agent
   - `extracted_metrics_count`: Anzahl gefundener Metriken
   - `critic_loops`: Anzahl Loops (nur LangGraph)

**Was passiert:** Ihr seht, welcher Agent am längsten braucht. Das zeigt, wo Optimierungen am meisten helfen würden.

---

## Tipps

1. **Speichern, dann testen:** Änderungen werden erst nach Speichern wirksam
2. **Bei Syntaxfehlern:** Prüft Einrückungen und Anführungszeichen - Python ist da sehr empfindlich
3. **App neu starten:** Wenn Änderungen nicht wirken, Streamlit neu starten (Strg+C, dann wieder starten)
4. **Nur eine Änderung pro Test:** Macht es einfacher, die Auswirkungen zu verstehen
5. **Backup behalten:** Behaltet eine Kopie der Original-Dateien, falls etwas schiefgeht
6. **Terminal beobachten:** Fehlermeldungen erscheinen im Terminal, nicht immer in der UI

---

## Häufige Fehler

**"Module not found"**
- Prüft, ob ihr im richtigen Verzeichnis seid
- Prüft, ob alle Imports korrekt sind (z. B. `from llm import llm`)

**"AttributeError: 'str' object has no attribute 'content'"**
- Das LLM gibt manchmal Strings statt Objekte zurück
- Der Code nutzt `getattr(llm_response, "content", llm_response)` um beide Fälle zu behandeln
- Falls das nicht hilft, prüft die LLM-Konfiguration

**"Timeout"**
- LLM-Aufruf dauert zu lange
- Erhöht den Timeout (siehe Experiment 6) oder verwendet ein schnelleres Modell

**"Empty response"**
- LLM gibt keine Antwort
- Prüft API-Key und Modell-Verfügbarkeit
- Prüft, ob das Modell in der Config richtig eingestellt ist
