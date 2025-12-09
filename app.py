"""
Streamlit App für Multi-Agent Paper Analyzer.

Unterstützt LangChain, LangGraph und DSPy Pipelines.
"""

import os
import io
import json
import copy
import streamlit as st
import pandas as pd
import altair as alt
from dotenv import load_dotenv
from pypdf import PdfReader

from workflows.langchain_pipeline import run_pipeline as run_lc
from workflows.langgraph_pipeline import run_pipeline as run_lg
from workflows.dspy_pipeline import run_pipeline as run_dspy, DSPY_READY
from utils import build_analysis_context

load_dotenv()
st.set_page_config(page_title="Paper Analyzer", layout="wide")
st.title("Paper Analyzer")

# Hilfe / Überblick
with st.expander("Hilfe"):
    st.markdown(
        """
**Was macht diese App?**  
Lädt Paper (PDF/TXT), erstellt einen abschnittsbasierten Analyse-Kontext und führt drei Orchestrierungs-Varianten aus:

- **LangChain (sequenziell):** Lineare Pipeline (Reader - Summarizer - Critic - Integrator). Einfach & schnell, wenig Boilerplate.
- **LangGraph (Graph):** Expliziter Graph mit Knoten/Kanten, deterministischer Kontrollfluss, sehr transparent (Graph-Ansicht).
- **DSPy (deklarativ):** Pipelines per "Signatures/Modules" definieren; optionales *Teleprompting* optimiert Prompts mit kleinem Dev-Set.

**Kontextfenster (LLM):**  
Große Dokumente passen evtl. nicht vollständig in das Modell-Kontextfenster. Das **Analyse-Budget** begrenzt deshalb den Input.  
Tipp: Passe bei Bedarf `Max Tokens` und `Max Eingabe (Zeichen)` an.

**Telemetry (CSV):**  
Schreibt u. a. `engine`, `input_chars`, `summary_len`, `meta_len`, `latency_s` sowie Schrittzeiten (`reader_s`, etc.) in `telemetry.csv`.

**DSPy-Teleprompting:**  
Mit Dev-Set (JSONL) kann die Summarizer-Stage leichtgewichtig optimiert werden (Few-Shot-Bootstrapping). Erst Dev-Set wählen, dann Häkchen setzen.
        """
    )

# Sidebar Settings
with st.sidebar:
    st.markdown("### Settings")

    preset = st.radio(
        "Preset",
        ["Speed", "Balanced", "Detail"],
        index=1,
        help=(
            "Wählt ein Profil für Geschwindigkeit vs. Detailtiefe:\n"
            "Speed: schnellere Laufzeit, weniger Kontext\n"
            "Balanced: ausgewogener Standard\n"
            "Detail: mehr Kontext, längere Antworten"
        ),
        horizontal=True
    )

    # Preset-Werte setzen
    if preset == "Speed":
        default_max_tokens = 160
        default_temperature = 0.0
    elif preset == "Balanced":
        default_max_tokens = 256
        default_temperature = 0.1
    else:  # Detail
        default_max_tokens = 384
        default_temperature = 0.15

    model = st.selectbox(
        "Model",
        ["gpt-4.1", "gpt-4o-mini"],
        index=0,
        help="OpenAI-Modell für alle Pipeline-Schritte.",
    )

    max_tokens = st.slider(
        "Max Tokens",
        64, 1024, default_max_tokens, 32,
        help="Maximale Token-Anzahl pro Schritt. Mehr = längere Antworten, aber langsamer.",
    )

    temperature = st.slider(
        "Temperature",
        0.0, 1.0, default_temperature, 0.05,
        help="Steuert Kreativität/Varianz des Modells. 0.0 = deterministisch, 1.0 = kreativer.",
    )

    timeout_seconds = st.slider(
        "Timeout (Sek)",
        10, 300, 60, 5,
        help="Maximale Wartezeit pro Schritt in Sekunden.",
    )

    st.sidebar.markdown("### DSPy")

    use_dspy_teleprompt = st.checkbox(
        "DSPy optimieren",
        value=False,
        help="Aktiviert automatische Prompt-Optimierung. Benötigt Dev-Set.",
    )

    dspy_dev_path = st.text_input(
        "Dev-Set Pfad",
        value="eval/dev.jsonl",
        help="Pfad zur JSONL-Datei mit Trainingsdaten.",
    )

    st.markdown("---")
    show_debug = st.toggle("Debug anzeigen", value=False)

