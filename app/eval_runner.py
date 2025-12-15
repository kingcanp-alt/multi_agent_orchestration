"""
Evaluation runner for comparing all pipelines.
"""

from __future__ import annotations

import json, re, os, sys
from typing import Dict

from utils import build_analysis_context
from workflows.dspy_pipeline import run_pipeline as run_dspy
from workflows.langchain_pipeline import run_pipeline as run_lc
from workflows.langgraph_pipeline import run_pipeline as run_lg

def _tokens(s: str) -> set[str]:
    """
    Extrahiert Tokens aus Text für F1-Berechnung.
    
    Einfache Tokenisierung. Kleinbuchstaben, Interpunktion entfernen, Wörter
    > 2 Zeichen behalten. Kurze Wörter meist Stoppwörter, helfen nicht beim Matching.
    """
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return {t for t in s.split() if len(t) > 2}

def unigram_f1(notes: str, summary: str) -> float:
    """
    Berechnet Unigram-F1-Score zwischen Notizen und Zusammenfassung.
    
    Einfache Überlappungs-Metrik. Nutzen Unigramme statt Bigramme/Trigramme.
    Schneller, gibt trotzdem vernünftiges Signal. Gut genug zum Vergleichen.
    """
    P = _tokens(summary)
    G = _tokens(notes)
    if not P or not G:
        return 0.0
    inter = len(P & G)
    prec = inter / len(P)
    rec = inter / len(G)
    return 0.0 if (prec + rec) == 0 else (2 * prec * rec) / (prec + rec)

def _evaluate_metrics(notes: str, summary: str) -> Dict[str, float]:
    """Bewertet Zusammenfassung gegen Notizen."""
    return {
        "f1": unigram_f1(notes, summary),
    }

def _round_metrics(metrics: Dict[str, float]) -> Dict[str, float]:
    """Rundet Metriken auf 3 Dezimalstellen für Lesbarkeit."""
    return {k: round(v, 3) for k, v in metrics.items()}

def run_example(text: str, cfg: Dict):
    """
    Führt alle drei Pipelines auf demselben Text aus und vergleicht.
    
    Führt LangChain, LangGraph und DSPy auf demselben Input aus, dann Metriken.
    F1-Score vergleicht Zusammenfassung mit ursprünglichen Notizen.
    """
    ctx = build_analysis_context(text, cfg)
    out_lc = run_lc(ctx, cfg)
    out_lg = run_lg(ctx, cfg)
    out_dp = run_dspy(ctx, cfg)

    def _annotate(out: Dict) -> Dict:
        """F1-Score zu Pipeline-Ausgabe hinzu."""
        summary = out.get("summary", "")
        metrics = _round_metrics(_evaluate_metrics(ctx, summary))
        return {
            **out,
            "f1": metrics.get("f1", 0.0),
        }

    return {
        "lc": _annotate(out_lc),
        "lg": _annotate(out_lg),
        "dspy": _annotate(out_dp),
    }

if __name__ == "__main__":
    # Base config
    cfg = {
        "dspy_teleprompt": False,
    }
    dev_path = "dev-set/dev.jsonl"
    if not os.path.exists(dev_path):
        print("Missing dev-set/dev.jsonl")
        sys.exit(1)

    results = []
    with open(dev_path, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            text = obj.get("text","")
            if not text:
                continue
            results.append(run_example(text, cfg))

    for i, r in enumerate(results, 1):
        print(f"\n# Example {i}")
        for k in ("lc","lg","dspy"):
            print(
                f"  {k.upper():5s}  F1={r[k]['f1']:.3f}  "
                f"total_s={r[k].get('latency_s','?')}"
            )
