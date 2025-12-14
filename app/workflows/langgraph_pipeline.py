"""
LangGraph Pipeline: Graph-basierte Ausführung mit expliziter Graph-Struktur.
"""

from __future__ import annotations

from typing import TypedDict, Dict, Any, Optional, Callable, List
from time import perf_counter
import concurrent.futures as cf
import re
from collections import Counter

from langgraph.graph import StateGraph, END

from agents.reader import run as run_reader
from agents.summarizer import run as run_summarizer
from agents.critic import run as run_critic
from agents.integrator import run as run_integrator
from llm import configure, llm
from telemetry import log_row
from utils import (
    build_analysis_context,
    truncate_text,
    detect_quantitative_signal,
    count_numeric_results,
    extract_confidence_line,
)
from langchain_core.prompts import ChatPromptTemplate


class PipelineState(TypedDict):
    """State des LangGraph-Workflows."""
    input_text: str
    analysis_context: str
    quant_signal: str
    quant_signal_label: str
    quant_keyword_hits: list[str]
    quant_number_samples: list[str]
    notes: str
    extracted_metrics_count: int
    recovery_attempted: bool
    recovered_results: str
    summary: str
    critic: str
    meta: str
    reader_s: float
    summarizer_s: float
    critic_s: float
    integrator_s: float
    translator_s: float
    keyword_s: float
    summary_translated: str
    keywords: str
    judge_aggregate: float
    critic_score: float
    critic_loops: int
    quality_f1: float
    quality_rougeL: float
    judge_score: float
    results_extractor_s: float
    execution_trace: list[str]
    routing_trace: list[str]
    translator_note: str
    keyword_note: str
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
    """Führt Funktion mit Timeout aus, schützt gegen hängende LLM-Requests."""
    with cf.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(function)
        try:
            return future.result(timeout=max(1, int(timeout_seconds)))
        except cf.TimeoutError:
            return timeout_default_value


def _execute_retriever_node(state: PipelineState) -> PipelineState:
    """Graph-Knoten: Preprocessing/Abschnittsauswahl (Retrieval/Guard)."""
    _append_trace(state, "retriever")
    config = state.get("_config", {}) or {}
    raw_input = state.get("input_text", "") or ""
    truncate_chars_limit = config.get("truncate_chars")
    preprocessed_text = truncate_text(raw_input, truncate_chars_limit) if truncate_chars_limit else raw_input
    analysis_context = build_analysis_context(preprocessed_text, config)
    state["analysis_context"] = analysis_context
    quant_info = detect_quantitative_signal(analysis_context)
    state["quant_signal"] = str(quant_info.get("signal") or "NO")
    state["quant_signal_label"] = str(quant_info.get("label") or "NO (no quantitative signal detected)")
    state["quant_keyword_hits"] = list(quant_info.get("keyword_hits") or [])
    state["quant_number_samples"] = list(quant_info.get("number_samples") or [])
    return state


def _execute_reader_node(state: PipelineState) -> PipelineState:
    """Graph-Knoten: Reader-Agent ausführen."""
    _append_trace(state, "reader")
    start_time = perf_counter()
    timeout_seconds = state.get("_timeout", 45)
    input_for_reader = state.get("analysis_context") or state.get("input_text") or ""
    notes_output = _execute_with_timeout(lambda: run_reader(input_for_reader), timeout_seconds)
    state["notes"] = notes_output
    state["extracted_metrics_count"] = count_numeric_results(notes_output)
    state["reader_s"] = round(perf_counter() - start_time, 2)
    return state


def _extract_results_section(notes_text: str) -> str:
    """Extrahiert den Results-Block aus Notes (beste Schätzung, fallback = kompletter Text)."""
    if not notes_text:
        return ""
    match = re.search(r"Results:\s*(.*?)(?:\n[A-Z][A-Za-z/ ]+:|\Z)", notes_text, flags=re.S)
    if match:
        return match.group(1).strip()
    return notes_text