# Config zusammenstellen
config = {
    "model": model,
    "max_tokens": int(max_tokens),
    "temperature": float(temperature),
    "timeout": int(timeout_seconds),
    "api_base": os.getenv("OPENAI_BASE_URL"),
    "debug": bool(show_debug),
    "dspy_teleprompt": use_dspy_teleprompt,
    "dspy_dev_path": dspy_dev_path,
}

# Pipeline-Auswahl
pipeline_mode = st.radio(
    "Pipeline",
    ["LangChain", "LangGraph", "DSPy"],
    horizontal=True,
    help=(
        "LangChain: einfach und schnell\n"
        "LangGraph: mit Graph-Visualisierung\n"
        "DSPy: mit automatischer Optimierung"
    ),
)

if pipeline_mode == "DSPy" and not DSPY_READY:
    st.warning("DSPy ist nicht installiert/konfiguriert (dspy-ai + litellm fehlen). Ergebnisse fallen auf Stub zurück.")

# File Upload
uploaded_files = st.file_uploader(
    "Datei hochladen",
    type=["pdf", "txt"],
    accept_multiple_files=True,
    help="PDF oder TXT-Dateien hochladen.",
)


def extract_pdf_text(file_handle) -> str:
    """Extrahiert Text aus PDF, bevorzugt mit pdfplumber für bessere Layout/Tabelle-Erkennung."""
    # Versuch mit pdfplumber (falls installiert)
    try:
        import pdfplumber  # type: ignore
        try:
            with pdfplumber.open(file_handle) as pdf:
                pages = []
                for page in pdf.pages:
                    pages.append(page.extract_text(x_tolerance=1, y_tolerance=1) or "")
                text = "\n\n".join(pages).strip()
                if text:
                    return text
        except Exception:
            pass  # Fallback zu pypdf
    except Exception:
        pass  # pdfplumber nicht installiert
    # Fallback: pypdf
    try:
        reader = PdfReader(file_handle)
        return "\n\n".join((page.extract_text() or "") for page in reader.pages).strip()
    except Exception as e:
        return f"[PDF error] {e}"


def read_uploaded_files(files) -> str:
    """Liest alle hochgeladenen Dateien und kombiniert sie."""
    if not files:
        return ""

    text_chunks = []
    for file in files:
        try:
            file_data = file.read()
            if file.type == "application/pdf" or file.name.lower().endswith(".pdf"):
                text_chunks.append(extract_pdf_text(io.BytesIO(file_data)))
            else:
                text_chunks.append(file_data.decode("utf-8", errors="ignore"))
        except Exception as e:
            text_chunks.append(f"[Error reading {file.name}: {e}]")

    return "\n\n".join(chunk for chunk in text_chunks if chunk).strip()


raw_text = read_uploaded_files(uploaded_files)

if uploaded_files:
    st.caption("Uploads:")
    for file in uploaded_files:
        st.write("-", file.name)

# Analysis Context erstellen
analysis_context = ""

if raw_text:
    analysis_context = build_analysis_context(raw_text, config)

# Preview
show_preview = st.checkbox(
    "Vorschau anzeigen",
    value=True,
    help="Zeigt den Text, der analysiert wird.",
)

if show_preview:
    st.markdown("#### Preview")
    st.caption(f"Characters in analysis context: {len(analysis_context)}")
    preview_text = analysis_context[:1200] + ("..." if len(analysis_context) > 1200 else "")
    st.text(preview_text)

# Run Button
run_col, compare_col, teleprompt_col, clear_col, _ = st.columns([1, 1.2, 1.4, 1, 4.4])
run_button = run_col.button("Starten", type="primary", help="Startet die Analyse.")
compare_button = compare_col.button("Alle Pipelines vergleichen", help="Führt LangChain, LangGraph und DSPy nacheinander auf demselben Kontext aus.")
teleprompt_button = teleprompt_col.button("DSPy Teleprompt Gain", help="Vergleicht DSPy Base vs. Teleprompting (Dev-Set notwendig).")

if clear_col.button("Löschen"):
    st.session_state.clear()

