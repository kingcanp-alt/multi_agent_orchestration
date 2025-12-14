"""
Critic-Agent: Bewertet Zusammenfassungen gegen Original-Notizen.
"""

from __future__ import annotations
from typing import Any, Dict
from langchain_core.prompts import ChatPromptTemplate
from llm import llm

CRITIC_PROMPT = ChatPromptTemplate.from_template(
    "You are a rigorous scientific reviewer. Judge the SUMMARY only against the NOTES (the ground truth). "
    "Penalize any claim not supported by NOTES.\n\n"
    "RUBRIC (0-5 integers):\n"
    "- Coherence: logical flow, no contradictions.\n"
    "- Groundedness: claims are supported by NOTES.\n"
    "- Coverage: objective, method, results, limitations are covered.\n"
    "- Specificity: salient details included when NOTES provide them (especially metrics if present; if metrics are missing in SUMMARY but exist in NOTES, lower the score; if NOTES have no metrics, do not reward high specificity).\n\n"
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
