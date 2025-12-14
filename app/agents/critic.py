"""
Critic-Agent: Bewertet Zusammenfassungen gegen Original-Notizen.
"""

from __future__ import annotations
from typing import Any, Dict
from langchain_core.prompts import ChatPromptTemplate
from llm import llm

CRITIC_PROMPT = ChatPromptTemplate.from_template(
    "You are a rigorous scientific reviewer. Judge the SUMMARY only against the NOTES (the ground truth). "
    "Penalize any claim, number, dataset, metric, or conclusion not supported by NOTES.\n\n"
    "Critical checks (must apply):\n"
    "1) Title fidelity: If NOTES Title is not 'not reported', SUMMARY must include the exact same title verbatim (not paraphrased, not shortened). If SUMMARY says 'not reported' for title or uses a different title, treat as a clear error.\n"
    "2) Quantitative results presence: If NOTES Results contains quantitative metrics/outcomes (i.e., any explicit numeric result statements), SUMMARY must include at least one (preferably two) of those numeric outcomes with context. If missing, lower Specificity and state exactly what numbers to add.\n"
    "3) No fabricated numbers: If SUMMARY includes any numbers not present in NOTES Results (e.g., years, section numbers, made-up scores), lower Groundedness and call out the offending numbers.\n"
    "4) If NOTES explicitly say 'No quantitative metrics reported in provided text.', SUMMARY must NOT contain any performance numbers; Results should use that exact sentence.\n\n"
    "RUBRIC (0-5 integers):\n"
    "- Coherence: logical flow, no contradictions.\n"
    "- Groundedness: claims are supported by NOTES.\n"
    "- Coverage: objective, method, results, limitations are covered.\n"
    "- Specificity: salient details included when NOTES provide them (especially metrics if present; if metrics are missing in SUMMARY but exist in NOTES, lower the score sharply; if NOTES have no metrics, do not reward high specificity).\n\n"
    "OUTPUT FORMAT (exactly, no extra text):\n"
    "Coherence: <0-5>\n"
    "Groundedness: <0-5>\n"
    "Coverage: <0-5>\n"
    "Specificity: <0-5>\n"
    "Improvements:\n"
    "- <short fix #1>\n"
    "- <short fix #2>\n"
    "- <optional fix #3>\n\n"
    "NOTES:\n{notes}\n\nSUMMARY:\n{summary}"
)


def _clean_output_text(raw_output: str) -> str:
    """Entfernt Leerzeichen am Anfang/Ende."""
    return (raw_output or "").strip()


def run(notes: str = "", summary: str = "", *args, **kwargs) -> Dict[str, Any]:
    """Bewertet Zusammenfassung gegen Original-Notizen."""
    # Rückwärtskompatibilität
    if args and not kwargs:
        notes_text = args[0]
        summary_text = args[0]
    else:
        notes_text = kwargs.get("notes", notes) or ""
        summary_text = kwargs.get("summary", summary) or ""
    
    prompt_chain = CRITIC_PROMPT | llm
    llm_response = prompt_chain.invoke({"notes": notes_text, "summary": summary_text})
    critique_text = _clean_output_text(getattr(llm_response, "content", llm_response))
    
    return {"critic": critique_text, "critique": critique_text}