if run_button:
    if not analysis_context.strip():
        st.warning("Bitte mindestens eine PDF- oder TXT-Datei hochladen.")
    else:
        with st.status("Analysiere Dokument ... bitte warten", expanded=False) as status:
            try:
                if pipeline_mode == "LangChain":
                    pipeline_result = run_lc(analysis_context, config)
                elif pipeline_mode == "LangGraph":
                    pipeline_result = run_lg(analysis_context, config)
                else:
                    pipeline_result = run_dspy(analysis_context, config)

                status.update(label="Fertig.", state="complete")

                st.markdown("### Ergebnisse")
                st.markdown("**Zusammenfassung**")
                st.write(pipeline_result.get("meta", ""))

                st.markdown("**Summary**")
                st.code(pipeline_result.get("summary", ""), language="")

                st.markdown("**Notizen**")
                st.code(pipeline_result.get("structured", ""), language="")

                st.markdown("**Bewertung**")
                st.code(pipeline_result.get("critic", ""), language="")

                st.markdown("**Zeiten (Sekunden)**")
                st.write({
                    "reader_s": pipeline_result.get("reader_s", 0),
                    "summarizer_s": pipeline_result.get("summarizer_s", 0),
                    "critic_s": pipeline_result.get("critic_s", 0),
                    "integrator_s": pipeline_result.get("integrator_s", 0),
                })

                graph_dot = pipeline_result.get("graph_dot")
                if graph_dot and pipeline_mode == "LangGraph":
                    st.markdown("### Graph")
                    st.graphviz_chart(graph_dot, use_container_width=True)

                st.download_button(
                    "Als JSON herunterladen",
                    data=json.dumps(pipeline_result, ensure_ascii=False, indent=2),
                    file_name="paper_analysis.json",
                    mime="application/json",
                )
            except Exception as e:
                status.update(label=f"Error: {e}", state="error")
                st.error(str(e))

if compare_button:
    if not analysis_context.strip():
        st.warning("Bitte mindestens eine PDF- oder TXT-Datei hochladen.")
    else:
        with st.status("Vergleiche Pipelines ...", expanded=False) as status:
            results = {}
            errors = {}
            for label, runner in (
                ("LangChain", lambda: run_lc(analysis_context, config)),
                ("LangGraph", lambda: run_lg(analysis_context, config)),
                ("DSPy", lambda: run_dspy(analysis_context, config)),
            ):
                try:
                    results[label] = runner()
                except Exception as exc:
                    errors[label] = str(exc)
                    results[label] = {"meta": f"Error: {exc}"}
            status.update(label="Vergleich fertig.", state="complete")

        st.markdown("### Vergleich (LangChain vs. LangGraph vs. DSPy)")

        table_rows = []
        for label, res in results.items():
            table_rows.append({
                "engine": label,
                "latency_s": res.get("latency_s", 0.0),
                "reader_s": res.get("reader_s", 0.0),
                "summarizer_s": res.get("summarizer_s", 0.0),
                "critic_s": res.get("critic_s", 0.0),
                "integrator_s": res.get("integrator_s", 0.0),
                "summary_len": len(res.get("summary", "") or ""),
                "meta_len": len(res.get("meta", "") or ""),
                "quality_f1": res.get("quality_f1", None),
                "judge_score": res.get("judge_score", None),
            })

        df = pd.DataFrame(table_rows)
        st.dataframe(df, use_container_width=True)

        if not df.empty and "latency_s" in df:
            chart = (
                alt.Chart(df)
                .mark_bar()
                .encode(
                    x=alt.X("engine:N", title="Pipeline"),
                    y=alt.Y("latency_s:Q", title="Latenz (s)"),
                    color="engine:N",
                )
            )
            st.altair_chart(chart, use_container_width=True)

        tabs = st.tabs(list(results.keys()))
        for tab, label in zip(tabs, results.keys()):
            res = results[label]
            with tab:
                if label == "DSPy" and not DSPY_READY:
                    st.warning("DSPy nicht aktiviert (Stub). Installiere dspy-ai + litellm für echte Ausführung.")
                st.markdown("**Meta Summary**")
                st.write(res.get("meta", ""))
                st.markdown("**Summary**")
                st.code(res.get("summary", ""), language="")
                st.markdown("**Notizen**")
                st.code(res.get("structured", ""), language="")
                st.markdown("**Bewertung**")
                st.code(res.get("critic", ""), language="")
                if errors.get(label):
                    st.error(f"Fehler: {errors[label]}")

