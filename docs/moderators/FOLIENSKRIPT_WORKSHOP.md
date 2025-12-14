# Folienskript (Moderator) – Multi-Agent Paper Analyzer (60 Min)

Ziel: Ein verständlicher, durchgehbarer Ablauf mit wenigen Theorie-Slides, dann Live-Demo/Code, dann Aufgaben (Verständnis + Grenzen) und Wrap-Up.

**Voraussetzung:** App läuft (`python -m streamlit run app/app.py`) oder Start per `scripts/launchers/run.*`.  
**Teilnehmer-Unterlagen:** `docs/participants/START_HIER.md`, `docs/participants/TEILNEHMER_SKRIPT.md`

---

## 0) Aufbau & Timing (für dich)

- **Einleitung:** 5 Min (Slides + 1 Mini-Demo)
- **Praxis:** 50 Min (LangChain → LangGraph → DSPy, jeweils: Prinzip → Code → Aufgaben)
- **Wrap-Up:** 5 Min (Erkenntnisse, Transfer, Q&A)

Wenn ihr bei Setup/Netzwerk hängt: sofort auf „Code-Walkthrough ohne Ausführen“ umschwenken (Screenshots/Beispiel-Outputs helfen).

---

## Slide 1 – Titel & Ziel (0:00–0:45)

**Slide-Inhalt**
- Multi-Agent Orchestration am Beispiel „Paper Analyzer“
- 3 Paradigmen: LangChain (linear), LangGraph (graph), DSPy (deklarativ)

**Sprechtext (kurz)**
„Heute bauen wir nicht *ein* großes Prompt-Monster, sondern orchestrieren mehrere spezialisierte Schritte. Ziel ist, dass ihr am Ende die drei Paradigmen unterscheiden und bewusst auswählen könnt.“

**Plenum-Frage**
- „Wer hat schon mal mehrere LLM-Calls hintereinander verkettet? Was ging dabei schief (Halluzinationen, Abhängigkeiten, Debugging…)?“

---

## Slide 2 – Lernziele (0:45–1:30)

**Slide-Inhalt**
- Prinzip: Zerlegen → Orchestrieren → Bewerten → Integrieren
- Im Code wiederfinden: Agenten (`app/agents/*`) + Workflows (`app/workflows/*`)
- Aufgabenarten:
  1) **Verständnis** (warum passiert das?)
  2) **Grenzen** (wann klappt es schlecht/nicht?)

**Sprechtext**
„Wir arbeiten immer gleich: erst Prinzip erklären, dann zeigen wo es im Code steckt, dann erst Aufgaben.“

---

## Slide 3 – Pipeline als mentale Landkarte (1:30–2:30)

**Slide-Inhalt (Diagramm)**
- Reader → Summarizer → Critic → Integrator

**Sprechtext**
„Reader extrahiert *Ground Truth Notes*. Summarizer baut daraus eine Summary. Critic bewertet Summary gegen Notes. Integrator erzeugt eine Meta-Summary *mit Critic-Signal*, aber weiterhin strikt grounded in Notes.“

**Code-Anchor**
- Reader: `app/agents/reader.py` (`READER_PROMPT`, `run()`)
- Summarizer: `app/agents/summarizer.py`
- Critic: `app/agents/critic.py`
- Integrator: `app/agents/integrator.py`

---

## Slide 4 – Live-Demo in 90 Sekunden (2:30–4:00)

**Demo-Schritte**
1. App öffnen: Tab „Analysis“
2. 1 kurzes PDF/TXT hochladen
3. Pipeline „LangChain“ auswählen
4. „Analyze“ klicken → Ergebnis-Blöcke zeigen (Meta Summary, Summary, Notes, Critic, Timing)

**Sprechtext**
„Achtet auf zwei Dinge: (1) die Artefakte pro Stage (Notes/Summary/Critic/Meta) und (2) Timing/Telemetry – das brauchen wir später, um Trade-offs zu diskutieren.“

**Plenum-Frage**
- „Welcher Schritt dürfte hier am teuersten/slowsten sein – Reader oder Summarizer? Warum?“

---

## Slide 5 – Praxis-Regeln (4:00–5:00)

**Slide-Inhalt**
- Änderungen: immer *eine* Sache ändern → erneut ausführen → Effekt beobachten
- Debug-Hilfe: App-„Debug Mode“ aktivieren
- Wiederherstellung: Git oder Copy/Undo

**Sprechtext**
„Wir optimieren nicht ‚blind‘. Wir machen Hypothese → Änderung → Messung (Output + Timing).“

---

# Praxis-Teil (50 Min)

## Slide 6 – LangChain: Prinzip (5:00–7:00)

**Prinzip**
- Linearer Kontrollfluss: Step A liefert Input für Step B
- Abhängigkeiten sind *implizit* (durch Reihenfolge)

