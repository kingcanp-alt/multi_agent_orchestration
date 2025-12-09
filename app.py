"""
Streamlit App for Multi-Agent Paper Analyzer.

Supports LangChain, LangGraph, and DSPy pipelines.
"""

import os
import io
import json
import copy
import time
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
st.set_page_config(
    page_title="Paper Analyzer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for tooltips
st.markdown("""
<style>
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 250px;
        background-color: #333;
        color: #fff;
        text-align: left;
        border-radius: 6px;
        padding: 8px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -125px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 12px;
        line-height: 1.4;
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

# === HEADER ===
st.title("Paper Analyzer")
st.caption("Multi-Agent Orchestration with LangChain, LangGraph & DSPy")

with st.expander("Help", expanded=False):
    st.markdown("""
    **Quick Start:**
    1. Upload a document (PDF/TXT)
    2. Select a pipeline
    3. Start analysis
    
    Hover over the question mark icons to see detailed explanations of each setting.
    """)

# === SIDEBAR: SETTINGS ===
with st.sidebar:
    st.markdown("### Settings")
    
    preset = st.radio(
        "Preset",
        ["Speed", "Balanced", "Detail"],
        index=1,
        help="Speed: Fast execution, fewer tokens (160), deterministic (temp=0.0)\n\nBalanced: Good trade-off (256 tokens, temp=0.1)\n\nDetail: Slower but more detailed (384 tokens, temp=0.15)",
    )
    
    if preset == "Speed":
        default_max_tokens = 160
        default_temperature = 0.0
    elif preset == "Balanced":
        default_max_tokens = 256
        default_temperature = 0.1
    else:  # Detail
        default_max_tokens = 384
        default_temperature = 0.15
    
    st.markdown("#### Model")
    
    model = st.selectbox(
        "Model",
        ["gpt-4o-mini", "gpt-4o"],
        index=0,
        help="gpt-4o-mini: Faster and cheaper, good for most tasks\n\ngpt-4o: More capable but slower and more expensive",
    )
    
    max_tokens = st.slider(
        "Max Tokens",
        64, 1024, default_max_tokens, 32,
        help="Maximum number of tokens the model can generate per step. Higher = longer responses but slower and more expensive. Typical range: 160-400.",
    )
    
    temperature = st.slider(
        "Temperature",
        0.0, 1.0, default_temperature, 0.05,
        help="Controls randomness in responses:\n\n0.0 = Deterministic, same input always gives same output\n0.1-0.3 = Slightly creative, good for structured tasks\n0.7-1.0 = Very creative, more variation",
    )
    
    st.markdown("#### DSPy Optimization")
    
    use_dspy_teleprompt = st.checkbox(
        "Enable Teleprompting",
        value=False,
        help="DSPy Teleprompting automatically optimizes prompts using examples from a dev set. It uses BootstrapFewShot to find better prompt examples. Requires a JSONL file with input-output pairs.",
    )
    
    if use_dspy_teleprompt:
        dspy_dev_path = st.text_input(
            "Dev-Set Path",
            value="eval/dev.jsonl",
            help="Path to JSONL file containing training examples. Each line must be a JSON object with input text and expected summary. The system uses this file for prompt optimization.",
        )
        if not os.path.exists(dspy_dev_path):
            st.warning(f"File not found: {dspy_dev_path}")
    else:
        dspy_dev_path = "eval/dev.jsonl"
    
    show_debug = st.checkbox("Debug Mode", value=False, help="Show detailed error messages and stack traces when errors occur. Useful for troubleshooting.")

# Config
config = {
    "model": model,
    "max_tokens": int(max_tokens),
    "temperature": float(temperature),
    "timeout": 60,
    "api_base": os.getenv("OPENAI_BASE_URL"),
    "debug": bool(show_debug),
    "dspy_teleprompt": use_dspy_teleprompt,
    "dspy_dev_path": dspy_dev_path,
}

# === MAIN TABS ===
tab_analyse, tab_vergleich, tab_teleprompt = st.tabs(["Analysis", "Compare", "DSPy Optimization"])

# === TAB 1: ANALYSIS ===
with tab_analyse:
    st.markdown("### Upload Document")
    
    uploaded_files = st.file_uploader(
        "Select PDF or TXT file",
        type=["pdf", "txt"],
        accept_multiple_files=True,
    )
    
    if uploaded_files:
        st.success(f"{len(uploaded_files)} file(s) uploaded")
        for file in uploaded_files:
            file_size_mb = file.size / (1024 * 1024)
            st.caption(f"{file.name} ({file_size_mb:.2f} MB)")
    
    # Pipeline selection
    st.markdown("### Select Pipeline")
    pipeline_mode = st.radio(
        "Pipeline",
        ["LangChain", "LangGraph", "DSPy"],
        horizontal=True,
        help="LangChain: Sequential pipeline, simple and fast. Linear flow: Reader → Summarizer → Critic → Integrator.\n\nLangGraph: Graph-based orchestration with explicit control flow. Includes quality metrics and visualization.\n\nDSPy: Declarative pipeline using signatures. Can optimize prompts automatically with teleprompting.",
    )
    
    if pipeline_mode == "DSPy" and not DSPY_READY:
        st.warning("DSPy not installed. Install `dspy-ai` and `litellm` for full functionality.")
    
    # Text processing
    def extract_pdf_text(file_handle) -> str:
        try:
            import pdfplumber
            try:
                with pdfplumber.open(file_handle) as pdf:
                    pages = [page.extract_text(x_tolerance=1, y_tolerance=1) or "" for page in pdf.pages]
                    text = "\n\n".join(pages).strip()
                    if text:
                        return text
            except Exception:
                pass
        except Exception:
            pass
        try:
            reader = PdfReader(file_handle)
            return "\n\n".join((page.extract_text() or "") for page in reader.pages).strip()
        except Exception as e:
            return f"[PDF error] {e}"
    
    def read_uploaded_files(files) -> str:
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
    analysis_context = ""
    
    if raw_text:
        analysis_context = build_analysis_context(raw_text, config)
        with st.expander("Preview", expanded=False):
            st.caption(f"Characters in analysis context: {len(analysis_context):,}")
            preview_text = analysis_context[:2000] + ("..." if len(analysis_context) > 2000 else "")
            st.text_area("", preview_text, height=150, disabled=True, label_visibility="collapsed")
    
    # Analyze button
    if st.button("Analyze", type="primary", use_container_width=True, disabled=not uploaded_files):
        if not analysis_context.strip():
            st.error("Please upload a file first!")
        else:
            pipeline_result = None
            try:
                with st.status("Analyzing document...", expanded=True) as status:
                    if pipeline_mode == "LangChain":
                        status.update(label="Running LangChain...", state="running")
                        pipeline_result = run_lc(analysis_context, config)
                    elif pipeline_mode == "LangGraph":
                        status.update(label="Running LangGraph...", state="running")
                        pipeline_result = run_lg(analysis_context, config)
                    else:
                        status.update(label="Running DSPy...", state="running")
                        if use_dspy_teleprompt:
                            status.update(label="Optimizing with Teleprompting...", state="running")
                        pipeline_result = run_dspy(analysis_context, config)
                    
                    status.update(label="Analysis complete!", state="complete")
                
                # Display results
                if pipeline_result:
                    st.markdown("## Results")
                    
                    # Metrics
                    col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)
                    with col_meta1:
                        st.metric("Total Time", f"{pipeline_result.get('latency_s', 0):.2f}s", help="Total execution time for the entire pipeline in seconds")
                    with col_meta2:
                        summary_len = len(pipeline_result.get("summary", "") or "")
                        st.metric("Summary Length", f"{summary_len:,} chars", help="Number of characters in the generated summary")
                    with col_meta3:
                        meta_len = len(pipeline_result.get("meta", "") or "")
                        st.metric("Meta Length", f"{meta_len:,} chars", help="Number of characters in the meta summary (final integrated summary)")
                    with col_meta4:
                        f1 = pipeline_result.get("quality_f1", None)
                        if f1 is not None:
                            st.metric("F1 Score", f"{f1:.3f}", help="F1 score measures overlap between notes and summary. Higher is better (0-1 range). Only available for LangGraph.")
                        else:
                            st.metric("F1 Score", "N/A", help="F1 score is not available for this pipeline")
                    
                    # Meta Summary
                    if pipeline_result.get("meta"):
                        st.markdown("### Meta Summary")
                        st.info(pipeline_result.get("meta"))
                    
                    # Summary
                    if pipeline_result.get("summary"):
                        st.markdown("### Summary")
                        st.markdown(pipeline_result.get("summary"))
                    
                    # Timing details
                    st.markdown("### Timing")
                    times = {
                        "Reader": pipeline_result.get('reader_s', 0),
                        "Summarizer": pipeline_result.get('summarizer_s', 0),
                        "Critic": pipeline_result.get('critic_s', 0),
                        "Integrator": pipeline_result.get('integrator_s', 0),
                    }
                    cols = st.columns(len(times))
                    for col, (key, value) in zip(cols, times.items()):
                        with col:
                            st.metric(key, f"{value:.2f}s")
                    
                    # Notes & Critic in expanders
                    col_notes, col_critic = st.columns(2)
                    with col_notes:
                        if pipeline_result.get("structured"):
                            with st.expander("Notes", expanded=False):
                                st.code(pipeline_result.get("structured"), language="")
                    
                    with col_critic:
                        if pipeline_result.get("critic"):
                            with st.expander("Critic", expanded=False):
                                st.code(pipeline_result.get("critic"), language="")
                    
                    # Graph (only LangGraph)
                    graph_dot = pipeline_result.get("graph_dot")
                    if graph_dot and pipeline_mode == "LangGraph":
                        st.markdown("### Workflow Graph")
                        st.graphviz_chart(graph_dot, use_container_width=True)
                    
                    # Download
                    st.markdown("### Export")
                    st.download_button(
                        "Download as JSON",
                        data=json.dumps(pipeline_result, ensure_ascii=False, indent=2),
                        file_name=f"paper_analysis_{pipeline_mode.lower()}_{int(time.time())}.json",
                        mime="application/json",
                        use_container_width=True,
                    )
                elif pipeline_result is None:
                    st.error("Analysis failed. No results received.")
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
                if show_debug:
                    st.exception(e)

# === TAB 2: COMPARE ===
with tab_vergleich:
    st.markdown("### Compare All Pipelines")
    st.info("Run all three pipelines on the same document to compare results.")
    
    uploaded_files_compare = st.file_uploader(
        "Upload file for comparison",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        key="compare_upload",
    )
    
    raw_text_compare = read_uploaded_files(uploaded_files_compare) if uploaded_files_compare else ""
    analysis_context_compare = build_analysis_context(raw_text_compare, config) if raw_text_compare else ""
    
    if analysis_context_compare:
        st.success(f"{len(analysis_context_compare):,} characters loaded")
    
    if st.button("Compare Pipelines", type="primary", use_container_width=True):
        if not analysis_context_compare.strip():
            st.error("Please upload a file first!")
        else:
            with st.status("Comparing pipelines...", expanded=True) as status:
                results = {}
                errors = {}
                pipelines = [
                    ("LangChain", lambda: run_lc(analysis_context_compare, config)),
                    ("LangGraph", lambda: run_lg(analysis_context_compare, config)),
                    ("DSPy", lambda: run_dspy(analysis_context_compare, config)),
                ]
                
                for label, runner in pipelines:
                    try:
                        status.update(label=f"Running {label}...")
                        results[label] = runner()
                    except Exception as exc:
                        errors[label] = str(exc)
                        results[label] = {"meta": f"Error: {exc}"}
                
                status.update(label="Comparison complete!", state="complete")
            
            # Comparison table
            st.markdown("## Comparison Table")
            table_rows = []
            for label, res in results.items():
                table_rows.append({
                    "Pipeline": label,
                    "Total (s)": f"{res.get('latency_s', 0.0):.2f}",
                    "Reader (s)": f"{res.get('reader_s', 0.0):.2f}",
                    "Summarizer (s)": f"{res.get('summarizer_s', 0.0):.2f}",
                    "Critic (s)": f"{res.get('critic_s', 0.0):.2f}",
                    "Summary (chars)": len(res.get("summary", "") or ""),
                    "Meta (chars)": len(res.get("meta", "") or ""),
                })
            
            df = pd.DataFrame(table_rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Runtime chart
            if not df.empty:
                st.markdown("### Runtime Comparison")
                chart_df = pd.DataFrame([
                    {
                        "Pipeline": row["Pipeline"],
                        "Runtime": float(row["Total (s)"])
                    }
                    for row in table_rows
                ])
                chart = (
                    alt.Chart(chart_df)
                    .mark_bar(size=50)
                    .encode(
                        x=alt.X("Pipeline:N", title="Pipeline", sort=None),
                        y=alt.Y("Runtime:Q", title="Runtime (seconds)"),
                        color=alt.Color("Pipeline:N", legend=None),
                        tooltip=["Pipeline", "Runtime"]
                    )
                    .properties(height=300)
                )
                st.altair_chart(chart, use_container_width=True)
            
            # Key metrics
            st.markdown("### Key Metrics")
            if len(table_rows) >= 3:
                fastest = min(table_rows, key=lambda x: float(x["Total (s)"]))
                longest_summary = max(table_rows, key=lambda x: int(x["Summary (chars)"]))
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Fastest Pipeline", fastest["Pipeline"], f"{fastest['Total (s)']}s")
                with col2:
                    st.metric("Longest Summary", longest_summary["Pipeline"], f"{int(longest_summary['Summary (chars)']):,} chars")
                with col3:
                    avg_time = sum(float(r["Total (s)"]) for r in table_rows) / len(table_rows)
                    st.metric("Average Runtime", f"{avg_time:.2f}s")
            
            # Detailed results in tabs
            st.markdown("## Detailed Results")
            tabs = st.tabs(list(results.keys()))
            for tab, label in zip(tabs, results.keys()):
                res = results[label]
                with tab:
                    if label == "DSPy" and not DSPY_READY:
                        st.warning("DSPy not installed. Install `dspy-ai` and `litellm` for full functionality.")
                    if errors.get(label):
                        st.error(f"Error: {errors[label]}")
                    
                    # Graph for LangGraph
                    if label == "LangGraph":
                        graph_dot = res.get("graph_dot")
                        if graph_dot:
                            st.markdown("### Workflow Graph")
                            st.graphviz_chart(graph_dot, use_container_width=True)
                    
                    st.markdown("**Meta Summary**")
                    st.info(res.get("meta", ""))
                    
                    st.markdown("**Summary**")
                    st.markdown(res.get("summary", ""))
                    
                    with st.expander("Notes"):
                        st.text(res.get("structured", ""))
                    
                    with st.expander("Critic"):
                        st.text(res.get("critic", ""))

# === TAB 3: DSPY TELEPROMPT ===
with tab_teleprompt:
    st.markdown("### DSPy Teleprompting: Base vs. Optimized")
    st.info("Compare DSPy without and with Teleprompting optimization. Enable Teleprompting in Settings and provide a dev set path.")
    
    if not DSPY_READY:
        st.warning("DSPy not installed. Please install `dspy-ai` and `litellm`.")
    else:
        uploaded_files_tp = st.file_uploader(
            "Upload file for teleprompt test",
            type=["pdf", "txt"],
            accept_multiple_files=True,
            key="teleprompt_upload",
        )
        
        raw_text_tp = read_uploaded_files(uploaded_files_tp) if uploaded_files_tp else ""
        analysis_context_tp = build_analysis_context(raw_text_tp, config) if raw_text_tp else ""
        
        if analysis_context_tp:
            st.success(f"{len(analysis_context_tp):,} characters loaded")
        
        if st.button("Run Teleprompt Comparison", type="primary", use_container_width=True):
            if not analysis_context_tp.strip():
                st.error("Please upload a file first!")
            else:
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
                
                with st.status("Running DSPy (Base vs. Teleprompt)...", expanded=True) as status:
                    try:
                        status.update(label="Base version...")
                        res_base = run_dspy(analysis_context_tp, base_cfg)
                        status.update(label="Teleprompt version...")
                        res_tp = run_dspy(analysis_context_tp, tp_cfg)
                        status.update(label="Comparison complete!", state="complete")
                    except Exception as e:
                        status.update(label=f"Error: {e}", state="error")
                        st.error(str(e))
                        res_base = res_tp = None
                
                if res_base and res_tp:
                    # Comparison table
                    st.markdown("## Comparison")
                    rows = []
                    for label, res in (("Base", res_base), ("Teleprompt", res_tp)):
                        f1 = _f1(analysis_context_tp, res.get("summary", "") or "")
                        rows.append({
                            "Variant": label,
                            "Runtime (s)": f"{res.get('latency_s', 0.0):.2f}",
                            "Summary Length": len(res.get("summary", "") or ""),
                            "Meta Length": len(res.get("meta", "") or ""),
                            "F1 Score": f"{f1:.3f}",
                        })
                    df_gain = pd.DataFrame(rows)
                    st.dataframe(df_gain, use_container_width=True, hide_index=True)
                    
                    if len(df_gain) == 2:
                        f1_base = float(df_gain.iloc[0]["F1 Score"])
                        f1_tp = float(df_gain.iloc[1]["F1 Score"])
                        gain = f1_tp - f1_base
                        if gain > 0:
                            st.success(f"Teleprompt F1 Gain: +{gain:.3f}")
                        else:
                            st.info(f"Teleprompt F1 Gain: {gain:.3f}")
                    
                    # Detailed results
                    st.markdown("## Results")
                    tabs = st.tabs(["Base", "Teleprompt"])
                    for tab, (label, res) in zip(tabs, (("Base", res_base), ("Teleprompt", res_tp))):
                        with tab:
                            st.markdown(f"### {label}")
                            st.markdown("**Meta Summary**")
                            st.info(res.get("meta", ""))
                            st.markdown("**Summary**")
                            st.markdown(res.get("summary", ""))
                            with st.expander("Notes"):
                                st.text(res.get("structured", ""))
                            with st.expander("Critic"):
                                st.text(res.get("critic", ""))

# === TELEMETRY ===
with st.expander("Telemetry (CSV)", expanded=False):
    telemetry_path = "telemetry.csv"
    if not os.path.exists(telemetry_path):
        st.caption("No telemetry.csv found.")
    else:
        try:
            telemetry_df = pd.read_csv(telemetry_path)
            st.caption(f"Showing last {min(len(telemetry_df), 200)} entries.")
            st.dataframe(telemetry_df.tail(200), use_container_width=True)
            if {"engine", "latency_s"} <= set(telemetry_df.columns):
                subset = telemetry_df[["engine", "latency_s"]].reset_index().rename(columns={"index": "run"})
                line = (
                    alt.Chart(subset.tail(200))
                    .mark_line(point=True)
                    .encode(
                        x=alt.X("run:Q", title="Run"),
                        y=alt.Y("latency_s:Q", title="Runtime (s)"),
                        color="engine:N",
                    )
                )
                st.altair_chart(line, use_container_width=True)
        except Exception as e:
            st.error(f"Could not load telemetry: {e}")