if teleprompt_button:
    if not DSPY_READY:
        st.warning("DSPy nicht installiert (dspy-ai + litellm).")
    elif not analysis_context.strip():
        st.warning("Bitte mindestens eine PDF- oder TXT-Datei hochladen.")
    else:
        st.markdown("### DSPy Teleprompting: Base vs. Optimiert")
        def _tokens(s: str) -> set[str]:
            import re
            s = (s or "").lower()
            s = re.sub(r"[^a-z0-9\s]", " ", s)
            return {t for t in s.split() if len(t) > 2}

        def _f1(gold: str, pred: str) -> float:
            G = _tokens(gold)
            P = _tokens(pred)
            if not G or not P:
                return 0.0
            inter = len(G & P)
            prec = inter / len(P)
            rec = inter / len(G)
            return 0.0 if (prec + rec) == 0 else (2 * prec * rec) / (prec + rec)

        base_cfg = copy.deepcopy(config)
        base_cfg["dspy_teleprompt"] = False
        tp_cfg = copy.deepcopy(config)
        tp_cfg["dspy_teleprompt"] = True

        with st.status("Führe DSPy (Base vs. Teleprompt) aus ...", expanded=False) as status:
            try:
                res_base = run_dspy(analysis_context, base_cfg)
                res_tp = run_dspy(analysis_context, tp_cfg)
                status.update(label="Fertig.", state="complete")
            except Exception as e:
                status.update(label=f"Error: {e}", state="error")
                st.error(str(e))
                res_base = res_tp = None

        if res_base and res_tp:
            rows = []
            for label, res in (("Base", res_base), ("Teleprompt", res_tp)):
                f1 = _f1(analysis_context, res.get("summary", "") or "")
                rows.append({
                    "variant": label,
                    "latency_s": res.get("latency_s", 0.0),
                    "summary_len": len(res.get("summary", "") or ""),
                    "meta_len": len(res.get("meta", "") or ""),
                    "f1_vs_context": round(f1, 3),
                })
            df_gain = pd.DataFrame(rows)
            st.dataframe(df_gain, use_container_width=True)

            if len(df_gain) == 2:
                gain = df_gain.iloc[1]["f1_vs_context"] - df_gain.iloc[0]["f1_vs_context"]
                st.info(f"Teleprompt F1 Gain vs. Base: {gain:+.3f}")
            tabs = st.tabs(["Base", "Teleprompt"])
            for tab, (label, res) in zip(tabs, (("Base", res_base), ("Teleprompt", res_tp))):
                with tab:
                    st.markdown(f"**Meta Summary ({label})**")
                    st.write(res.get("meta", ""))
                    st.markdown("**Summary**")
                    st.code(res.get("summary", ""), language="")
                    st.markdown("**Notizen**")
                    st.code(res.get("structured", ""), language="")
                    st.markdown("**Bewertung**")
                    st.code(res.get("critic", ""), language="")
# Telemetrie-Viewer
with st.expander("Telemetry (CSV)", expanded=False):
    telemetry_path = "telemetry.csv"
    if not os.path.exists(telemetry_path):
        st.caption("Keine telemetry.csv gefunden.")
    else:
        try:
            telemetry_df = pd.read_csv(telemetry_path)
            st.caption(f"Zeige letzte {min(len(telemetry_df), 200)} Einträge.")
            st.dataframe(telemetry_df.tail(200), use_container_width=True)
            if {"engine", "latency_s"} <= set(telemetry_df.columns):
                subset = telemetry_df[["engine", "latency_s"]].reset_index().rename(columns={"index": "run"})
                line = (
                    alt.Chart(subset.tail(200))
                    .mark_line(point=True)
                    .encode(
                        x=alt.X("run:Q", title="Run"),
                        y=alt.Y("latency_s:Q", title="Latenz (s)"),
                        color="engine:N",
                    )
                )
                st.altair_chart(line, use_container_width=True)
        except Exception as e:
            st.error(f"Telemetry konnte nicht geladen werden: {e}")
