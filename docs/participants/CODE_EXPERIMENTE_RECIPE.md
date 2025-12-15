# Code Experimente (Recipe Book)

Diese Datei ist euer **Mitmach-Handbuch**: kurze, sichere Änderungen am Code, um Unterschiede zwischen **LangChain (sequentiell)**, **LangGraph (graphbasiert mit Bedingungen/Loops)** und **DSPy (deklarativ)** sichtbar zu machen.

**Wichtig:** Immer nur ein Experiment auf einmal ändern, dann testen. Wenn etwas schiefgeht, könnt ihr es einfach rückgängig machen.

---

## Zurücksetzen, wenn etwas schiefgeht

**Mit Git:**
```bash
git checkout -- <DATEI>
```

**Ohne Git:**
- Editor "Undo" nutzen
- Oder den Original-Code wieder zurückkopieren

---

## A) Einsteiger-Experimente (einfach und sicher)

### A1 — Summarizer kürzer oder länger machen

**Warum:** Der Prompt steuert direkt, wie lang die Summary wird. Einfach zu testen und sofort sichtbar.

**Datei:** `app/agents/summarizer.py`

**So geht's:**
1. Sucht `SUMMARIZER_PROMPT` (ca. Zeile 11)
2. Ändert Zeile 12:

```python
# Sehr kurz:
"Produce a very brief scientific summary (max 100 words) from NOTES. Do not invent facts. Do not include citations.\n\n"

# Oder detailliert:
"Produce a detailed scientific summary (300-500 words) from NOTES. Do not invent facts. Do not include citations.\n\n"
```

3. Speichern und Pipeline neu starten

**Was passiert:** Die Summary wird deutlich kürzer oder länger. Das zeigt, wie direkt Prompts das Ergebnis beeinflussen.

**Rückgängig:** Prompt wieder auf `"Produce a concise scientific summary..."` zurücksetzen

---

### A2 — Critic um "Clarity" erweitern

**Warum:** Ihr seht, wie einfach man Bewertungskriterien hinzufügen kann. Das ist nützlich, wenn ihr spezifische Aspekte bewerten wollt.

**Datei:** `app/agents/critic.py`

**So geht's:**
1. Sucht `CRITIC_PROMPT` (ca. Zeile 13)
2. Erweitert die Rubric (nach Zeile 25):

```python
"- Clarity: clear and easy to understand, no jargon overload.\n\n"
```

3. Erweitert das OUTPUT FORMAT (nach Zeile 30):

```python
"Clarity: <0-5>\n"
```

4. Speichern und Pipeline neu starten

**Was passiert:** Der Critic gibt jetzt auch einen Klarheitswert aus. Das zeigt, wie flexibel das Bewertungssystem ist.

**Rückgängig:** Clarity-Zeilen entfernen

---

### A3 — Reader: Results detaillierter extrahieren

**Warum:** Wenn der Reader mehr Details extrahiert, verbessert sich oft auch die Summary. Das zeigt, wie Upstream-Extraktion Downstream-Qualität beeinflusst.

**Datei:** `app/agents/reader.py`

**So geht's:**
1. Sucht `READER_PROMPT` (ca. Zeile 11)
2. Ändert die "Results"-Anweisung (Zeile 20-21):

```python
"Results:\n"
"<EITHER list at least 3 quantitative outcomes as bullets with full context (model, dataset, metric, value) OR write exactly: No quantitative metrics reported in provided text.>\n"
```

3. Speichern und Pipeline neu starten

**Was passiert:** Der Reader extrahiert mehr Details aus den Ergebnissen. Das kann die Critic-Scores verbessern, weil mehr Informationen verfügbar sind.

**Rückgängig:** Zur alten Results-Anweisung zurück

---

## B) Grenzen zeigen (gezielt "kaputt" machen)

### B1 — LangChain Reihenfolge brechen

