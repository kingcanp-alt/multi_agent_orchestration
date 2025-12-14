"""
Streamlit App for Paper Analyzer.

LangChain, LangGraph, and DSPy pipelines.
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
try:
    from workflows.langgraph_pipeline import run_pipeline as run_lg
    LANGGRAPH_READY = True
except Exception as e:
    LANGGRAPH_READY = False
    def run_lg(*args, **kwargs):
        raise ImportError(f"LangGraph import failed: {e}")
from workflows.dspy_pipeline import run_pipeline as run_dspy, DSPY_READY
from utils import build_analysis_context, extract_confidence_line

load_dotenv()
st.set_page_config(
    page_title="Paper Summarizer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
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
    .main-content {
        padding-top: 1rem;
    }
    .section-spacing {
        margin-top: 2rem;
        margin-bottom: 1.5rem;
    }
    .help-box {
        background-color: #f0f2f6;
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        margin-top: 0.5rem;
        border-left: 4px solid #1f77b4;
        line-height: 1.5;
        font-size: 0.9rem;
    }
    .stExpander {
        margin-bottom: 0.75rem;
    }
    .element-container {
        margin-bottom: 0.75rem;
    }
    div[data-testid="stFileUploader"] {
        margin-bottom: 0.75rem;
    }
    .compact-section {
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("Paper Analyzer")
st.caption("Multi-Agent Orchestration with LangChain, LangGraph & DSPy")

# Help
st.markdown("""
<div class="help-box">
    <strong>Quick Start:</strong> Upload document → Select pipeline → Analyze
