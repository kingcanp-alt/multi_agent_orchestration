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
        """Extract structured scientific notes from TEXT. Work ONLY with the provided TEXT.
        If an item is not explicitly stated, write 'not reported'. Do NOT invent facts.
        Do NOT include author names, emails, or affiliations.
        Return structured notes following this schema:
        Title: <paper title or 'not reported'>
        Objective: <1-2 sentences or 'not reported'>
        Methods:
        - <technique/model>
        - <dataset or setup>
        - <tools/frameworks>
        Results:
        - <metric: value>
        - <comparison>
        Limitations: <text or 'not reported'>
        Takeaways:
        - <bullet>
        - <bullet>
        - <bullet>
        If tables or metrics are present, extract numeric values. If no numbers exist, write 'not reported'.
        NEVER guess or interpolate metrics."""
        TEXT: str = dspy.InputField(desc="The scientific paper text to extract notes from")
        NOTES: str = dspy.OutputField(desc="Structured scientific notes following the schema above, no JSON, no extra prose")

    class Summarize(dspy.Signature):
        """Produce a concise scientific summary (200-300 words) from NOTES.
        Cover in this order: Objective -> Method (what/how) -> Results (numbers if present; otherwise say 'not reported')
        -> Limitations -> 3-5 Practical Takeaways (bulleted).
        Avoid speculation or citations. Do NOT invent metrics; if NOTES have no numbers, write 'not reported'."""
        NOTES: str = dspy.InputField(desc="Structured scientific notes")
        SUMMARY: str = dspy.OutputField(desc="200-300 word summary covering objective, method, results, limitations, and takeaways")

    class Critique(dspy.Signature):
        """Critique SUMMARY against NOTES. Judge for coherence, groundedness, coverage, and specificity.
        Return a rubric with scores 0-5 for each dimension, followed by improvement suggestions.
        Format:
        Coherence: <0-5>
        Groundedness: <0-5>
        Coverage: <0-5>
        Specificity: <0-5>
        Improvements:
        - <short fix #1>
        - <short fix #2>
        - <optional fix #3>"""
        NOTES: str = dspy.InputField(desc="Original structured notes (ground truth)")
        SUMMARY: str = dspy.InputField(desc="Summary to be critiqued")
        CRITIC: str = dspy.OutputField(desc="Critique with rubric scores and improvement suggestions")

    class Integrate(dspy.Signature):
        """Create an executive meta-summary by fusing SUMMARY with CRITIC feedback, grounded strictly in NOTES.
        Do not invent metrics or citations. Provide a concise meta-summary covering:
        Objective (one sentence), Method (one sentence), Results (one sentence), Limitations (one sentence),
        Takeaways (3 bullets), Open Questions (2 questions), and Confidence level (High/Medium/Low).
        Confidence: High if all rubric scores ≥4; Medium if any score is 3; Low if any score ≤2."""
        NOTES: str = dspy.InputField(desc="Original structured notes (ground truth)")
        SUMMARY: str = dspy.InputField(desc="Summary to integrate")
        CRITIC: str = dspy.InputField(desc="Critique feedback with rubric scores")
        META: str = dspy.OutputField(desc="Executive meta-summary with objective, method, results, limitations, takeaways, open questions, and confidence")

    # ---------------- Module (deklarativ - DSPy generiert Prompts aus Signatures) ----------------
    class ReaderM(dspy.Module):
        """Reader module that extracts structured notes from text using declarative signatures."""
        def __init__(self):
            super().__init__()
            self.gen = dspy.Predict(ReadNotes)

        def forward(self, text: str):
            # Deklarativ: Direkt die Signature nutzen, DSPy generiert den Prompt automatisch
            out = self.gen(TEXT=text)
            return dspy.Prediction(NOTES=_sanitize(out.NOTES))

    class SummarizerM(dspy.Module):
        """Summarizer module that creates summaries from notes using declarative signatures."""
        def __init__(self):
            super().__init__()
            self.gen = dspy.Predict(Summarize)

        def forward(self, notes: str = None, NOTES: str = None):
            # Deklarativ: Direkt die Signature nutzen, DSPy generiert den Prompt automatisch
            # Unterstützt sowohl 'notes' als auch 'NOTES' für Kompatibilität mit DSPy Teleprompting
            input_notes = NOTES if NOTES is not None else notes
            if input_notes is None:
                raise ValueError("Either 'notes' or 'NOTES' must be provided")
            out = self.gen(NOTES=input_notes)
            return dspy.Prediction(SUMMARY=_sanitize(out.SUMMARY))

    class CriticM(dspy.Module):
        """Critic module that critiques summaries using declarative signatures."""
        def __init__(self):
            super().__init__()
            self.gen = dspy.Predict(Critique)

        def forward(self, notes: str, summary: str):
            # Deklarativ: Direkt die Signature nutzen, DSPy generiert den Prompt automatisch
            out = self.gen(NOTES=notes, SUMMARY=summary)
            return dspy.Prediction(CRITIC=_sanitize(out.CRITIC))

    class IntegratorM(dspy.Module):
        """Integrator module that creates meta-summaries using declarative signatures."""
        def __init__(self):
            super().__init__()
            self.gen = dspy.Predict(Integrate)

        def forward(self, notes: str, summary: str, critic: str):
            # Deklarativ: Direkt die Signature nutzen, DSPy generiert den Prompt automatisch
            out = self.gen(NOTES=notes, SUMMARY=summary, CRITIC=critic)
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
            # Verwende NOTES= für Kompatibilität mit Teleprompting
            summary = self.summarizer(NOTES=notes).SUMMARY
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
    # Du kannst kleine Dev-Beispiele in dev-set/dev.jsonl (freiwillig) ablegen:
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
        dev_path = cfg.get("dspy_dev_path", "dev-set/dev.jsonl")
        dev = _load_devset(dev_path)
        if not dev:
            return  # nichts zu tun

        # Metrik-Funktion: pred ist ein Prediction-Objekt mit .SUMMARY Attribut
        def _metric(gold, pred, trace=None):
            # Extrahiere SUMMARY aus Prediction-Objekt
            pred_text = ""
            if hasattr(pred, "SUMMARY"):
                pred_text = str(pred.SUMMARY)
            elif isinstance(pred, dict):
                pred_text = str(pred.get("SUMMARY", ""))
            else:
                pred_text = str(pred)
            gold_text = str(gold) if gold else ""
            return _word_f1(pred_text, gold_text)

        # sehr kleine BootstrapFewShot-Optimierung
        tp = dspy.teleprompt.BootstrapFewShot(
            metric=_metric,
            max_bootstrapped_demos=3,
            max_labeled_demos=3,
        )

        # Wir optimieren hier nur die Summarizer-Stage (als Beispiel)
        # Trainset: Liste von dspy.Example oder Dict mit NOTES und SUMMARY
        trainset = []
        for (text, gold) in dev:
            notes = pipeline.reader(text).NOTES
            trainset.append(dspy.Example(NOTES=notes, SUMMARY=gold).with_inputs("NOTES"))
        
        if trainset:
            # compile() gibt eine optimierte Version zurück - diese muss verwendet werden!
            optimized_summarizer = tp.compile(pipeline.summarizer, trainset=trainset)
            pipeline.summarizer = optimized_summarizer

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
