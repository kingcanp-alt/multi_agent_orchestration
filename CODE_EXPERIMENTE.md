# Code-Experimente für den Workshop
## Konkrete Code-Snippets zum Kopieren und Anpassen

Diese Datei enthält Code-Snippets, die ihr direkt in eure Dateien kopieren könnt.

---

## Experiment 1: Summarizer-Prompt ändern

**Datei:** `agents/summarizer.py`

**Original (Zeile 10):**
```python
"Produce a concise scientific summary (200-300 words) of the paper described in the NOTES. "
```

**Variante 1 - Kürzer:**
```python
"Produce a very brief scientific summary (50-100 words) of the paper described in the NOTES. "
```

**Variante 2 - Länger:**
```python
"Produce a detailed scientific summary (400-500 words) of the paper described in the NOTES. "
```

**Variante 3 - Fokus auf Ergebnisse:**
```python
"Produce a concise scientific summary (200-300 words) focusing mainly on RESULTS and METRICS from the NOTES. "
```

**Was passiert:** Die Summary-Länge und der Fokus ändern sich entsprechend.

---

## Experiment 2: Critic-Rubric erweitern

**Datei:** `agents/critic.py`

**Original (Zeile 13-17):**
```python
"RUBRIC (0-5 integers):\n"
"- Coherence: logical flow, no contradictions.\n"
"- Groundedness: claims are supported by NOTES.\n"
"- Coverage: objective, method, results, limitations are covered.\n"
"- Specificity: salient details included when NOTES provide them (especially metrics if present; if metrics are missing in SUMMARY but exist in NOTES, lower the score; if NOTES have no metrics, do not reward high specificity).\n\n"
```

**Hinzufügen - Neue Kategorie:**
```python
"RUBRIC (0-5 integers):\n"
"- Coherence: logical flow, no contradictions.\n"
"- Groundedness: claims are supported by NOTES.\n"
"- Coverage: objective, method, results, limitations are covered.\n"
"- Specificity: salient details included when NOTES provide them (especially metrics if present; if metrics are missing in SUMMARY but exist in NOTES, lower the score; if NOTES have no metrics, do not reward high specificity).\n"
"- Clarity: how easy is it to understand, appropriate technical level.\n\n"
```

**Und in der Ausgabe (Zeile 19-22) hinzufügen:**
```python
"OUTPUT FORMAT (exactly, no extra text):\n"
"Coherence: <0-5>\n"
"Groundedness: <0-5>\n"
"Coverage: <0-5>\n"
"Specificity: <0-5>\n"
"Clarity: <0-5>\n"
```

**Was passiert:** Der Critic bewertet jetzt auch nach Klarheit.

---

## Experiment 3: LangChain Reihenfolge ändern

**Datei:** `workflows/langchain_pipeline.py`

**Original (Zeilen 33-52):**
```python
structured_notes = run_reader(analysis_context)
summary = run_summarizer(structured_notes)
critic_result = run_critic(notes=structured_notes, summary=summary)
meta_summary = run_integrator(notes=structured_notes, summary=summary, critic=critic_text)
```

**Experiment - Critic vor Summarizer:**
```python
structured_notes = run_reader(analysis_context)
critic_result = run_critic(notes=structured_notes, summary="")  # Leere Summary!
summary = run_summarizer(structured_notes)
meta_summary = run_integrator(notes=structured_notes, summary=summary, critic=critic_text)
```

**Was passiert:** Der Critic läuft mit leerer Summary. Das zeigt, dass die Reihenfolge wichtig ist und LangChain die Abhängigkeiten nicht explizit macht.

---

## Experiment 4: Neuen Node zu LangGraph hinzufügen

**Datei:** `workflows/langgraph_pipeline.py`

### Schritt 1: PipelineState erweitern

**Original (Zeile 24-39) - Fügt hinzu:**
```python
class PipelineState(TypedDict):
    input_text: str
    analysis_context: str
    notes: str
    summary: str
    critic: str
    meta: str
    summary_de: str  # NEU HINZUGEFÜGT
    reader_s: float
    # ... rest bleibt gleich
```

### Schritt 2: Node-Funktion erstellen

**Nach Zeile 161 einfügen:**
```python
def _execute_translator_node(state: PipelineState) -> PipelineState:
    """Graph-Knoten: Übersetzt die Summary ins Deutsche."""
    start_time = perf_counter()
    timeout_seconds = state.get("_timeout", 45)
    
    # Einfacher Platzhalter (später könnt ihr einen echten LLM-Call machen)
    summary_en = state.get("summary", "") or ""
    summary_de = f"[DE] {summary_en[:100]}..."  # Platzhalter
    
    state["summary_de"] = summary_de
    state["translator_s"] = round(perf_counter() - start_time, 2)
    return state
```

### Schritt 3: Node zum Graph hinzufügen

**In `_build_langgraph_workflow` (nach Zeile 195):**
```python
graph.add_node("translator", _execute_translator_node)
```

### Schritt 4: Edges anpassen

**Entfernt (Zeile 199):**
```python
# graph.add_edge("summarizer", "critic")  # Auskommentieren
```

**Fügt hinzu:**
```python
graph.add_edge("summarizer", "translator")
graph.add_edge("translator", "critic")
```

**Was passiert:** Der Graph hat jetzt einen neuen Translator-Node zwischen Summarizer und Critic. Ihr seht ihn in der Visualisierung.

---

## Experiment 5: Conditional Edge in LangGraph

