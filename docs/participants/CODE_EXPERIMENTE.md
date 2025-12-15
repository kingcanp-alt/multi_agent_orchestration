# Code Experimente

Diese Datei liefert kurze Code Beispiele, die ihr direkt übernehmen oder anpassen könnt.

---

## 1. Summarizer kürzer oder länger machen

**Datei:** `app/agents/summarizer.py`

**Was ändern:**
- Sucht `SUMMARIZER_PROMPT` (Zeile 11)
- Ändert Zeile 12:
  ```python
  # Vorher:
  "Produce a concise scientific summary from NOTES. Do not invent facts. Do not include citations.\n\n"
  
  # Nachher (sehr kurz):
  "Produce a very brief scientific summary (max 100 words) from NOTES. Do not invent facts. Do not include citations.\n\n"
  
  # Oder (sehr lang):
  "Produce a detailed scientific summary (300-500 words) from NOTES. Do not invent facts. Do not include citations.\n\n"
  ```

**Ergebnis:** GPT erzeugt eine kürzere oder längere Zusammenfassung.

---

## 2. Critic um Klarheit erweitern

**Datei:** `app/agents/critic.py`

**Was ändern:**
- Sucht `CRITIC_PROMPT` (Zeile 13)
- Erweitert die Rubric um "Clarity" (nach Zeile 25):
  ```python
  "SCORING (0-5 integers):\n"
  "- Makes sense: logical flow, no contradictions.\n"
  "- Accuracy: claims supported by NOTES.\n"
  "- Coverage: objective covered, method covered, results covered, limitations covered.\n"
  "- Details: important details included. If metrics missing in SUMMARY but exist in NOTES, lower score sharply. If NOTES have no metrics, do not reward high details score.\n"
  "- Clarity: clear and easy to understand, no jargon overload.\n\n"  # NEU
  ```
- Erweitert das OUTPUT FORMAT (nach Zeile 30):
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

**Ergebnis:** Der Critic gibt zusätzlich einen Klarheitswert aus.

---

## 3. LangChain Reihenfolge testen

**Datei:** `app/workflows/langchain_pipeline.py`

**Was ändern:**
- Sucht die Funktion `run_pipeline` (Zeile 21)
- Verschiebt den Critic-Aufruf VOR den Summarizer:
  ```python
  # Vorher (korrekt):
  summary = run_summarizer(structured_notes)
  critic_result = run_critic(notes=structured_notes, summary=summary)
  
  # Nachher (falsch):
  critic_result = run_critic(notes=structured_notes, summary="")  # Leere Summary!
  summary = run_summarizer(structured_notes)
  ```

**Ergebnis:** Ihr seht, dass die Reihenfolge die Logik bricht und warum LangChain die Abhängigkeiten nicht automatisch steuert.

---

## 4. LangGraph Conditional Flow anpassen

**Datei:** `app/workflows/langgraph_pipeline.py`

**Was ändern:**
- Sucht die Funktion `_critic_post_path` (Zeile 185)
- Ändert den Schwellenwert (Zeile 208):
  ```python
  # Vorher:
  if state["critic_score"] < 0.5 and loops < max_loops:
  
  # Nachher (strenger):
  if state["critic_score"] < 0.7 and loops < max_loops:
  
  # Oder (lockerer):
  if state["critic_score"] < 0.3 and loops < max_loops:
  ```

**Ergebnis:** Der Graph routet häufiger/seltener zurück zum Summarizer.

---

## 5. LangGraph Max Loops ändern

**Datei:** `app/app.py`

**Was ändern:**
- Sucht die Config-Definition (Zeile 191):
  ```python
  # Vorher:
  "max_critic_loops": 2,
  
  # Nachher (keine Loops):
  "max_critic_loops": 0,
  
  # Oder (mehr Loops):
  "max_critic_loops": 5,
  ```

**Ergebnis:** LangGraph erlaubt mehr/fewer Wiederholungen des Summarizers.

---

## 6. LangGraph Timeout anpassen

**Datei:** `app/workflows/langgraph_pipeline.py`

**Was ändern:**
- Sucht die Funktion `run_pipeline` (Zeile 330)
- Ändert den Timeout (Zeile 342):
  ```python
  # Vorher:
  timeout_seconds = int(config_dict.get("timeout", 45))
  
  # Nachher (kürzer):
  timeout_seconds = int(config_dict.get("timeout", 30))
  
  # Oder (länger):
  timeout_seconds = int(config_dict.get("timeout", 60))
  ```

