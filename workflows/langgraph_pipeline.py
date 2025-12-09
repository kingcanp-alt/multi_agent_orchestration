"""
LangGraph Pipeline: Graph-basierte Ausführung mit expliziter Graph-Struktur.
"""

from __future__ import annotations

from typing import TypedDict, Dict, Any, Optional, Callable
from time import perf_counter
import concurrent.futures as cf
import re

from langgraph.graph import StateGraph, END

from agents.reader import run as run_reader
from agents.summarizer import run as run_summarizer
from agents.critic import run as run_critic
from agents.integrator import run as run_integrator
from llm import configure
from telemetry import log_row
from utils import build_analysis_context, truncate_text
from langchain_core.prompts import ChatPromptTemplate


class PipelineState(TypedDict):
    """State des LangGraph-Workflows."""
    input_text: str
    analysis_context: str
    notes: str
    summary: str
    critic: str
    meta: str
    reader_s: float
    summarizer_s: float
    critic_s: float
    integrator_s: float
    quality_f1: float
    judge_score: float
    _timeout: int
    _config: Dict[str, Any]


def _execute_with_timeout(
    function: Callable,
    timeout_seconds: int,
    timeout_default_value: str = "__TIMEOUT__"
) -> Any:
    """Führt Funktion mit Timeout aus, schützt gegen hängende LLM-Requests."""
    with cf.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(function)
        try:
            return future.result(timeout=max(1, int(timeout_seconds)))
        except cf.TimeoutError:
            return timeout_default_value


def _execute_retriever_node(state: PipelineState) -> PipelineState:
    """Graph-Knoten: Preprocessing/Abschnittsauswahl (Retrieval/Guard)."""
    config = state.get("_config", {}) or {}
    raw_input = state.get("input_text", "") or ""
    truncate_chars_limit = config.get("truncate_chars")
    preprocessed_text = truncate_text(raw_input, truncate_chars_limit) if truncate_chars_limit else raw_input
    analysis_context = build_analysis_context(preprocessed_text, config)
    state["analysis_context"] = analysis_context
    return state


def _execute_reader_node(state: PipelineState) -> PipelineState:
    """Graph-Knoten: Reader-Agent ausführen."""
    start_time = perf_counter()
    timeout_seconds = state.get("_timeout", 45)
    input_for_reader = state.get("analysis_context") or state.get("input_text") or ""
    notes_output = _execute_with_timeout(lambda: run_reader(input_for_reader), timeout_seconds)
    state["notes"] = notes_output
    state["reader_s"] = round(perf_counter() - start_time, 2)
    return state


def _execute_summarizer_node(state: PipelineState) -> PipelineState:
    """Graph-Knoten: Summarizer-Agent ausführen."""
    start_time = perf_counter()
    timeout_seconds = state.get("_timeout", 45)
    summary_output = _execute_with_timeout(lambda: run_summarizer(state["notes"]), timeout_seconds)
    state["summary"] = summary_output
    state["summarizer_s"] = round(perf_counter() - start_time, 2)
    return state


def _execute_critic_node(state: PipelineState) -> PipelineState:
    """Graph-Knoten: Critic-Agent ausführen."""
    start_time = perf_counter()
    timeout_seconds = state.get("_timeout", 45)
    critic_result = _execute_with_timeout(
        lambda: run_critic(notes=state["notes"], summary=state["summary"]),
        timeout_seconds
    )
    
    if isinstance(critic_result, dict):
        critic_text = critic_result.get("critic") or critic_result.get("critique") or ""
    else:
        critic_text = str(critic_result)
    
    state["critic"] = critic_text
    state["critic_s"] = round(perf_counter() - start_time, 2)
    return state


def _tokens(s: str) -> set[str]:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return {t for t in s.split() if len(t) > 2}


def _execute_quality_node(state: PipelineState) -> PipelineState:
    """Graph-Knoten: Einfaches Qualitäts-Maß (Unigram-F1) zwischen NOTES und SUMMARY."""
    gold = _tokens(state.get("notes", "") or "")
    pred = _tokens(state.get("summary", "") or "")
    if not gold or not pred:
        state["quality_f1"] = 0.0
        return state
    inter = len(gold & pred)
    prec = inter / len(pred)
    rec = inter / len(gold)
    f1 = 0.0 if (prec + rec) == 0 else (2 * prec * rec) / (prec + rec)
    state["quality_f1"] = round(f1, 3)
    return state


def _execute_judge_node(state: PipelineState) -> PipelineState:
    """Graph-Knoten: LLM-as-a-judge (ein Gesamt-Score 0-5, nur Zahl)."""
    prompt = ChatPromptTemplate.from_template(
        "Score the SUMMARY against NOTES for coherence, groundedness, and coverage. "
        "Return a single integer 0-5 (0=worst, 5=best). No extra text.\n\n"
        "NOTES:\n{notes}\n\nSUMMARY:\n{summary}"
    )
    chain = prompt | llm
    try:
        llm_resp = chain.invoke({
            "notes": state.get("notes", "") or "",
            "summary": state.get("summary", "") or ""
        })
        raw = getattr(llm_resp, "content", llm_resp) or ""
        m = re.search(r"(-?\d+)", str(raw))
        score = float(m.group(1)) if m else 0.0
    except Exception:
        score = 0.0
    score = max(0.0, min(5.0, score))
    state["judge_score"] = round(score, 2)
    return state