**Warum:** Das zeigt die Grenzen sequenzieller Pipelines. Wenn die Reihenfolge falsch ist, funktioniert es nicht - und LangChain prüft das nicht automatisch.

**Datei:** `app/workflows/langchain_pipeline.py`

**So geht's:**
1. Sucht die Funktion `run_pipeline` (Zeile 21)
2. Verschiebt den Critic-Aufruf VOR den Summarizer (bewusst falsch):

```python
# FALSCH (nur für Demo):
critic_result = run_critic(notes=structured_notes, summary="")  # leere Summary
summary = run_summarizer(structured_notes)
```

3. Speichern und Pipeline starten

**Was passiert:** Der Critic bewertet eine leere Summary - die Scores sind schlecht und die Verbesserungsvorschläge sind generisch. Das zeigt, warum die Reihenfolge bei LangChain so wichtig ist.

**Rückgängig:** Wieder korrekt:
```python
summary = run_summarizer(structured_notes)
critic_result = run_critic(notes=structured_notes, summary=summary)
```

---

### B2 — LangGraph: Max Loops ändern

**Warum:** Loops erhöhen oft die Qualität, kosten aber Zeit und Tokens. Bei 0 ist es wie LangChain (keine Wiederholungen), bei 5 kann es mehrfach versuchen.

**Datei:** `app/app.py`

**So geht's:**
1. Sucht `max_critic_loops` (Zeile 191)
2. Ändert den Wert:

```python
"max_critic_loops": 0,   # keine Iteration (wie LangChain)
# oder
"max_critic_loops": 5,   # viele Iterationen
```

3. Speichern und Pipeline neu starten

**Was passiert:**
- Bei 0: schnell, aber oft schlechtere Critic-Scores
- Bei 5: langsamer, aber die Summary kann sich über mehrere Versuche verbessern

**Rückgängig:** Zurück auf Default (z. B. 2)

---

## C) LangGraph Verhalten steuern

### C1 — Conditional Threshold anpassen

**Warum:** Der Schwellenwert bestimmt, wie streng der Graph ist. Das ist der Kern von LangGraph - bedingte Entscheidungen.

**Datei:** `app/workflows/langgraph_pipeline.py`

**So geht's:**
1. Sucht die Funktion `_critic_post_path` (Zeile 185)
2. Ändert den Schwellenwert (Zeile 208):

```python
# strenger (mehr Loops):
if state["critic_score"] < 0.7 and loops < max_loops:

# lockerer (weniger Loops):
if state["critic_score"] < 0.3 and loops < max_loops:
```

3. Speichern und Pipeline neu starten

**Was passiert:** Bei 0.7 wird häufiger zurückgeroutet (strenger), bei 0.3 seltener (lockerer). Die Visualisierung zeigt die Unterschiede im Graph.

**Rückgängig:** Zurück auf Default (z. B. 0.5)

---

### C2 — Timeout anpassen

**Warum:** Manchmal hängen LLM-Aufrufe. Ein Timeout verhindert, dass die ganze Pipeline blockiert. Wichtig bei langsamen Modellen oder langen Texten.

**Datei:** `app/workflows/langgraph_pipeline.py`

**So geht's:**
1. Sucht die Funktion `run_pipeline` (Zeile 330)
2. Ändert den Timeout (Zeile 342):

```python
timeout_seconds = int(config_dict.get("timeout", 30))  # kürzer
# oder
timeout_seconds = int(config_dict.get("timeout", 60))  # länger
```

3. Speichern und Pipeline neu starten

**Was passiert:** Bei 30 Sekunden bricht es früher ab (gut für schnelle Tests), bei 60 wartet es länger (gut für langsame Modelle).

**Rückgängig:** Zurück auf Default (z. B. 45)

---

## D) DSPy: Deklarativ verändern

### D1 — DSPy Signature variieren

**Warum:** Das ist der Kern von DSPy - ihr beschreibt nur, was ihr wollt, und DSPy erzeugt den Prompt. Ändert ihr die Beschreibung, ändert sich der Prompt automatisch.