**Wo im Code?**
- `app/workflows/langchain_pipeline.py` (`run_pipeline()` ruft `run_reader` → `run_summarizer` → `run_critic` → `run_integrator` auf)

**Mini-Check**
- „Welche Daten fließen weiter? (Text → Notes → Summary → Critic → Meta)“

---

## Slide 7 – Aufgabe (Verständnis): Prompt-Wirkung (7:00–12:00)

**Aufgabe**
1. In `app/agents/summarizer.py` im `SUMMARIZER_PROMPT` „200-300 words“ auf „50-100 words“ ändern.
2. Pipeline „LangChain“ erneut ausführen.
3. Beobachten: Summary-Länge, Critic-Score/Improvements, Meta Summary.

**Diskussion im Plenum (2–3 kurze Stimmen)**
- „Welche Nebenwirkung hat ‚kürzer‘ auf Coverage/Specificity im Critic?“

**Grenzen-Hinweis**
- „Wenn Notes keine Zahlen enthalten, kann die Summary keine validen Metriken liefern – der Prompt erzwingt ‚not reported‘.“
- Ergänzend erwähnen: Die Tabelle unter „Alle Pipelines vergleichen“ zeigt jetzt ROUGE-1/ROUGE-2/ROUGE-L sowie Coverage/Coherence, sodass sich Prompt-Änderungen auch hinsichtlich Lexical Coverage und Satzkohärenz beurteilen lassen.

---

## Slide 8 – Aufgabe (Grenzen): Reihenfolge/Abhängigkeiten (12:00–15:00)

**Prinzip vorher**
„Der Critic kann nur bewerten, wenn er Notes **und** Summary hat.“

**Aufgabe**
- In `app/workflows/langchain_pipeline.py` den Critic *vor* den Summarizer ziehen (Summary ist dann leer/alt).
- Erwartung: Bewertung wird sinnlos oder bricht konzeptionell.

**Plenum-Frage**
- „Wie könnte man Abhängigkeiten sichtbar machen, ohne gleich auf LangGraph umzusteigen?“

---

## Slide 9 – LangGraph: Prinzip (15:00–18:00)

**Prinzip**
- Explizite Nodes + Edges + State
- Conditional Flow (Branches, Loops)
- Visualisierung: DOT/Graphviz

**Wo im Code?**
- `app/workflows/langgraph_pipeline.py`
  - `PipelineState` (welche Felder existieren)
  - `_build_langgraph_workflow()` (Nodes/Edges)
  - `_critic_post_path()` (Routing/Entscheidungen)

**Sprechtext**
„Hier sieht man Kontrolle als Graph: nicht nur Reihenfolge, sondern *Regeln* (wenn X, dann Y).“

---

## Slide 10 – Demo: Graph-Visualisierung lesen (18:00–20:00)

**Demo-Schritte**
1. Pipeline „LangGraph“ ausführen
2. Graph-Visualisierung zeigen (DOT wird als Chart gerendert)
3. Kurz erklären, was ein Branch bedeutet (z. B. „rework“ zurück zum Summarizer)

**Plenum-Frage**
- „Welche Kante wäre gefährlich, wenn sie unendlich loopen könnte? Wie begrenzen wir das?“

---

## Slide 11 – Aufgabe (Verständnis): State & Zusatz-Nodes (20:00–28:00)

**Aufgabe**
- In `app/workflows/langgraph_pipeline.py`:
  1. `_execute_translator_node` anschauen: schreibt `state["summary_translated"]`
  2. `_execute_keyword_node` anschauen: schreibt `state["keywords"]`
- Dann *eine* kleine Änderung machen und erneut ausführen (LangGraph):
  - Variante A (schnell): In `_execute_translator_node` die Defaults ändern (`language = ...`, `style = ...`), z. B. `EN` + `ultra_short`.
  - Variante B (optional): In `app/app.py` in der `config = {...}`-Dict zwei Keys ergänzen: `translator_language` und `translator_style`.

**Warum diese Aufgabe?**
„Ihr lernt: (1) State-Felder sind die ‚API‘ zwischen Nodes, (2) zusätzliche Nodes erhöhen Output-Artefakte ohne das Grundprinzip zu ändern.“

---

## Slide 12 – Aufgabe (Grenzen): Routing/Qualitätsschwellen (28:00–35:00)

**Prinzip vorher**
„Wir können *programmgesteuert* entscheiden, ob wir nochmal summarizen (Loop) oder direkt bewerten/aggregieren.“

**Aufgabe**
- In `app/workflows/langgraph_pipeline.py` Routing-Logik suchen (`_critic_post_path()`).
- 1 Schwelle bewusst ändern (z. B. „low critic“ empfindlicher machen) und erneut ausführen.
- Beobachten: `critic_loops`, Laufzeit, Output-Qualität.

