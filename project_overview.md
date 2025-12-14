# Projekt Erklärung: Multi Agent Paper Analyzer

## Projektüberblick

Wir analysieren wissenschaftliche Texte mit vier spezialisierten Agenten:
- **Reader** liest das Dokument und extrahiert Notizen.
- **Summarizer** fasst die wichtigsten Aussagen zusammen.
- **Critic** bewertet, wie gut die Zusammenfassung ist.
- **Integrator** erstellt eine Meta-Zusammenfassung aus allem.

Der Workflow läuft in drei Frameworks:
- **LangChain**: Simple, sequenzielle Schritte.
- **LangGraph**: Graph basierte Steuerung und Visualisierung.
- **DSPy**: Deklarativ und automatisch optimierend (optional mit Teleprompting).

## Designentscheidungen

### Warum mehrere Agenten?
Ein großer Prompt → schwer zu kontrollieren. Mit einzelnen Agenten bleibt jede Aufgabe klar getrennt. Das erleichtert Debugging und Anpassung.

### Warum drei Frameworks?
- LangChain geht schnell und bleibt übersichtlich.
- LangGraph zeigt den Ablauf als Graph und lässt sich besser erweitern.
- DSPy übernimmt Optimierungsschritte automatisch durch Signaturen.

So lernen Teilnehmer verschiedene Stile kennen und entscheiden, welcher Ansatz zu ihrer Idee passt.

### Warum Streamlit?
Streamlit startet mit einem Befehl, zeigt Uploads, Buttons und Vergleiche direkt im Browser und macht die Arbeit interaktiv.

### Warum Text Vorverarbeitung?
PDFs enthalten oft störende Elemente (Metadaten, Literaturverzeichnis, seltsame Zeilenumbrüche). `utils.py` normalisiert den Text, damit die Agenten sauber arbeiten.

### Warum Telemetrie?
`telemetry.py` schreibt Laufzeiten und Textlängen in eine CSV. So kann man sehen, welche Pipeline schneller ist und wie groß die Outputs werden.

### Warum Doppelklick Start?
`run.bat` und `run.sh` übernehmen Setup, pip, `.env` und starten Streamlit. Das ist für Workshop-Teilnehmer der einfachste Weg.
