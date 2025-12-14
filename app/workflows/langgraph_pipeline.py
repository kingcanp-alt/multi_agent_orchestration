"""
LangGraph Pipeline: Graph-based execution with conditional loops.
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
from utils import (
    build_analysis_context,
    truncate_text,
    extract_confidence_line,
)


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
    critic_score: float
    critic_loops: int
    execution_trace: list[str]
    routing_trace: list[str]
    confidence: str
    _timeout: int
    _config: Dict[str, Any]


def _append_trace(state: PipelineState, label: str) -> None:
    trace = state.get("execution_trace")
    if not isinstance(trace, list):
        trace = []
        state["execution_trace"] = trace
    trace.append(label)


def _append_route(state: PipelineState, route: str) -> None:
    routes = state.get("routing_trace")
    if not isinstance(routes, list):
        routes = []
        state["routing_trace"] = routes
    routes.append(route)


def _execute_with_timeout(
    function: Callable,
    timeout_seconds: int,
    timeout_default_value: str = "__TIMEOUT__"
) -> Any:
    """
    Runs function with timeout protection.
    
    LLM calls can hang. ThreadPoolExecutor interrupts them after timeout_seconds.
    Without this, one slow API call blocks the whole pipeline.
    """
    with cf.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(function)
        try:
            return future.result(timeout=max(1, int(timeout_seconds)))
        except cf.TimeoutError:
            return timeout_default_value


def _execute_retriever_node(state: PipelineState) -> PipelineState:
    """Preprocesses input text and builds analysis context."""
    _append_trace(state, "retriever")
    config = state.get("_config", {}) or {}
    raw_input = state.get("input_text", "") or ""
    truncate_chars_limit = config.get("truncate_chars")
    preprocessed_text = truncate_text(raw_input, truncate_chars_limit) if truncate_chars_limit else raw_input
    analysis_context = build_analysis_context(preprocessed_text, config)
    state["analysis_context"] = analysis_context
    return state


def _execute_reader_node(state: PipelineState) -> PipelineState:
    """Executes Reader agent."""
    _append_trace(state, "reader")
    start_time = perf_counter()
    timeout_seconds = state.get("_timeout", 45)
    input_for_reader = state.get("analysis_context") or state.get("input_text") or ""
    notes_output = _execute_with_timeout(lambda: run_reader(input_for_reader), timeout_seconds)
    state["notes"] = notes_output
    state["reader_s"] = round(perf_counter() - start_time, 2)
    return state


def _execute_summarizer_node(state: PipelineState) -> PipelineState:
    """Executes Summarizer agent."""
    _append_trace(state, "summarizer")
    start_time = perf_counter()
    timeout_seconds = state.get("_timeout", 45)
    summary_output = _execute_with_timeout(lambda: run_summarizer(state["notes"]), timeout_seconds)
    state["summary"] = summary_output
    state["summarizer_s"] = round(perf_counter() - start_time, 2)
    return state


def _execute_critic_node(state: PipelineState) -> PipelineState:
    """Executes Critic agent."""
    _append_trace(state, "critic")
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


def _extract_critic_score(state: PipelineState) -> float:
    """
    Extracts score from critic text.
    
    Critic returns text like "Makes sense: 4" or "Accuracy: 4". We find the first number.
    If it is greater than 1.0, we assume a 0-5 scale. Then we convert
    to 0-1 for routing.
    """
    text = state.get("critic", "") or ""
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", text)
    if match:
        score = float(match.group(1))
    else:
        score = 0.5
    if score > 1.0:
        score = min(score / 5.0, 1.0)
    score = max(0.0, min(score, 1.0))
    state["critic_score"] = round(score, 3)
    return state["critic_score"]


def _critic_post_path(state: PipelineState) -> str:
    """
    Routes based on critic score.
    
    If score is below 0.5, route back to summarizer. The system can fix
    bad summaries automatically. We limit loops to avoid infinite cycles.
    First we tried fixed 3 retries. Configurable max_loops fits better
    for different use cases.
    """
    _extract_critic_score(state)
    loops = state.get("critic_loops", 0)
    cfg = state.get("_config", {}) or {}
    max_loops = max(0, int(cfg.get("max_critic_loops", 1)))
    
    if state["critic_score"] < 0.5 and loops < max_loops:
        state["critic_loops"] = loops + 1
        _append_route(state, "summarizer")
        return "summarizer"
    
    _append_route(state, "integrator")
    return "integrator"


def _execute_integrator_node(state: PipelineState) -> PipelineState:
    """Executes Integrator agent."""
    _append_trace(state, "integrator")
    start_time = perf_counter()
    timeout_seconds = state.get("_timeout", 45)
    meta_output = _execute_with_timeout(
        lambda: run_integrator(notes=state["notes"], summary=state["summary"], critic=state["critic"]),
        timeout_seconds
    )
    state["meta"] = meta_output
    state["integrator_s"] = round(perf_counter() - start_time, 2)
    return state


def _generate_graph_visualization_dot(state: Optional[PipelineState] = None) -> str:
    """Generates Graphviz representation of workflow."""
    if state is None:
        return r"""