**Datei:** `app/workflows/dspy_pipeline.py`

**So geht's:**
1. Sucht `class Summarize` (Zeile 127)
2. Ändert die Beschreibung (Zeile 128):

**Variante "Results-first, sehr kurz":**
```python
"""Produce a very brief scientific summary (max 100 words) from NOTES, focusing primarily on RESULTS.
Include quantitative outcomes if present in NOTES. Otherwise write exactly 'No quantitative metrics reported in provided text.'
Avoid speculation or citations. Do NOT invent metrics."""
```

**Variante "Method-first, ausführlich":**
```python
"""Produce a detailed scientific summary from NOTES, focusing primarily on METHODOLOGY.
Explain what techniques were used, how they were applied, and what tools/frameworks were involved.
Include Results if present, but emphasize the methodological approach.
Avoid speculation or citations. Do NOT invent metrics."""
```

3. Speichern und Pipeline neu starten

**Was passiert:** DSPy erzeugt automatisch einen neuen Prompt basierend auf eurer Beschreibung. Die Summary verschiebt den Fokus sichtbar (mehr Results vs mehr Method).

**Rückgängig:** Beschreibung wieder auf Default zurück

---

### D2 — DSPy Critique erweitern

**Warum:** Genau wie bei LangChain könnt ihr Bewertungskriterien hinzufügen, aber hier macht ihr es in der Signature statt im Prompt.

**Datei:** `app/workflows/dspy_pipeline.py`

**So geht's:**
1. Sucht `class Critique` (Zeile 136)
2. Erweitert die Rubric (Zeile 137):

```python
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

3. Speichern und Pipeline neu starten

**Was passiert:** Die Critique enthält jetzt auch eine Klarheitsbewertung. Das zeigt, wie flexibel Signatures sind.

**Rückgängig:** Clarity wieder entfernen

---

## E) Beobachten und Analysieren

### E1 — Error Handling testen

**Warum:** Ihr seht, wie die Pipeline mit ungültigen Eingaben umgeht. Wichtig für robuste Anwendungen.

**Datei:** `app/workflows/langchain_pipeline.py`

**So geht's:**
1. Keinen Code ändern - nur testen
2. In der UI: Leeres Textfeld oder sehr kurzen Text (< 100 Zeichen) hochladen
3. Pipeline starten

**Was passiert:** Die Pipeline gibt eine verständliche Fehlermeldung zurück statt abzustürzen. Das zeigt, wie Error Handling funktioniert.

**Rückgängig:** entfällt

---

### E2 — Telemetrie analysieren

**Warum:** Die Telemetrie zeigt, wo die Zeit verbraucht wird. Das hilft, Bottlenecks zu finden und zu optimieren.

**Datei:** `telemetry.csv` (wird automatisch erstellt)

**So geht's:**
1. Führt mehrere Pipeline-Läufe aus (mind. 3 pro Pipeline)
2. Öffnet `telemetry.csv` oder den "CSV Telemetry Data" Expander in der UI
3. Analysiert die Spalten:
   - `latency_s`: Gesamtlaufzeit
   - `reader_s`, `summarizer_s`, `critic_s`, `integrator_s`: Zeiten pro Agent
   - `extracted_metrics_count`: Anzahl gefundener Metriken
   - `critic_loops`: Anzahl Loops (nur LangGraph)

**Was passiert:** Ihr seht, welcher Agent am längsten braucht und welche Pipeline am schnellsten ist. Das zeigt, wo Optimierungen am meisten helfen würden.

**Rückgängig:** entfällt

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
- Erhöht den Timeout (siehe Experiment C2) oder verwendet ein schnelleres Modell

**"Empty response"**
- LLM gibt keine Antwort
- Prüft API-Key und Modell-Verfügbarkeit
- Prüft, ob das Modell in der Config richtig eingestellt ist