**Ergebnis:** LangGraph bricht langsamere LLM-Aufrufe früher/später ab.

---

## 7. DSPy Signature variieren

**Datei:** `app/workflows/dspy_pipeline.py`

**Was ändern:**
- Sucht `class Summarize` (Zeile 127)
- Ändert die Beschreibung (Zeile 128):
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

**Ergebnis:** DSPy erstellt automatisch den Prompt neu basierend auf der Beschreibung.

---

## 8. DSPy Critique Signature erweitern

**Datei:** `app/workflows/dspy_pipeline.py`

**Was ändern:**
- Sucht `class Critique` (Zeile 136)
- Erweitert die Rubric (Zeile 137):
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

**Ergebnis:** Die Critique enthält eine zusätzliche Bewertungskategorie.

---

## 9. DSPy Target Length als Input hinzufügen

**Datei:** `app/workflows/dspy_pipeline.py`

**Was ändern:**

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

**Ergebnis:** Ihr steuert die Länge über einen Parameter.

---

## 10. Reader Prompt anpassen

**Datei:** `app/agents/reader.py`

**Was ändern:**
- Sucht `READER_PROMPT` (Zeile 11)
- Ändert die Anweisung für "Results" (Zeile 20-21):
  ```python
  # Vorher:
  "Results:\n"
  "<EITHER list quantitative outcomes as bullets OR write exactly: No quantitative metrics reported in provided text.>\n"
  
  # Nachher (mehr Details):
  "Results:\n"
  "<EITHER list at least 3 quantitative outcomes as bullets with full context (model, dataset, metric, value) OR write exactly: No quantitative metrics reported in provided text.>\n"
  ```

**Ergebnis:** Der Reader extrahiert mehr/weniger Details aus den Ergebnissen.

---

## 11. Error Handling testen

**Datei:** `app/workflows/langchain_pipeline.py`

**Was ändern:**
- Sucht die Funktion `run_pipeline` (Zeile 21)
- Testet mit leerem Input:
  ```python
  # In der UI: Leeres Textfeld oder sehr kurzer Text (< 100 Zeichen)
  ```
- Beobachtet die Fehlerbehandlung (Zeile 40-43)

**Ergebnis:** Ihr seht, wie die Pipeline mit ungültigen Eingaben umgeht.

---

## 12. Telemetrie analysieren

**Datei:** `app/telemetry.py` (optional)

**Was ändern:**
- Öffnet `telemetry.csv` nach mehreren Pipeline-Läufen
- Analysiert die Spalten:
  - `latency_s`: Gesamtlaufzeit
  - `reader_s`, `summarizer_s`, `critic_s`, `integrator_s`: Zeiten pro Agent
  - `extracted_metrics_count`: Anzahl gefundener Metriken
  - `critic_loops`: Anzahl Loops (nur LangGraph)

**Ergebnis:** Ihr identifiziert Bottlenecks und Performance-Unterschiede.

---

## Tipps

1. **Speichern, dann testen:** Änderungen werden erst nach Speichern wirksam
2. **Bei Syntaxfehlern:** Prüft Einrückungen und Anführungszeichen
3. **App neu starten:** Wenn Änderungen nicht wirken, Streamlit neu starten
4. **Nur eine Änderung pro Test:** Macht es einfacher, die Auswirkungen zu verstehen
5. **Backup behalten:** Behaltet eine Kopie der Original-Dateien
6. **Terminal beobachten:** Fehlermeldungen erscheinen im Terminal, nicht immer in der UI

---

## Häufige Fehler

**"Module not found"**
- Prüft, ob ihr im richtigen Verzeichnis seid
- Prüft, ob alle Imports korrekt sind

**"AttributeError: 'str' object has no attribute 'content'"**
- Das LLM gibt manchmal Strings statt Objekte zurück
- `getattr(llm_response, "content", llm_response)` behandelt beide Fälle

**"Timeout"**
- LLM-Aufruf dauert zu lange
- Erhöht den Timeout oder verwendet ein schnelleres Modell

**"Empty response"**
- LLM gibt keine Antwort
- Prüft API-Key und Modell-Verfügbarkeit