RESULTS_EXTRACT_PROMPT = ChatPromptTemplate.from_template(
    "You are a metric-only extractor. From the provided TEXT/NOTES, extract 2-6 quantitative result bullets.\n"
    "Only use numbers that actually appear in the TEXT. Do NOT invent or average anything.\n"
    "Output format ONLY:\n"
    "- <Dataset/Task>: <Metric>=<Value> (context...)\n"
    "- <Dataset/Task>: <Metric>=<Value> (context...)\n"
    "If you cannot find any numeric metrics, output exactly: No quantitative metrics found.\n\n"
    "TEXT:\n{text}"
)


def _merge_recovered_results(notes_text: str, recovered: str) -> str:
    """Fügt extrahierte Metriken in den Results-Block der Notes ein (ohne andere Bereiche zu verändern)."""
    if not recovered or "No quantitative metrics found." in recovered:
        return notes_text
    if not notes_text:
        return f"Results:\n{recovered}"
    match = re.search(r"(Results:\s*)(.*?)(\n[A-Z][A-Za-z/ ]+:|\Z)", notes_text, flags=re.S)
    if match:
        prefix, existing, suffix = match.group(1), match.group(2), match.group(3)
        existing_clean = existing.strip()
        if not existing_clean or "No quantitative metrics reported in provided text." in existing_clean:
            new_block = f"{prefix}{recovered}\n"
        else:
            new_block = f"{prefix}{existing_clean}\n{recovered}\n"
        before = notes_text[:match.start()]
        after = notes_text[match.end():]
        return f"{before}{new_block}{suffix}{after}"
    else:
        return notes_text + f"\nResults:\n{recovered}\n"


def _execute_results_extractor_node(state: PipelineState) -> PipelineState:
    """Graph-Knoten: gezielte Extraktion quantitativer Metriken (Recovery-Pfad)."""
    _append_trace(state, "results_extractor")
    start_time = perf_counter()
    timeout_seconds = state.get("_timeout", 30)
    text_source = (
        _extract_results_section(state.get("notes", "") or "")
        or state.get("analysis_context")
        or state.get("input_text")
        or ""
    )
    chain = RESULTS_EXTRACT_PROMPT | llm
    recovered = _execute_with_timeout(lambda: chain.invoke({"text": text_source}), timeout_seconds)
    recovered_text = getattr(recovered, "content", recovered) or ""
    recovered_text = str(recovered_text).strip()
    if recovered_text == "__TIMEOUT__":
        recovered_text = ""
    state["recovered_results"] = recovered_text
    state["recovery_attempted"] = True
    if recovered_text:
        merged = _merge_recovered_results(state.get("notes", ""), recovered_text)
        state["notes"] = merged
        state["extracted_metrics_count"] = count_numeric_results(merged)
    state["results_extractor_s"] = round(perf_counter() - start_time, 2)
    return state


def _reader_post_path(state: PipelineState) -> str:
    """Entscheidet nach dem Reader, ob ein Recovery-Extraktor nötig ist."""
    metrics_count = int(state.get("extracted_metrics_count", 0) or 0)
    quant_signal = str(state.get("quant_signal") or "NO").upper()
    recovery_used = bool(state.get("recovery_attempted"))
    if quant_signal in {"YES", "MAYBE"} and metrics_count < 1 and not recovery_used:
        _append_route(state, "results_extractor")
        return "results_extractor"
    _append_route(state, "summarizer")
    return "summarizer"


def _execute_summarizer_node(state: PipelineState) -> PipelineState:
    """Graph-Knoten: Summarizer-Agent ausführen."""
    _append_trace(state, "summarizer")
    start_time = perf_counter()
    timeout_seconds = state.get("_timeout", 45)
    summary_output = _execute_with_timeout(lambda: run_summarizer(state["notes"]), timeout_seconds)
    state["summary"] = summary_output
    state["summarizer_s"] = round(perf_counter() - start_time, 2)
    return state


def _execute_critic_node(state: PipelineState) -> PipelineState:
    """Graph-Knoten: Critic-Agent ausführen."""
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
    """Schätzung eines numerischen Kritiker-Scores aus dem Critic-Text."""
    text = state.get("critic", "") or ""
    match = re.search(r"([0-9]+(?:\\.[0-9]+)?)", text)
    if match:
        score = float(match.group(1))
    else:
        score = state.get("quality_f1", 0.0)
    if score > 1.0:
        score = min(score / 5.0, 1.0)
    score = max(0.0, min(score, 1.0))
    state["critic_score"] = round(score, 3)
    return state["critic_score"]


