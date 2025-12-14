"""
LangChain Pipeline: Sequenzielle Ausführung der Multi-Agent-Pipeline.
"""

from typing import Optional, Dict, Any
from time import perf_counter

from agents.reader import run as run_reader
from agents.summarizer import run as run_summarizer
from agents.critic import run as run_critic
from agents.integrator import run as run_integrator
from telemetry import log_row
from llm import configure
from utils import (
    build_analysis_context,
    detect_quantitative_signal,
    count_numeric_results,
    extract_confidence_line,
)


def run_pipeline(input_text: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Führt LangChain-Pipeline sequenziell aus: Reader - Summarizer - Critic - Integrator.
    
    Gibt Dictionary zurück mit: structured, summary, critic, meta, Timing-Infos und Gesamt-Latenz.
    """
    config_dict = config or {}
    configure(config_dict)
    
    execution_trace = ["retriever"]
    analysis_context = build_analysis_context(input_text, config_dict)
    
    if not analysis_context or len(analysis_context.strip()) < 100:
        return _create_error_response(
            "No valid text detected. Try disabling truncation or re-uploading the PDF."
        )
    
    start_time_reader = perf_counter()
    execution_trace.append("reader")
    structured_notes = run_reader(analysis_context)
    end_time_reader = perf_counter()
    reader_duration = round(end_time_reader - start_time_reader, 2)
    metrics_count = count_numeric_results(structured_notes)
    quant_info = detect_quantitative_signal(analysis_context)
    
    start_time_summarizer = perf_counter()
    execution_trace.append("summarizer")
    summary = run_summarizer(structured_notes)
    end_time_summarizer = perf_counter()
    summarizer_duration = round(end_time_summarizer - start_time_summarizer, 2)
    
    start_time_critic = perf_counter()
    execution_trace.append("critic")
    critic_result = run_critic(notes=structured_notes, summary=summary)
    critic_text = critic_result.get("critic") or critic_result.get("critique") or ""
    end_time_critic = perf_counter()
    critic_duration = round(end_time_critic - start_time_critic, 2)
    
    start_time_integrator = perf_counter()
    execution_trace.append("integrator")
    meta_summary = run_integrator(notes=structured_notes, summary=summary, critic=critic_text)
    end_time_integrator = perf_counter()
    integrator_duration = round(end_time_integrator - start_time_integrator, 2)
    confidence_line = extract_confidence_line(meta_summary)
    
    total_duration = round(end_time_integrator - start_time_reader, 2)
    input_chars = len(analysis_context)
    timing_statistics = {
        "reader_s": reader_duration,
        "summarizer_s": summarizer_duration,
        "critic_s": critic_duration,
        "integrator_s": integrator_duration,
    }
    
    log_row({
        "engine": "langchain",
        "input_chars": input_chars,
        "summary_len": len(str(summary)),
        "meta_len": len(str(meta_summary)),
        "latency_s": total_duration,
        **timing_statistics,
        "quant_signal": quant_info.get("signal", ""),
        "extracted_metrics_count": metrics_count,
        "confidence": confidence_line,
    })
    
    # Ergebnis zusammenstellen
    return {
        "structured": structured_notes,
        "summary": summary,
        "critic": critic_text,
        "meta": meta_summary,
        "latency_s": total_duration,
        "input_chars": input_chars,
        **timing_statistics,
        "execution_trace": execution_trace,
        "quant_signal": quant_info.get("signal", ""),
        "quant_signal_label": quant_info.get("label", ""),
        "quant_keyword_hits": quant_info.get("keyword_hits", []),
        "quant_number_samples": quant_info.get("number_samples", []),
        "extracted_metrics_count": metrics_count,
        "confidence": confidence_line or "",
    }


def _create_error_response(error_message: str) -> Dict[str, Any]:
    """Erstellt standardisierte Fehlerantwort."""
    return {
        "structured": "[Input empty or too short]",
        "summary": "",
        "critic": "",
        "meta": error_message,
        "reader_s": 0.0,
        "summarizer_s": 0.0,
        "critic_s": 0.0,
        "integrator_s": 0.0,
        "execution_trace": [],
    }