def _execute_integrator_node(state: PipelineState) -> PipelineState:
    """Graph-Knoten: Integrator-Agent ausführen."""
    start_time = perf_counter()
    timeout_seconds = state.get("_timeout", 45)
    meta_output = _execute_with_timeout(
        lambda: run_integrator(notes=state["notes"], summary=state["summary"], critic=state["critic"]),
        timeout_seconds
    )
    state["meta"] = meta_output
    state["integrator_s"] = round(perf_counter() - start_time, 2)
    return state


def _generate_graph_visualization_dot() -> str:
    """Generiert Graphviz DOT-Darstellung des Workflows."""
    return r"""
digraph G {
  rankdir=LR;
  node [shape=box, style="rounded,filled", color="#9ca3af", fillcolor="#f9fafb", fontname="Inter"];

  input      [label="Input (raw text/PDF extract)"];
  retriever  [label="Retriever/Preprocess - Analysis Context"];
  reader     [label="Reader - Notes"];
  summarizer [label="Summarizer - Summary"];
  critic     [label="Critic - Review"];
  quality    [label="Quality (F1)"];
  judge      [label="LLM Judge (0-5)"];
  integrator [label="Integrator - Meta Summary"];
  output     [label="Output (notes, summary, critic, meta, f1, judge)"];

  input -> retriever -> reader -> summarizer -> critic -> quality -> judge -> integrator -> output;
}
""".strip()


def _build_langgraph_workflow() -> Any:
    """Baut LangGraph-Workflow mit Retrieval/Preprocessing, vier Agenten und Qualitäts-Metrik."""
    graph = StateGraph(PipelineState)
    graph.add_node("retriever", _execute_retriever_node)
    graph.add_node("reader", _execute_reader_node)
    graph.add_node("summarizer", _execute_summarizer_node)
    graph.add_node("critic", _execute_critic_node)
    graph.add_node("quality", _execute_quality_node)
    graph.add_node("judge", _execute_judge_node)
    graph.add_node("integrator", _execute_integrator_node)
    graph.set_entry_point("retriever")
    graph.add_edge("retriever", "reader")
    graph.add_edge("reader", "summarizer")
    graph.add_edge("summarizer", "critic")
    graph.add_edge("critic", "quality")
    graph.add_edge("quality", "judge")
    graph.add_edge("judge", "integrator")
    graph.add_edge("integrator", END)
    return graph.compile()


def run_pipeline(input_text: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Führt LangGraph-Pipeline aus. Gibt Dictionary mit structured, summary, critic, meta, Timings und graph_dot zurück."""
    config_dict = config or {}
    configure(config_dict)
    timeout_seconds = int(config_dict.get("timeout", 45))
    start_total = perf_counter()
    
    workflow = _build_langgraph_workflow()
    initial_state = {
        "input_text": input_text or "",
        "analysis_context": "",
        "notes": "",
        "summary": "",
        "critic": "",
        "meta": "",
        "reader_s": 0.0,
        "summarizer_s": 0.0,
        "critic_s": 0.0,
        "integrator_s": 0.0,
        "quality_f1": 0.0,
        "judge_score": 0.0,
        "_timeout": timeout_seconds,
        "_config": config_dict,
    }
    
    final_state = workflow.invoke(initial_state)
    total_duration = round(perf_counter() - start_total, 2)
    input_chars = len(final_state.get("analysis_context") or input_text or "")
    
    log_row({
        "engine": "langgraph",
        "input_chars": input_chars,
        "summary_len": len(str(final_state.get("summary", ""))),
        "meta_len": len(str(final_state.get("meta", ""))),
        "latency_s": total_duration,
        "reader_s": final_state.get("reader_s", 0.0),
        "summarizer_s": final_state.get("summarizer_s", 0.0),
        "critic_s": final_state.get("critic_s", 0.0),
        "integrator_s": final_state.get("integrator_s", 0.0),
        "quality_f1": final_state.get("quality_f1", 0.0),
        "judge_score": final_state.get("judge_score", 0.0),
    })
    
    return {
        "structured": final_state.get("notes", ""),
        "summary": final_state.get("summary", ""),
        "critic": final_state.get("critic", ""),
        "meta": final_state.get("meta", ""),
        "reader_s": final_state.get("reader_s", 0.0),
        "summarizer_s": final_state.get("summarizer_s", 0.0),
        "critic_s": final_state.get("critic_s", 0.0),
        "integrator_s": final_state.get("integrator_s", 0.0),
        "quality_f1": final_state.get("quality_f1", 0.0),
        "judge_score": final_state.get("judge_score", 0.0),
        "latency_s": total_duration,
        "input_chars": input_chars,
        "graph_dot": _generate_graph_visualization_dot(),
    }