def _execute_translator_node(state: PipelineState) -> PipelineState:
    """Graph-Knoten: Dummy-Übersetzer (Deutsch/Englisch) plus Kürzung."""
    _append_trace(state, "translator")
    start_time = perf_counter()
    summary = state.get("summary", "") or ""
    if not summary.strip():
        state["summary_translated"] = "Translator skipped (reason: summary empty)"
        state["translator_note"] = "summary empty"
        state["translator_s"] = round(perf_counter() - start_time, 2)
        return state
    cfg = state.get("_config", {}) or {}
    language = cfg.get("translator_language", "DE").upper()
    style = cfg.get("translator_style", "short")
    max_chars = len(summary)
    if style == "short":
        max_chars = min(120, len(summary))
    elif style == "ultra_short":
        max_chars = min(80, len(summary))
    truncated = summary if not max_chars else summary[:max_chars]
    truncated = truncated.strip()
    translation = f"[{language}] {truncated}"
    if len(truncated) < len(summary):
        translation = f"{translation}…"
    state["summary_translated"] = translation
    state["translator_note"] = ""
    state["translator_s"] = round(perf_counter() - start_time, 2)
    return state


def _execute_keyword_node(state: PipelineState) -> PipelineState:
    """Graph-Knoten: Extrahiert Keywords aus der Summary."""
    _append_trace(state, "keyword")
    start_time = perf_counter()
    summary = state.get("summary", "") or ""
    stopwords = {"the", "and", "with", "from", "that", "this", "have", "will", "been"}
    tokens = [token.lower() for token in re.findall(r"\w+", summary) if len(token) > 3 and token.lower() not in stopwords]
    fallback_used = False
    if not tokens:
        fallback_used = True
        source = state.get("notes") or state.get("analysis_context") or summary
        tokens = [tok.lower() for tok in re.findall(r"\w+", source) if len(tok) > 3 and tok.lower() not in stopwords]
    freq = Counter(tokens)
    most_common = [token for token, _ in freq.most_common(6) if token]
    if not most_common:
        state["keywords"] = "Keywords: none (fallback used)"
        state["keyword_note"] = "fallback"
    else:
        state["keywords"] = ", ".join(most_common)
        state["keyword_note"] = "fallback" if fallback_used else ""
    state["keyword_s"] = round(perf_counter() - start_time, 2)
    return state


def _critic_post_path(state: PipelineState) -> str:
    """Entscheidet nach dem Critic-Node über den nächsten Schritt."""
    _extract_critic_score(state)
    summary = state.get("summary", "") or ""
    loops = state.get("critic_loops", 0)
    cfg = state.get("_config", {}) or {}
    max_loops = max(0, int(cfg.get("max_critic_loops", 1)))
    if state["critic_score"] < 0.5 and loops < max_loops:
        state["critic_loops"] = loops + 1
        _append_route(state, "summarizer")
        return "summarizer"
    if len(summary) < 100:
        _append_route(state, "judge")
        return "judge"
    _append_route(state, "quality")
    return "quality"


def _tokens(s: str) -> set[str]:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return {t for t in s.split() if len(t) > 2}


def _execute_quality_node(state: PipelineState) -> PipelineState:
    """Graph-Knoten: Einfaches Qualitäts-Maß (Unigram-F1 + ROUGE-L) zwischen NOTES und SUMMARY."""
    _append_trace(state, "quality")
    gold = _tokens(state.get("notes", "") or "")
    pred = _tokens(state.get("summary", "") or "")
    if not gold or not pred:
        state["quality_f1"] = 0.0
        state["quality_rougeL"] = 0.0
        return state
    inter = len(gold & pred)
    prec = inter / len(pred)
    rec = inter / len(gold)
    f1 = 0.0 if (prec + rec) == 0 else (2 * prec * rec) / (prec + rec)
    state["quality_f1"] = round(f1, 3)

    ref_seq = _word_sequence(state.get("notes", "") or "")
    pred_seq = _word_sequence(state.get("summary", "") or "")
    state["quality_rougeL"] = round(_rouge_l_f1(ref_seq, pred_seq), 3)
    return state