</div>
""", unsafe_allow_html=True)

# Settings
with st.sidebar:
    st.markdown("### Settings")
    st.markdown("---")
    
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
        ["gpt-4o-mini", "gpt-4o", "gpt-4.1"],
        index=0,
        help="gpt-4o-mini: Faster and cheaper, good for most tasks\n\ngpt-4o: More capable but slower and more expensive",
    )
    
    with st.expander("Advanced"):
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
    
    # DSPy settings
    if DSPY_READY:
        with st.expander("DSPy"):
            use_dspy_teleprompt = st.checkbox(
                "Enable Teleprompting",
                value=False,
                help="DSPy Teleprompting automatically optimizes prompts using examples from a dev set. Uses BootstrapFewShot to find better prompt examples. Requires JSONL file with input-output pairs.",
            )
            
            if use_dspy_teleprompt:
                dspy_dev_path = st.text_input(
                    "Dev-Set Path",
                    value="dev-set/dev.jsonl",
                    help="Path to JSONL file containing training examples. Each line must be a JSON object with input text and expected summary. The system uses this file for prompt optimization.",
                )
                if not os.path.exists(dspy_dev_path):
                    st.warning(f"File not found: {dspy_dev_path}")
            else:
                dspy_dev_path = "dev-set/dev.jsonl"
            
            show_debug = st.checkbox("Debug Mode", value=False, help="Show detailed error messages and stack traces when errors occur. Useful for troubleshooting.")
    else:
        # DSPy not available
        use_dspy_teleprompt = False
        dspy_dev_path = "dev-set/dev.jsonl"
        show_debug = False

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
    "csv_telemetry": True,
    "max_critic_loops": 2, # Default for LangGraph
}

# Main tabs
tab_analyse, tab_vergleich, tab_teleprompt = st.tabs(["Analysis", "Compare", "DSPy Optimization"])

# Tab 1: Analysis
with tab_analyse:
    col_upload, col_pipeline = st.columns([2, 1])
    
    with col_upload:
        st.markdown("### Upload Document")
        uploaded_files = st.file_uploader(
            "Select PDF or TXT file",
            type=["pdf", "txt"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        
        if uploaded_files:
            st.success(f"{len(uploaded_files)} file(s) uploaded")
            for file in uploaded_files:
                file_size_mb = file.size / (1024 * 1024)
                st.caption(f"{file.name} ({file_size_mb:.2f} MB)")
    
    with col_pipeline:
        st.markdown("### Select Pipeline")
        pipeline_mode = st.radio(
            "Pipeline",
            ["LangChain", "LangGraph", "DSPy"],
            label_visibility="collapsed",
            help="LangChain: Sequential pipeline, simple and fast. Linear flow: Reader → Summarizer → Critic → Integrator.\n\nLangGraph: Graph-based orchestration with explicit control flow. Includes quality metrics and visualization.\n\nDSPy: Declarative pipeline using signatures. Can optimize prompts automatically with teleprompting.",
        )
        
        if pipeline_mode == "DSPy" and not DSPY_READY:
            st.warning("DSPy not installed. Install `dspy-ai` and `litellm` for full functionality.")
        if pipeline_mode == "LangGraph" and not LANGGRAPH_READY:
            st.warning("LangGraph import failed. Check if langgraph is installed.")
    
    st.markdown("---")
    
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
    
    # Analyze button
    if st.button("Analyze", type="primary", use_container_width=True, disabled=not uploaded_files):
        if not analysis_context.strip():
            st.error("Please upload a file first!")
        else:
            pipeline_result = None
            try:
                with st.status("Analyzing document", expanded=True) as status:
                    if pipeline_mode == "LangChain":
                        status.update(label="Running LangChain", state="running")
                        pipeline_result = run_lc(analysis_context, config)
                    elif pipeline_mode == "LangGraph":
                        status.update(label="Running LangGraph", state="running")
                        pipeline_result = run_lg(analysis_context, config)
                    else:
                        status.update(label="Running DSPy", state="running")
                        if use_dspy_teleprompt:
                            status.update(label="Optimizing with Teleprompting...", state="running")
                        pipeline_result = run_dspy(analysis_context, config)
                    
                    status.update(label="Analysis complete!", state="complete")
                
                # Results
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
                        loops = int(pipeline_result.get("critic_loops", 0) or 0)
                        st.metric("Critic Loops", str(loops), help="How many times LangGraph routed back to Summarizer due low critic score (LangGraph only).")

                    execution_trace = pipeline_result.get("execution_trace", []) or []
                    trace_set = {str(x).lower() for x in execution_trace if x}
                    agent_lines = []
                    for key, label in (
                        ("reader", "Reader"),
                        ("summarizer", "Summarizer"),
                        ("critic", "Critic"),
                        ("integrator", "Integrator"),
                    ):
                        status_text = "visited" if key in trace_set else "not visited"
                        agent_lines.append(f"{label} - {status_text}")

                    with st.expander("Execution Trace", expanded=True):
                        st.markdown("\n".join(f"- {line}" for line in agent_lines))
                        if pipeline_mode == "LangGraph":
                            looped = "YES" if int(pipeline_result.get("critic_loops", 0) or 0) > 0 else "NO"
                            routing = pipeline_result.get("routing_trace", []) or []
                            branch = (routing[-1] if routing else "n/a").upper()
                            st.markdown(f"LangGraph looped: **{looped}**")
                            st.markdown(f"LangGraph branch: **{branch}**")
                    
                    # Meta Summary
                    if pipeline_result.get("meta"):
                        st.markdown("### Meta Summary")
                        st.info(pipeline_result.get("meta"))
                        confidence_line = pipeline_result.get("confidence") or extract_confidence_line(pipeline_result.get("meta", ""))
                        if confidence_line:
                            st.caption(confidence_line)
                        else:
                            st.caption("Confidence: not provided")

                    # Summary
                    if pipeline_result.get("summary"):
                        st.markdown("### Summary")
                        st.markdown(pipeline_result.get("summary"))
                    
                    # Timing
                    st.markdown("### Timing")
                    times = {
                        "Reader": pipeline_result.get('reader_s', 0),
                        "Results Extractor": pipeline_result.get('results_extractor_s', 0),
                        "Summarizer": pipeline_result.get('summarizer_s', 0),
                        "Critic": pipeline_result.get('critic_s', 0),
                        "Integrator": pipeline_result.get('integrator_s', 0),
                    }
                    cols = st.columns(len(times))
                    for col, (key, value) in zip(cols, times.items()):
                        with col:
                            st.metric(key, f"{value:.2f}s")
                    
                    # Notes & Critic
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

# Tab 2: Compare
with tab_vergleich:
    st.markdown("### Compare All Pipelines")
    st.info("Run all pipelines on same document to compare results.")
    
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
            with st.status("Comparing pipelines", expanded=True) as status:
                results = {}
                errors = {}
                pipelines = [
                    ("LangChain", lambda: run_lc(analysis_context_compare, config)),
                    ("LangGraph", lambda: run_lg(analysis_context_compare, config)),
                    ("DSPy", lambda: run_dspy(analysis_context_compare, config)),
                ]
                
                for label, runner in pipelines:
                    try:
                        status.update(label=f"Running {label}")
                        results[label] = runner()
                    except Exception as exc:
                        import traceback
                        error_msg = str(exc)
                        error_trace = traceback.format_exc()
                        errors[label] = error_msg
                        results[label] = {
                            "meta": f"Error: {error_msg}",
                            "summary": "",
                            "structured": "",
                            "critic": "",
                            "latency_s": 0.0,
                            "reader_s": 0.0,
                            "summarizer_s": 0.0,
                            "critic_s": 0.0,
                            "integrator_s": 0.0,
                        }
                        if show_debug:
                            st.error(f"{label} error: {error_trace}")
                
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
            
            # Runtime Comparison
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
            
            # Key Metrics
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
            
            # Detailed results
            st.markdown("## Detailed Results")
            tabs = st.tabs(list(results.keys()))
            for tab, label in zip(tabs, results.keys()):
                res = results[label]
                with tab:
                    if label == "DSPy" and not DSPY_READY:
                        st.warning("DSPy not installed. Install `dspy-ai` and `litellm` for full functionality.")
                    if errors.get(label):
                        st.error(f"**Error in {label}:** {errors[label]}")
                        if show_debug:
                            import traceback
                            st.code(traceback.format_exc(), language="python")

                    execution_trace = res.get("execution_trace", []) or []
                    if execution_trace:
                        with st.expander("Execution Trace", expanded=False):
                            st.markdown("\n".join(f"- {t}" for t in execution_trace))
                    
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

# Tab 3: DSPy Teleprompt
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

# CSV Telemetry
st.markdown("---")
with st.expander("CSV Telemetry Data", expanded=False):
    telemetry_path = "telemetry.csv"
    if not os.path.exists(telemetry_path):
        st.info("No telemetry data yet. Run a pipeline to start logging metrics.")
    else:
        try:
            telemetry_df = pd.read_csv(telemetry_path)
            if len(telemetry_df) > 0:
                st.markdown(f"**Total runs:** {len(telemetry_df)}")
                
                # Last 10 entries
                last_entries = telemetry_df.tail(10).copy()
                
                # Columns for display
                display_cols = []
                if "timestamp" in last_entries.columns:
                    display_cols.append("timestamp")
                if "engine" in last_entries.columns:
                    display_cols.append("engine")
                if "model" in last_entries.columns:
                    display_cols.append("model")
                if "latency_s" in last_entries.columns:
                    display_cols.append("latency_s")
                if "summary_len" in last_entries.columns:
                    display_cols.append("summary_len")
                if "extracted_metrics_count" in last_entries.columns:
                    display_cols.append("extracted_metrics_count")
                if "critic_loops" in last_entries.columns:
                    display_cols.append("critic_loops")
                if "critic_score" in last_entries.columns:
                    display_cols.append("critic_score")
                
                if display_cols:
                    # Format data for better display
                    display_df = last_entries[display_cols].copy()
                    if "timestamp" in display_df.columns:
                        # Format timestamp only date and time
                        try:
                            display_df["timestamp"] = pd.to_datetime(display_df["timestamp"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
                        except Exception:
                            pass
                    if "latency_s" in display_df.columns:
                        display_df["latency_s"] = pd.to_numeric(display_df["latency_s"], errors="coerce").round(2)
                    if "summary_len" in display_df.columns:
                        display_df["summary_len"] = pd.to_numeric(display_df["summary_len"], errors="coerce").fillna(0).astype(int)
                    if "extracted_metrics_count" in display_df.columns:
                        display_df["extracted_metrics_count"] = pd.to_numeric(display_df["extracted_metrics_count"], errors="coerce").fillna(0).astype(int)
                    if "critic_score" in display_df.columns:
                        display_df["critic_score"] = pd.to_numeric(display_df["critic_score"], errors="coerce").round(2)
                    if "critic_loops" in display_df.columns:
                        display_df["critic_loops"] = pd.to_numeric(display_df["critic_loops"], errors="coerce").fillna(0).astype(int)
                    
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Latency over time
                    if "latency_s" in telemetry_df.columns and "engine" in telemetry_df.columns:
                        st.markdown("**Latency over time:**")
                        plot_data = telemetry_df.tail(30).copy()
                        plot_data = plot_data.reset_index()
                        plot_data["run"] = plot_data.index + 1
                        
                        chart = (
                            alt.Chart(plot_data)
                            .mark_line(point=True, size=2)
                            .encode(
                                x=alt.X("run:Q", title="Run #"),
                                y=alt.Y("latency_s:Q", title="Latency (seconds)"),
                                color=alt.Color("engine:N", legend=alt.Legend(title="Pipeline")),
                            )
                            .properties(height=250)
                        )
                        st.altair_chart(chart, use_container_width=True)
                
                # Download CSV
                csv_data = telemetry_df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    data=csv_data,
                    file_name="telemetry.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("No data yet. Run a pipeline to start logging metrics.")
        except Exception as e:
            st.error(f"Could not load telemetry: {e}")
