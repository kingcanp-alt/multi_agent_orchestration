# eval_runner.py
import json, re, os, sys, time
from typing import Dict

from utils import build_analysis_context
from workflows.langchain_pipeline import run_pipeline as run_lc
from workflows.langgraph_pipeline import run_pipeline as run_lg
from workflows.dspy_pipeline import run_pipeline as run_dspy

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
    rec  = inter / len(G)
    return 0.0 if (prec+rec)==0 else (2*prec*rec)/(prec+rec)

def run_example(text: str, cfg: Dict):
    ctx = build_analysis_context(text, cfg)
    out_lc = run_lc(ctx, cfg)
    out_lg = run_lg(ctx, cfg)
    out_dp = run_dspy(ctx, cfg)

    score = lambda o: unigram_f1(ctx, o.get("summary",""))
    return {
        "lc": {"f1": round(score(out_lc),3), **out_lc},
        "lg": {"f1": round(score(out_lg),3), **out_lg},
        "dspy": {"f1": round(score(out_dp),3), **out_dp},
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
    for i, r in enumerate(results, 1):
        print(f"\n# Example {i}")
        for k in ("lc","lg","dspy"):
            print(f"  {k.upper():5s}  F1={r[k]['f1']:.3f}  total_s={r[k].get('latency_s','?')}")