def _word_sequence(s: str) -> list[str]:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return [t for t in s.split() if len(t) > 2]


def _rouge_l_f1(reference_tokens: list[str], prediction_tokens: list[str]) -> float:
    if not reference_tokens or not prediction_tokens:
        return 0.0
    n = len(reference_tokens)
    m = len(prediction_tokens)
    if n == 0 or m == 0:
        return 0.0

    prev = [0] * (m + 1)
    for i in range(1, n + 1):
        curr = [0] * (m + 1)
        ref_tok = reference_tokens[i - 1]
        for j in range(1, m + 1):
            if ref_tok == prediction_tokens[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = curr[j - 1] if curr[j - 1] >= prev[j] else prev[j]
        prev = curr

    lcs = float(prev[m])
    precision = lcs / m
    recall = lcs / n
    return 0.0 if (precision + recall) == 0 else (2 * precision * recall) / (precision + recall)


def _execute_judge_node(state: PipelineState) -> PipelineState:
    """Graph-Knoten: LLM-as-a-judge (ein Gesamt-Score 0-5, nur Zahl)."""
    _append_trace(state, "judge")
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


def _execute_aggregator_node(state: PipelineState) -> PipelineState:
    """Graph-Knoten: Aggregiert Judge-, Quality- und Critic Scores."""
    _append_trace(state, "aggregator")
    quality = state.get("quality_f1", 0.0)
    judge_norm = state.get("judge_score", 0.0) / 5.0
    critic = state.get("critic_score", 0.0)
    candidates = [value for value in (quality, judge_norm, critic) if value is not None and value > 0]
    aggregate = round(sum(candidates) / len(candidates), 3) if candidates else 0.0
    state["judge_aggregate"] = aggregate
    return state


def _execute_integrator_node(state: PipelineState) -> PipelineState:
    """Graph-Knoten: Integrator-Agent ausführen."""
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
    """Generiert Graphviz DOT-Darstellung des Workflows mit optionalen dynamischen Werten."""
    if state is None:
        return r"""
digraph G {
  rankdir=LR;
  node [shape=box, style="rounded,filled", color="#9ca3af", fillcolor="#f9fafb", fontname="Inter"];

  input      [label="Input (raw text/PDF extract)"];
  retriever  [label="Retriever/Preprocess"];
  reader     [label="Reader - Notes"];
  results_extractor [label="Results Extractor (metrics recovery)"];
  summarizer [label="Summarizer"];
  translator [label="Translator (DE/EN)"];
  keyword    [label="Keyword Extraction"];
  critic_node [label="Critic - Review"];
  quality    [label="Quality (F1)"];
  judge      [label="LLM Judge"];
  aggregator [label="Judge Aggregator"];
  integrator [label="Integrator - Meta Summary"];
  output     [label="Output (notes, summary, critic, meta, f1, judge)"];

  input -> retriever -> reader -> summarizer -> translator -> keyword -> critic_node;
  reader -> results_extractor -> summarizer [style="dashed"];
  critic_node -> quality [label="long summary"];
  critic_node -> judge [label="short summary", style="dashed"];
  critic_node -> summarizer [label="rework (low critic)", style="dotted"];
  quality -> judge -> aggregator -> integrator -> output;
  judge -> aggregator;
}
""".strip()

    reader_time = state.get("reader_s", 0.0)
    extractor_time = state.get("results_extractor_s", 0.0)
    summarizer_time = state.get("summarizer_s", 0.0)
    critic_time = state.get("critic_s", 0.0)
    integrator_time = state.get("integrator_s", 0.0)
    translator_time = state.get("translator_s", 0.0)
    keyword_time = state.get("keyword_s", 0.0)
    f1_score = state.get("quality_f1", 0.0)
    judge_score = state.get("judge_score", 0.0)
    judge_aggregate = state.get("judge_aggregate", 0.0)
    translation_preview = (state.get("summary_translated", "") or "").replace('"', "'")
    translation_preview = translation_preview[:40] + ("…" if len(translation_preview) > 40 else "")
    keywords_label = state.get("keywords", "") or "no keywords"
    critic_label = f"Critic - Review\\n{critic_time:.2f}s"

    reader_label = f"Reader - Notes\\n{reader_time:.2f}s"
    summarizer_label = f"Summarizer - Summary\\n{summarizer_time:.2f}s"
    results_extractor_label = f"Results Extractor\\n{extractor_time:.2f}s"
    translator_label = f"Translator\\n{translation_preview}\\n{translator_time:.2f}s"
    keyword_label = f"Keywords\\n{keywords_label}\\n{keyword_time:.2f}s"
    quality_label = f"Quality (F1)\\n{f1_score:.3f}"
    judge_label = f"LLM Judge\\n{judge_score:.1f}/5"
    aggregator_label = f"Judge Aggregate\\n{judge_aggregate:.3f}"
    integrator_label = f"Integrator - Meta Summary\\n{integrator_time:.2f}s"

    return f"""
digraph G {{
  rankdir=LR;
  node [shape=box, style="rounded,filled", color="#667eea", fillcolor="#f0f4ff", fontname="Inter"];
  edge [color="#9ca3af"];

  input      [label="Input\\n(raw text/PDF)", fillcolor="#e0e7ff", color="#667eea"];
  retriever  [label="Retriever/Preprocess\\nAnalysis Context", fillcolor="#f0f4ff"];
  reader     [label="{reader_label}", fillcolor="#dbeafe"];
  results_extractor [label="{results_extractor_label}", fillcolor="#fde68a"];
  summarizer [label="{summarizer_label}", fillcolor="#dbeafe"];
  translator [label="{translator_label}", fillcolor="#fde68a"];
  keyword    [label="{keyword_label}", fillcolor="#fef3c7"];
  critic_node [label="{critic_label}", fillcolor="#dbeafe"];
  quality    [label="{quality_label}", fillcolor="#d1fae5"];
  judge      [label="{judge_label}", fillcolor="#c7d2fe"];
  aggregator [label="{aggregator_label}", fillcolor="#c5fde2"];
  integrator [label="{integrator_label}", fillcolor="#dbeafe"];
  output     [label="Output\\n(all results)", fillcolor="#e0e7ff", color="#667eea"];

  input -> retriever -> reader -> summarizer -> translator -> keyword -> critic_node;
  reader -> results_extractor -> summarizer [style="dashed"];
  critic_node -> quality [label="long summary", style="solid"];
  critic_node -> judge [label="short summary", style="dashed"];
  critic_node -> summarizer [label="rework (low critic)", style="dotted"];
  quality -> judge -> aggregator -> integrator -> output;
  judge -> aggregator;
}}
""".strip()


def _build_langgraph_workflow() -> Any:
    """Baut LangGraph-Workflow mit Retrieval/Preprocessing, vier Agenten und Qualitäts-Metrik."""
    graph = StateGraph(PipelineState)
    graph.add_node("retriever", _execute_retriever_node)
    graph.add_node("reader", _execute_reader_node)
    graph.add_node("results_extractor", _execute_results_extractor_node)
    graph.add_node("summarizer", _execute_summarizer_node)
    graph.add_node("translator", _execute_translator_node)
    graph.add_node("keyword", _execute_keyword_node)
    graph.add_node("critic_node", _execute_critic_node)  # Umbenannt: Node-Name != State-Key
    graph.add_node("quality", _execute_quality_node)
    graph.add_node("judge", _execute_judge_node)
    graph.add_node("aggregator", _execute_aggregator_node)
    graph.add_node("integrator", _execute_integrator_node)
    graph.set_entry_point("retriever")
    graph.add_edge("retriever", "reader")
    graph.add_conditional_edges("reader", _reader_post_path)
    graph.add_edge("results_extractor", "summarizer")
    graph.add_edge("summarizer", "translator")
    graph.add_edge("translator", "keyword")
    graph.add_edge("keyword", "critic_node")
    graph.add_conditional_edges("critic_node", _critic_post_path)
    graph.add_edge("quality", "judge")
    graph.add_edge("judge", "aggregator")
    graph.add_edge("aggregator", "integrator")
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
        "quant_signal": "NO",
        "quant_signal_label": "NO (no quantitative signal detected)",
        "quant_keyword_hits": [],
        "quant_number_samples": [],
        "notes": "",
        "extracted_metrics_count": 0,
        "recovery_attempted": False,
        "recovered_results": "",
        "summary": "",
        "critic": "",
        "meta": "",
        "reader_s": 0.0,
        "summarizer_s": 0.0,
        "critic_s": 0.0,
        "translator_s": 0.0,
        "keyword_s": 0.0,
        "results_extractor_s": 0.0,
        "summary_translated": "",
        "keywords": "",
        "judge_aggregate": 0.0,
        "critic_score": 0.0,
        "critic_loops": 0,
        "integrator_s": 0.0,
        "quality_f1": 0.0,
        "quality_rougeL": 0.0,
        "judge_score": 0.0,
        "execution_trace": [],
        "routing_trace": [],
        "translator_note": "",
        "keyword_note": "",
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
        "results_extractor_s": final_state.get("results_extractor_s", 0.0),
        "translator_s": final_state.get("translator_s", 0.0),
        "keyword_s": final_state.get("keyword_s", 0.0),
        "integrator_s": final_state.get("integrator_s", 0.0),
        "quality_f1": final_state.get("quality_f1", 0.0),
        "quality_rougeL": final_state.get("quality_rougeL", 0.0),
        "judge_score": final_state.get("judge_score", 0.0),
        "judge_aggregate": final_state.get("judge_aggregate", 0.0),
        "critic_score": final_state.get("critic_score", 0.0),
        "critic_loops": final_state.get("critic_loops", 0),
        "quant_signal": final_state.get("quant_signal", ""),
        "extracted_metrics_count": final_state.get("extracted_metrics_count", 0),
        "confidence": final_state.get("confidence", ""),
    })
    
    return {
        "structured": final_state.get("notes", ""),
        "recovered_results": final_state.get("recovered_results", ""),
        "summary": final_state.get("summary", ""),
        "summary_translated": final_state.get("summary_translated", ""),
        "keywords": final_state.get("keywords", ""),
        "critic": final_state.get("critic", ""),
        "meta": final_state.get("meta", ""),
        "reader_s": final_state.get("reader_s", 0.0),
        "summarizer_s": final_state.get("summarizer_s", 0.0),
        "critic_s": final_state.get("critic_s", 0.0),
        "translator_s": final_state.get("translator_s", 0.0),
        "keyword_s": final_state.get("keyword_s", 0.0),
        "results_extractor_s": final_state.get("results_extractor_s", 0.0),
        "integrator_s": final_state.get("integrator_s", 0.0),
        "quality_f1": final_state.get("quality_f1", 0.0),
        "judge_score": final_state.get("judge_score", 0.0),
        "judge_aggregate": final_state.get("judge_aggregate", 0.0),
        "critic_score": final_state.get("critic_score", 0.0),
        "critic_loops": final_state.get("critic_loops", 0),
        "quant_signal": final_state.get("quant_signal", ""),
        "quant_signal_label": final_state.get("quant_signal_label", ""),
        "quant_keyword_hits": final_state.get("quant_keyword_hits", []),
        "quant_number_samples": final_state.get("quant_number_samples", []),
        "extracted_metrics_count": final_state.get("extracted_metrics_count", 0),
        "recovery_attempted": final_state.get("recovery_attempted", False),
        "latency_s": total_duration,
        "input_chars": input_chars,
        "graph_dot": _generate_graph_visualization_dot(final_state),  # Dynamisch mit Werten
        "execution_trace": final_state.get("execution_trace", []) or [],
        "routing_trace": final_state.get("routing_trace", []) or [],
        "translator_note": final_state.get("translator_note", ""),
        "keyword_note": final_state.get("keyword_note", ""),
        "confidence": final_state.get("confidence", "") or confidence_line or "",
    }
