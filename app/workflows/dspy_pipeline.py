# workflows/dspy_pipeline.py
from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple
from time import perf_counter
import json, os, re

from utils import count_numeric_results, extract_confidence_line

# Use CSV telemetry
try:
    from telemetry import log_row
except Exception:
    def log_row(_row: dict):
        pass

# Import dependencies
try:
    import dspy
    HAVE_DSPY = True
except Exception:
    HAVE_DSPY = False

try:
    import litellm  # noqa: F401
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
        "execution_trace": [],
    }


if not DSPY_READY:
    def run_pipeline(input_text: str, cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        why = "missing 'dspy-ai'" if not HAVE_DSPY else "missing 'litellm'"
        return _lean_fallback(f"install dspy-ai and litellm to enable DSPy ({why}).")
else:
    # DSPy configuration
    def _configure_dspy(cfg: Optional[Dict[str, Any]] = None):
        """Configures DSPy language model. Uses LiteLLM for provider abstraction."""
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

    # Sanitize output
    def _sanitize(s: str) -> str:
        """Removes JSON fragments and excessive blank lines from LLM output."""
        s = re.sub(r"^\s*[{[]\s*|\s*[}\]]\s*$", "", s or "", flags=re.S)
        s = re.sub(r"\n{3,}", "\n\n", s)
        return s.strip()

    # Signatures
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
        <EITHER list quantitative outcomes as bullets OR, if none exist anywhere in the provided TEXT, write exactly this single sentence on its own line: No quantitative metrics reported in provided text.>
        Limitations: <text or 'not reported'>
        Takeaways:
        - <bullet>
        - <bullet>
        - <bullet>
        If the text contains the word 'Table', you MUST extract at least 2 numeric entries from the nearest table region.
        If tables or metrics are present, extract numeric values exactly as written. If no numbers exist, write exactly: No quantitative metrics reported in provided text.
        NEVER guess or interpolate metrics."""
        TEXT: str = dspy.InputField(desc="The scientific paper text to extract notes from")
        NOTES: str = dspy.OutputField(desc="Structured scientific notes following the schema above, no JSON, no extra prose")

    class Summarize(dspy.Signature):
        """Produce a concise scientific summary (200-300 words) from NOTES.
        Cover in this order: Objective -> Method (what/how) -> Results (numbers if present; otherwise write exactly 'No quantitative metrics reported in provided text.')
        -> Limitations -> 3-5 Practical Takeaways (bulleted).
        Avoid speculation or citations. Do NOT invent metrics; if NOTES Results contains the exact sentence
        'No quantitative metrics reported in provided text.', then the summary Results must use that exact sentence and contain no numbers."""
        NOTES: str = dspy.InputField(desc="Structured scientific notes")
        SUMMARY: str = dspy.OutputField(desc="200-300 word summary covering objective, method, results, limitations, and takeaways")

    class Critique(dspy.Signature):
        """Critique SUMMARY against NOTES. Judge for makes sense, accuracy, coverage, and details.
        Return a rubric with scores 0-5 for each dimension, followed by improvement suggestions.
        Format:
        Makes sense: <0-5>
        Accuracy: <0-5>
        Coverage: <0-5>
        Details: <0-5>
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
        Confidence: High if all rubric scores ≥4; Medium if any score is 3; Low if any score ≤2.

        STRICT RESULTS RULE:
        - If NOTES Results contains quantitative metrics/outcomes, Results MUST include at least one (preferably two) concrete numeric outcomes with context, copied from NOTES without changing the numbers.
        - If NOTES Results contains the exact sentence 'No quantitative metrics reported in provided text.', then Results must be exactly: No quantitative metrics reported in provided text. (and contain no numbers)."""
        NOTES: str = dspy.InputField(desc="Original structured notes (ground truth)")
        SUMMARY: str = dspy.InputField(desc="Summary to integrate")
        CRITIC: str = dspy.InputField(desc="Critique feedback with rubric scores")
        META: str = dspy.OutputField(desc="Executive meta-summary with objective, method, results, limitations, takeaways, open questions, and confidence")

    # Modules
    class ReaderM(dspy.Module):
        """Reader module using declarative signature."""
        def __init__(self):
            super().__init__()
            self.gen = dspy.Predict(ReadNotes)

        def forward(self, text: str):
            out = self.gen(TEXT=text)
            return dspy.Prediction(NOTES=_sanitize(out.NOTES))

    class SummarizerM(dspy.Module):
        """Summarizer module that creates summaries from notes using declarative signatures."""
        def __init__(self):
            super().__init__()
            self.gen = dspy.Predict(Summarize)

        def forward(self, notes: str = None, NOTES: str = None):
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
            out = self.gen(NOTES=notes, SUMMARY=summary)
            return dspy.Prediction(CRITIC=_sanitize(out.CRITIC))

    class IntegratorM(dspy.Module):
        """Integrator module that creates meta-summaries using declarative signatures."""
        def __init__(self):
            super().__init__()
            self.gen = dspy.Predict(Integrate)

        def forward(self, notes: str, summary: str, critic: str):
            out = self.gen(NOTES=notes, SUMMARY=summary, CRITIC=critic)
            return dspy.Prediction(META=_sanitize(out.META))

    # Pipeline
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

    # Optional teleprompting
    def _word_f1(pred: str, gold: str) -> float:
        ps = set(w.lower() for w in re.findall(r"\w+", pred))
        gs = set(w.lower() for w in re.findall(r"\w+", gold))
        if not ps or not gs:
            return 0.0
        prec = len(ps & gs) / len(ps)
        rec = len(ps & gs) / len(gs)
        return 0.0 if (prec + rec) == 0 else (2 * prec * rec) / (prec + rec)

    def _load_devset(path: str) -> List[Dict[str, str]]:
        if not os.path.exists(path):
            return []
        examples: List[Dict[str, str]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    text = obj.get("text", "")
                    gold = obj.get("target_summary", "")
                    if text and gold:
                        examples.append({
                            "text": text,
                            "target_summary": gold,
                            "target_length": obj.get("target_length", "medium"),
                            "prompt_focus": obj.get("prompt_focus", "Results"),
                        })
                except Exception:
                    continue
        return examples

    def _teleprompt_if_requested(pipeline: PaperPipeline, cfg: Dict[str, Any]):
        """
        Optimizes DSPy pipeline using BootstrapFewShot.
        
        Instead of tuning prompts manually, we provide examples. DSPy finds
        better strategies. BootstrapFewShot tries different few-shot combinations.
        It picks the best by word F1. We only optimize summarizer as example.
        We tried optimizing all modules. Summarizer has biggest impact. Full
        optimization is too slow for interactive use.
        """
        if not cfg.get("dspy_teleprompt"):
            return
        dev_path = cfg.get("dspy_dev_path", "dev-set/dev.jsonl")
        dev = _load_devset(dev_path)
        if not dev:
            return

        def _metric(gold, pred, trace=None):
            pred_text = ""
            if hasattr(pred, "SUMMARY"):
                pred_text = str(pred.SUMMARY)
            elif isinstance(pred, dict):
                pred_text = str(pred.get("SUMMARY", ""))
            else:
                pred_text = str(pred)
            gold_text = str(gold) if gold else ""
            return _word_f1(pred_text, gold_text)

        tp = dspy.teleprompt.BootstrapFewShot(
            metric=_metric,
            max_bootstrapped_demos=3,
            max_labeled_demos=3,
        )
        trainset = []
        note_gold_pairs: List[Tuple[str, str]] = []
        target_lengths: set[str] = set()
        prompt_focuses: set[str] = set()
        for entry in dev:
            text = entry["text"]
            gold = entry["target_summary"]
            notes = pipeline.reader(text).NOTES
            trainset.append(dspy.Example(NOTES=notes, SUMMARY=gold).with_inputs("NOTES"))
            note_gold_pairs.append((notes, gold))
            target_lengths.add(entry.get("target_length") or "medium")
            prompt_focuses.add(entry.get("prompt_focus") or "Results")

        if not trainset:
            return

        def _score_module(module):
            scores = []
            for notes, gold in note_gold_pairs:
                pred = module(NOTES=notes)
                scores.append(_metric(gold, pred))
            return sum(scores) / len(scores) if scores else 0.0

        base_score = _score_module(pipeline.summarizer)
        optimized_summarizer = tp.compile(pipeline.summarizer, trainset=trainset)
        pipeline.summarizer = optimized_summarizer

        optimized_score = _score_module(pipeline.summarizer)
        gain = optimized_score - base_score
        choice = f"BootstrapFewShot(demos={len(trainset)})"

        summary_line = (
            f"Teleprompt gain {gain:+.3f} (baseline {base_score:.3f} → optimized {optimized_score:.3f}); "
            f"{len(trainset)} dev examples; lengths={sorted(target_lengths)}; focus={sorted(prompt_focuses)}."
        )

        return {
            "gain": round(gain, 3),
            "base_score": round(base_score, 3),
            "optimized_score": round(optimized_score, 3),
            "choice": choice,
            "summary": summary_line,
            "examples": len(trainset),
            "target_lengths": sorted(target_lengths),
            "prompt_focus": sorted(prompt_focuses),
        }


    # Public API
    def run_pipeline(input_text: str, cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cfg = cfg or {}
        _configure_dspy(cfg)

        pipe = PaperPipeline()
        teleprompt_info = _teleprompt_if_requested(pipe, cfg)

        t0 = perf_counter()
        out = pipe(input_text=input_text)
        t1 = perf_counter()
        metrics_count = count_numeric_results(out.NOTES)
        confidence_line = extract_confidence_line(out.META)

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
            "graph_dot": None,
            "dspy_available": True,
            "execution_trace": ["reader", "summarizer", "critic", "integrator"],
            "extracted_metrics_count": metrics_count,
            "confidence": confidence_line,
        }
        if teleprompt_info:
            result.update({
                "teleprompt_gain": teleprompt_info["gain"],
                "teleprompt_choice": teleprompt_info["choice"],
                "teleprompt_base_score": teleprompt_info["base_score"],
                "teleprompt_optimized_score": teleprompt_info["optimized_score"],
                "teleprompt_dev_examples": teleprompt_info["examples"],
                "teleprompt_target_lengths": teleprompt_info["target_lengths"],
                "teleprompt_prompt_focus": teleprompt_info["prompt_focus"],
                "teleprompt_summary": teleprompt_info["summary"],
            })
            result["meta"] = result["meta"] + "\n\n" + teleprompt_info["summary"]

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
                "extracted_metrics_count": metrics_count,
                "confidence": confidence_line,
            })
        except Exception:
            pass

        return result