**Plenum-Fragen**
- „Was passiert, wenn wir zu aggressiv loopen? (Kosten/Latenz/Overfitting auf Critic)“
- „Welche Signale sind robust genug für Routing – LLM-Score, F1-Heuristik, beides?“

---

## Slide 13 – DSPy: Prinzip (35:00–38:00)

**Prinzip**
- Statt Prompt-Strings pro Step: `dspy.Signature` beschreibt Inputs/Outputs + Constraints
- Optional: Teleprompting optimiert anhand eines Dev-Sets

**Wo im Code?**
- `app/workflows/dspy_pipeline.py`
  - Signatures: `ReadNotes`, `Summarize`, `Critique`, `Integrate`
  - Teleprompting: `_teleprompt_if_requested(...)`

**Sprechtext**
„DSPy verschiebt die Kontrolle: ihr beschreibt *was* rauskommen soll; DSPy hilft, *wie* das prompt-technisch am besten klappt.“

---

## Slide 14 – Aufgabe (Verständnis): Signature ändern (38:00–45:00)

**Aufgabe**
- In `app/workflows/dspy_pipeline.py` die Docstring-Beschreibung von `Summarize` so ändern, dass der Fokus klarer ist:
  - z. B. „Focus on Results and numeric metrics first“
- DSPy ausführen und beobachten: Output-Struktur ändert sich, obwohl kein Prompt-String editiert wurde.

**Grenzen-Hinweis**
- Wenn DSPy/LiteLLM nicht installiert: Stub-Modus erklärt das Konzept trotzdem über `meta` (keine Crashes).

---

## Slide 15 – Aufgabe (Grenzen): Teleprompting Trade-off (45:00–50:00)

**Prinzip vorher**
„Teleprompting = mehr Qualität gegen mehr Laufzeit/Komplexität, abhängig vom Dev-Set.“

**Aufgabe (falls Dev-Set vorhanden)**
1. In der App „Enable Teleprompting“ aktivieren
2. „Run Teleprompt Comparison“ starten
3. Ergebnis vergleichen: F1 Gain vs. Latenz
4. Tabs beobachten: `teleprompt_gain`, `teleprompt_target_lengths`, `teleprompt_prompt_focus` zeigen, welche Tags das Optimieren angestoßen haben; `meta` liefert `teleprompt_choice`.

**Plenum-Fragen**
- „Welche Art Dev-Beispiele würden Teleprompting *kaputt* machen? (biased, zu kurz, falsche Labels)“
- „Wie würdet ihr ein Dev-Set für *eure* Domäne bauen?“

---

# Wrap-Up (5 Min)

## Slide 16 – Die 3 Paradigmen (50:00–53:00)

**Kurzvergleich (1 Slide)**
- LangChain: schnell, linear, gut für Einstieg – aber implizite Abhängigkeiten
- LangGraph: expliziter Flow + Routing + Visualisierung – mehr Boilerplate, aber kontrollierbar
- DSPy: deklarativ + (optional) self-improving – braucht Dev-Set, andere Debugging-Logik

**Plenum-Frage**
- „Für welchen Use Case würdet ihr heute welches Paradigma wählen – und warum?“

---

## Slide 17 – Zentrale Erkenntnisse (53:00–55:00)

**Takeaways**
- Multi-Agent heißt: Artefakte pro Schritt → besser debuggbar als „ein Prompt“
- Qualität entsteht durch **Grounding** (Notes als Referenz) + **Feedback** (Critic) + **Kontrollfluss**
- Messbar machen: Timing/Telemetry + (optional) Quality-Heuristiken

**Code-Anchor**
- Preprocessing/Robustheit: `app/utils.py` (`build_analysis_context`, Meta/References stripping)
- Messung: `app/telemetry.py` (`log_row`)

---

## Slide 18 – Transfer: „Was würdet ihr als Nächstes ändern?“ (55:00–60:00)

**Diskussionsfragen**
- „Wenn wir jetzt einen *fünften Agenten* ergänzen (z. B. ‚FactChecker‘): Wo wäre der richtige Platz – und warum?“
- „Wenn wir strikt verhindern wollen, dass Summary Dinge erfindet: Wo setzen wir an (Reader-Prompt, Critic-Score, Routing, Output-Parser)?“
- „Welche Probleme entstehen, wenn das Input-Dokument riesig ist (Token-Limits, Zeit, Kosten) – und wie lösen wir das (Trunkierung, Section-Selection, Retrieval)?“

**Abschluss-Satz**
„Wenn ihr nur eine Sache mitnehmt: Erst Artefakte + Messung schaffen, dann optimieren.“