digraph G {
  rankdir=LR;
  node [shape=box, style="rounded,filled", color="#9ca3af", fillcolor="#f9fafb", fontname="Inter"];

  input      [label="Input (raw text/PDF extract)"];
  retriever  [label="Retriever/Preprocess"];
  reader     [label="Reader - Notes"];
  summarizer [label="Summarizer"];
  critic_node [label="Critic - Review"];
  integrator [label="Integrator - Meta Summary"];
  output     [label="Output (notes, summary, critic, meta)"];

  input -> retriever -> reader -> summarizer -> critic_node;
  critic_node -> summarizer [label="rework (low critic)", style="dotted"];
  critic_node -> integrator [label="ok"];
  integrator -> output;
}
""".strip()

    reader_time = state.get("reader_s", 0.0)
    summarizer_time = state.get("summarizer_s", 0.0)
    critic_time = state.get("critic_s", 0.0)
    integrator_time = state.get("integrator_s", 0.0)
    critic_score = state.get("critic_score", 0.0)
    loops = state.get("critic_loops", 0)

    reader_label = f"Reader - Notes\\n{reader_time:.2f}s"
    summarizer_label = f"Summarizer - Summary\\n{summarizer_time:.2f}s"
    critic_label = f"Critic - Review\\nScore: {critic_score:.2f}\\n{critic_time:.2f}s"
    integrator_label = f"Integrator - Meta Summary\\n{integrator_time:.2f}s"

    return f"""
digraph G {{
  rankdir=LR;
  node [shape=box, style="rounded,filled", color="#667eea", fillcolor="#f0f4ff", fontname="Inter"];
  edge [color="#9ca3af"];

  input      [label="Input\\n(raw text/PDF)", fillcolor="#e0e7ff", color="#667eea"];
  retriever  [label="Retriever/Preprocess\\nAnalysis Context", fillcolor="#f0f4ff"];
  reader     [label="{reader_label}", fillcolor="#dbeafe"];
  summarizer [label="{summarizer_label}", fillcolor="#dbeafe"];
  critic_node [label="{critic_label}", fillcolor="#dbeafe"];
  integrator [label="{integrator_label}", fillcolor="#dbeafe"];
  output     [label="Output\\n(all results)", fillcolor="#e0e7ff", color="#667eea"];

  input -> retriever -> reader -> summarizer -> critic_node;
  critic_node -> summarizer [label="rework (score < 0.5, loops: {loops})", style="dotted"];
  critic_node -> integrator [label="ok (score >= 0.5)"];
  integrator -> output;
}}
""".strip()


def _build_langgraph_workflow() -> Any:
    """
    Builds LangGraph workflow.
    
    Flow: retriever -> reader -> summarizer -> critic -> (conditional) -> integrator
    The conditional edge allows return to summarizer on low quality. This is
    the main difference from LangChain: explicit state and conditional routing.
    We considered parallel branches like translator or keyword nodes. We kept
    it simple to match base requirements.
    """
    graph = StateGraph(PipelineState)
    graph.add_node("retriever", _execute_retriever_node)
    graph.add_node("reader", _execute_reader_node)
    graph.add_node("summarizer", _execute_summarizer_node)
    graph.add_node("critic_node", _execute_critic_node)
    graph.add_node("integrator", _execute_integrator_node)
    
    graph.set_entry_point("retriever")
    graph.add_edge("retriever", "reader")
    graph.add_edge("reader", "summarizer")
    graph.add_edge("summarizer", "critic_node")
    graph.add_conditional_edges("critic_node", _critic_post_path)
    graph.add_edge("integrator", END)
    return graph.compile()


def run_pipeline(input_text: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Executes LangGraph pipeline."""
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
        "critic_score": 0.0,
        "critic_loops": 0,
        "execution_trace": [],
        "routing_trace": [],
        "confidence": "",
        "_timeout": timeout_seconds,
        "_config": config_dict,
    }
    
    final_state = workflow.invoke(initial_state)
    total_duration = round(perf_counter() - start_total, 2)
    input_chars = len(final_state.get("analysis_context") or input_text or "")
    confidence_line = extract_confidence_line(final_state.get("meta", "") or "") or ""
    final_state["confidence"] = confidence_line or final_state.get("confidence", "")
    
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
        "critic_score": final_state.get("critic_score", 0.0),
        "critic_loops": final_state.get("critic_loops", 0),
        "confidence": final_state.get("confidence", ""),
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
        "critic_score": final_state.get("critic_score", 0.0),
        "critic_loops": final_state.get("critic_loops", 0),
        "latency_s": total_duration,
        "input_chars": input_chars,
        "graph_dot": _generate_graph_visualization_dot(final_state),
        "execution_trace": final_state.get("execution_trace", []) or [],
        "routing_trace": final_state.get("routing_trace", []) or [],
        "confidence": final_state.get("confidence", "") or confidence_line or "",
    }
