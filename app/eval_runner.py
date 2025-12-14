# eval_runner.py
import json, re, os, sys
from typing import Dict

from rouge_score import rouge_scorer

from utils import build_analysis_context
from workflows.langchain_pipeline import run_pipeline as run_lc
from workflows.langgraph_pipeline import run_pipeline as run_lg
from workflows.dspy_pipeline import run_pipeline as run_dspy

_ROUGE_TARGETS = [
    ("rougeLsum", "rougeL"),
]

_ROUGE_SCORER = rouge_scorer.RougeScorer(
    [target for target, _ in _ROUGE_TARGETS], use_stemmer=True
)

def _tokens(s: str) -> set[str]:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return {t for t in s.split() if len(t) > 2}

def unigram_f1(notes: str, summary: str) -> float:
    P = _tokens(summary)
    G = _tokens(notes)
    if not P or not G:
        return 0.0
    inter = len(P & G)
    prec = inter / len(P)
    rec = inter / len(G)
    return 0.0 if (prec + rec) == 0 else (2 * prec * rec) / (prec + rec)

def _rouge_scores(notes: str, summary: str) -> Dict[str, float]:
    scores = _ROUGE_SCORER.score(notes or "", summary or "")
    return {
        target_name: scores[source_name].fmeasure
        for source_name, target_name in _ROUGE_TARGETS
    }

def _evaluate_metrics(notes: str, summary: str) -> Dict[str, float]:
    return {
        "f1": unigram_f1(notes, summary),
        **_rouge_scores(notes, summary),
    }

def _round_metrics(metrics: Dict[str, float]) -> Dict[str, float]:
    return {k: round(v, 3) for k, v in metrics.items()}

def run_example(text: str, cfg: Dict):
    ctx = build_analysis_context(text, cfg)
    out_lc = run_lc(ctx, cfg)
    out_lg = run_lg(ctx, cfg)
    out_dp = run_dspy(ctx, cfg)

    def _annotate(out: Dict) -> Dict:
        summary = out.get("summary", "")
        metrics = _round_metrics(_evaluate_metrics(ctx, summary))
        metric_detail = {k: v for k, v in metrics.items() if k != "f1"}
        return {
            **out,
            "f1": metrics.get("f1", 0.0),
            "metrics": metric_detail,
        }

    return {
        "lc": _annotate(out_lc),
        "lg": _annotate(out_lg),
        "dspy": _annotate(out_dp),
    }

if __name__ == "__main__":
    # Basis-Konfiguration
    cfg = {
        "truncate_chars": 4000,
        "sections_enabled": True,
        "section_budget_chars": 3500,
        "min_analysis_chars": 800,
        "auto_expand_if_short": True,
        # DSPy Teleprompting hier aus; in der App per Toggle
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

    # Kurzer Überblick
    METRIC_LABELS = [
        ("rougeL", "RL"),
    ]

    def _format_metrics(metrics: Dict[str, float]) -> str:
        return " ".join(
            f"{label}={metrics.get(key,0.0):.3f}" for key, label in METRIC_LABELS
        )

    for i, r in enumerate(results, 1):
        print(f"\n# Example {i}")
        for k in ("lc","lg","dspy"):
            metric_string = _format_metrics(r[k].get("metrics", {}))
            print(
                f"  {k.upper():5s}  F1={r[k]['f1']:.3f}  {metric_string}  "
                f"total_s={r[k].get('latency_s','?')}"
            )