**Datei:** `workflows/langgraph_pipeline.py`

### Routing-Funktion erstellen

**Nach Zeile 162 einfügen (vor `_build_langgraph_workflow`):**
```python
def should_skip_quality(state: PipelineState) -> str:
    """Entscheidet, ob Quality-Step übersprungen wird."""
    summary = state.get("summary", "") or ""
    
    # Einfache Bedingung: Wenn Summary sehr kurz ist, überspringe Quality
    if len(summary) < 100:
        return "judge"  # Überspringe Quality, gehe direkt zu Judge
    else:
        return "quality"  # Normale Route über Quality
```

### Conditional Edge einfügen

**In `_build_langgraph_workflow` - Ersetzt Zeile 200:**
```python
# Alte Zeile auskommentieren:
# graph.add_edge("critic", "quality")

# Neue Conditional Edge:
graph.add_conditional_edges("critic", should_skip_quality)
```

**Fügt die entsprechenden Edges hinzu (nach Zeile 201):**
```python
graph.add_edge("quality", "judge")  # Falls Quality ausgeführt wird
# Falls direkt zu Judge geht, ist die Edge schon da (Zeile 201)
```

**Was passiert:** Bei sehr kurzen Summaries wird der Quality-Step übersprungen. Der Graph verzweigt sich basierend auf Bedingungen.

---

## Experiment 6: DSPy Signature ändern

**Datei:** `workflows/dspy_pipeline.py`

### Summarize Signature ändern

**Original (Zeile 85-88):**
```python
class Summarize(dspy.Signature):
    """Grounded 200-300 word summary from NOTES with takeaways."""
    NOTES: str = dspy.InputField()
    SUMMARY: str = dspy.OutputField()
```

**Variante 1 - Kürzer:**
```python
class Summarize(dspy.Signature):
    """Grounded 100-150 word very brief summary from NOTES with key points only."""
    NOTES: str = dspy.InputField()
    SUMMARY: str = dspy.OutputField()
```

**Variante 2 - Fokus auf Ergebnisse:**
```python
class Summarize(dspy.Signature):
    """Grounded 200-300 word summary from NOTES focusing on RESULTS and METRICS."""
    NOTES: str = dspy.InputField()
    SUMMARY: str = dspy.OutputField()
```

**Was passiert:** DSPy generiert automatisch einen neuen Prompt basierend auf der geänderten Beschreibung. Ihr müsst den Prompt nicht manuell ändern.

---

## Experiment 7: Neues Feld zur DSPy Signature hinzufügen

**Datei:** `workflows/dspy_pipeline.py`

### Summarize Signature erweitern

**Original (Zeile 85-88) - Ändern zu:**
```python
class Summarize(dspy.Signature):
    """Grounded summary from NOTES with takeaways. Length depends on TARGET_LENGTH."""
    NOTES: str = dspy.InputField()
    TARGET_LENGTH: str = dspy.InputField(desc="Target length: short, medium, or long")
    SUMMARY: str = dspy.OutputField()
```

### Verwendung anpassen

**Findet die SummarizerM.forward Methode (Zeile 131-146). Ändert:**
```python
def forward(self, notes: str, target_length: str = "medium"):
    tpl = (
        "Objective: <1-2 sentences>\n"
        "Method: <2-4 sentences>\n"
        "Results: <numbers if present; else 'not reported'>\n"
        "Limitations: <short>\n"
        "Takeaways:\n- <bullet>\n- <bullet>\n- <bullet>\n"
    )
    prompt = (
        f"Write a grounded {'brief' if target_length == 'short' else 'detailed' if target_length == 'long' else ''} "
        f"summary from NOTES. Target length: {target_length}. "
        "Use the following template, no JSON, no citations. "
        "Return ONLY the filled template.\n\n"
        f"TEMPLATE:\n{tpl}\n\nNOTES:\n{notes}"
    )
    out = self.gen(NOTES=prompt, TARGET_LENGTH=target_length)
    return dspy.Prediction(SUMMARY=_sanitize(out.SUMMARY))
```

**Und in PaperPipeline.forward (Zeile 197-215) anpassen:**
```python
summary = self.summarizer(notes, "short").SUMMARY  # oder "medium" oder "long"
```

**Was passiert:** Ihr könnt jetzt die Ziel-Länge als Parameter übergeben. Das zeigt, wie Signatures erweitert werden können.

---

## Tipps für die Experimente

1. **Immer speichern** bevor ihr die Pipeline ausführt
2. **Bei Fehlern:** Prüft die Syntax, besonders Einrückungen
3. **Falls Änderungen nicht übernommen werden:** Wartet ein paar Sekunden oder startet die App neu
4. **Backup machen:** Falls etwas nicht funktioniert, könnt ihr die Original-Dateien wiederherstellen
5. **Kleine Schritte:** Ändert immer nur eine Sache auf einmal, dann testet

---

## Erwartete Ergebnisse

- **Experiment 1:** Summary-Länge ändert sich
- **Experiment 2:** Critic bewertet zusätzlich nach Klarheit
- **Experiment 3:** Kritik funktioniert nicht richtig (zeigt Abhängigkeiten)
- **Experiment 4:** Neuer Node erscheint im Graph
- **Experiment 5:** Graph verzweigt sich basierend auf Bedingung
- **Experiment 6:** Summary ändert sich, auch ohne expliziten Prompt
- **Experiment 7:** Summary-Länge kann als Parameter gesteuert werden

Viel Spaß beim Experimentieren!

