# workflows/dspy_pipeline.py
from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple
from time import perf_counter
import json, os, re

# Optional: unsere bestehende CSV-Telemetrie nutzen
try:
    from telemetry import log_row
except Exception:
    def log_row(_row: dict):  # no-op fallback
        pass

# --- Abhängigkeiten behutsam importieren ---
try:
    import dspy
    HAVE_DSPY = True
except Exception:
    HAVE_DSPY = False

try:
    import litellm  # noqa: F401  (wird indirekt von dspy genutzt)
    HAVE_LITELLM = True
except Exception:
    HAVE_LITELLM = False

DSPY_READY = HAVE_DSPY and HAVE_LITELLM


def _lean_fallback(msg: str) -> Dict[str, Any]:
    return {
        "structured": "",
        "summary": "",
        "critic": "",
        "meta": f"DSPy is disabled: {msg}",
        "reader_s": 0.0,
        "summarizer_s": 0.0,
        "critic_s": 0.0,
        "integrator_s": 0.0,
        "latency_s": 0.0,
        "graph_dot": None,
        "dspy_available": DSPY_READY,
    }


if not DSPY_READY:
    # Stub, damit die App nicht crasht wenn Pakete fehlen
    def run_pipeline(input_text: str, cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        why = "missing 'dspy-ai'" if not HAVE_DSPY else "missing 'litellm'"
        return _lean_fallback(f"install dspy-ai and litellm to enable DSPy ({why}).")
else:
    # ---------------- DSPy: Konfiguration & Module ----------------

    # Provider-Fix: LiteLLM erwartet "ollama/<model>"
    def _configure_dspy(cfg: Optional[Dict[str, Any]] = None):
        cfg = cfg or {}
        model = cfg.get("model", "gpt-4.1")
        base = cfg.get("api_base") or os.getenv("OPENAI_BASE_URL")
        api_key = cfg.get("api_key") or os.getenv("OPENAI_API_KEY", "")
        temperature = float(cfg.get("temperature", 0.0))
        max_tokens = int(cfg.get("max_tokens", 256))

        lm = dspy.LM(
            model=model,
            api_base=base,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        dspy.settings.configure(lm=lm)

    # Sanitizer: keine JSON-Fragmente, keine Mehrfach-Leerzeilen
    def _sanitize(s: str) -> str:
        s = re.sub(r"^\s*[{[]\s*|\s*[}\]]\s*$", "", s or "", flags=re.S)
        s = re.sub(r"\n{3,}", "\n\n", s)
        return s.strip()

    # ---------------- Signatures ----------------
    class ReadNotes(dspy.Signature):
        """Return structured scientific notes from TEXT as per schema."""
        TEXT: str = dspy.InputField()
        NOTES: str = dspy.OutputField(desc="Structured notes per schema")

    class Summarize(dspy.Signature):
        """Grounded 200-300 word summary from NOTES with takeaways."""
        NOTES: str = dspy.InputField()
        SUMMARY: str = dspy.OutputField()

    class Critique(dspy.Signature):
        """Critique SUMMARY vs NOTES with rubric and short fixes."""
        NOTES: str = dspy.InputField()
        SUMMARY: str = dspy.InputField()
        CRITIC: str = dspy.OutputField()

    class Integrate(dspy.Signature):
        """Executive meta-summary fusing SUMMARY + CRITIC grounded in NOTES."""
        NOTES: str = dspy.InputField()
        SUMMARY: str = dspy.InputField()
        CRITIC: str = dspy.InputField()
        META: str = dspy.OutputField()

    # ---------------- Module (strikte Templates, keine JSON) ----------------
    class ReaderM(dspy.Module):
        def __init__(self):
            super().__init__()
            self.gen = dspy.Predict(ReadNotes)

        def forward(self, text: str):
            schema = (
                "Title: <text or 'not reported'>\n"
                "Objective: <1-2 sentences or 'not reported'>\n"
                "Methods:\n- <method>\n- <dataset or setup>\n- <tools/frameworks>\n"
                "Results:\n- <metric: value>\n- <comparison>\n"
                "Limitations: <text or 'not reported'>\n"
                "Takeaways:\n- <bullet>\n- <bullet>\n- <bullet>\n"
            )
            prompt = (
                "ONLY return the filled template below. "
                "No JSON, no extra prose, no author names or citations.\n\n"
                f"{schema}\n\nTEXT:\n{text}\n\nReturn ONLY the template, nothing else."
            )
            out = self.gen(TEXT=prompt)
            return dspy.Prediction(NOTES=_sanitize(out.NOTES))

    class SummarizerM(dspy.Module):
        def __init__(self):
            super().__init__()
            self.gen = dspy.Predict(Summarize)

        def forward(self, notes: str):
            tpl = (
                "Objective: <1-2 sentences>\n"
                "Method: <2-4 sentences>\n"
                "Results: <numbers if present; else 'not reported'>\n"
                "Limitations: <short>\n"
                "Takeaways:\n- <bullet>\n- <bullet>\n- <bullet>\n"
            )
            prompt = (
                "Write a grounded 200-300 word summary from NOTES. "
                "Use the following template, no JSON, no citations. "
                "Return ONLY the filled template.\n\n"
                f"TEMPLATE:\n{tpl}\n\nNOTES:\n{notes}"
            )
            out = self.gen(NOTES=prompt)
            return dspy.Prediction(SUMMARY=_sanitize(out.SUMMARY))

    class CriticM(dspy.Module):
        def __init__(self):
            super().__init__()
            self.gen = dspy.Predict(Critique)

        def forward(self, notes: str, summary: str):
            rubric = (
                "Coherence: <0-5>\nGroundedness: <0-5>\nCoverage: <0-5>\nSpecificity: <0-5>\n"
                "Improvements:\n- <≤1 sentence>\n- <≤1 sentence>\n- <optional>\n"
            )
            prompt = (
                "Score SUMMARY vs NOTES. Return ONLY this rubric (no JSON):\n"
                f"{rubric}\n\nNOTES:\n{notes}\n\nSUMMARY:\n{summary}"
            )
            out = self.gen(NOTES=notes, SUMMARY=prompt)
            return dspy.Prediction(CRITIC=_sanitize(out.CRITIC))

    class IntegratorM(dspy.Module):
        def __init__(self):
            super().__init__()
            self.gen = dspy.Predict(Integrate)

        def forward(self, notes: str, summary: str, critic: str):
            tpl = (
                "**Objective:** <one sentence>\n"
                "**Method:** <one sentence>\n"
                "**Results:** <one sentence>\n"
                "**Limitations:** <one sentence>\n"
                "**Takeaways:**\n- <bullet>\n- <bullet>\n- <bullet>\n"
                "Open Questions:\n- <q1>\n- <q2>\n"
                "Confidence: <High|Medium|Low>\n"
            )
            prompt = (
                "Fuse SUMMARY + CRITIC, grounded strictly in NOTES. "
                "Return ONLY the following template (no JSON):\n"
                f"{tpl}\n\nNOTES:\n{notes}\n\nSUMMARY:\n{summary}\n\nCRITIC:\n{critic}"
            )
            out = self.gen(NOTES=notes, SUMMARY=summary, CRITIC=prompt)
            return dspy.Prediction(META=_sanitize(out.META))

    # ---------------- Pipeline (optional Teleprompting) ----------------
    class PaperPipeline(dspy.Module):
        def __init__(self):
            super().__init__()
            self.reader = ReaderM()
            self.summarizer = SummarizerM()
            self.critic = CriticM()
            self.integrator = IntegratorM()

        def forward(self, input_text: str):
            t0 = perf_counter()
            notes = self.reader(input_text).NOTES
            t1 = perf_counter()
            summary = self.summarizer(notes).SUMMARY
            t2 = perf_counter()
            critic = self.critic(notes, summary).CRITIC
            t3 = perf_counter()
            meta = self.integrator(notes, summary, critic).META
            t4 = perf_counter()

            return dspy.Prediction(
                NOTES=notes, SUMMARY=summary, CRITIC=critic, META=meta,
                reader_s=round(t1 - t0, 2),
                summarizer_s=round(t2 - t1, 2),
                critic_s=round(t3 - t2, 2),
                integrator_s=round(t4 - t3, 2),
                total_s=round(t4 - t0, 2),
            )

    # -------- Optional: leichtgewichtiges Teleprompting (Bootstrap FS) --------
    #
    # Du kannst kleine Dev-Beispiele in eval/dev.jsonl (freiwillig) ablegen:
    # Jede Zeile: {"text": "...", "target_summary": "..."}
    #
    # Wir nehmen eine sehr einfache Overlap-Metrik (keine externen Pakete).
    def _word_f1(pred: str, gold: str) -> float:
        ps = set(w.lower() for w in re.findall(r"\w+", pred))
        gs = set(w.lower() for w in re.findall(r"\w+", gold))
        if not ps or not gs:
            return 0.0
        prec = len(ps & gs) / len(ps)
        rec = len(ps & gs) / len(gs)
        return 0.0 if (prec + rec) == 0 else (2 * prec * rec) / (prec + rec)

    def _load_devset(path: str) -> List[Tuple[str, str]]:
        if not os.path.exists(path):
            return []
        pairs: List[Tuple[str, str]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    text = obj.get("text", "")
                    gold = obj.get("target_summary", "")
                    if text and gold:
                        pairs.append((text, gold))
                except Exception:
                    continue
        return pairs

    def _teleprompt_if_requested(pipeline: PaperPipeline, cfg: Dict[str, Any]):
        # aktiviere mit cfg["dspy_teleprompt"]=True
        if not cfg.get("dspy_teleprompt"):
            return
        dev_path = cfg.get("dspy_dev_path", "eval/dev.jsonl")
        dev = _load_devset(dev_path)
        if not dev:
            return  # nichts zu tun

        # sehr kleine BootstrapFewShot-Optimierung
        tp = dspy.teleprompt.BootstrapFewShot(
            metric=lambda gold, pred: _word_f1(pred or "", gold or ""),
            max_bootstrapped_demos=3,
            max_labeled_demos=3,
        )

        # Wir optimieren hier nur die Summarizer-Stage (als Beispiel)
        tp.compile(pipeline.summarizer, trainset=[
            {"NOTES": pipeline.reader(text).NOTES, "SUMMARY": gold}
            for (text, gold) in dev
        ])

    # ---------------- Public API ----------------
    def run_pipeline(input_text: str, cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cfg = cfg or {}
        _configure_dspy(cfg)

        pipe = PaperPipeline()
        _teleprompt_if_requested(pipe, cfg)

        t0 = perf_counter()
        out = pipe(input_text=input_text)
        t1 = perf_counter()

        result = {
            "structured": out.NOTES,
            "summary": out.SUMMARY,
            "critic": out.CRITIC,
            "meta": out.META,
            "reader_s": out.reader_s,
            "summarizer_s": out.summarizer_s,
            "critic_s": out.critic_s,
            "integrator_s": out.integrator_s,
            "latency_s": round(t1 - t0, 2),
            "input_chars": len(input_text or ""),
            "graph_dot": None,  # nur LangGraph
            "dspy_available": True,
        }

        # Telemetrie-CSV (so wie bei LangChain)
        try:
            log_row({
                "engine": "dspy",
                "input_chars": len(input_text or ""),
                "summary_len": len(result["summary"]),
                "meta_len": len(result["meta"]),
                "latency_s": result["latency_s"],
                "reader_s": result["reader_s"],
                "summarizer_s": result["summarizer_s"],
                "critic_s": result["critic_s"],
                "integrator_s": result["integrator_s"],
            })
        except Exception:
            pass

        return result
