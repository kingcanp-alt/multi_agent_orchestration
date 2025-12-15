from __future__ import annotations

from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate

from llm import llm

CRITIC_PROMPT = ChatPromptTemplate.from_template(
    "You are a careful scientific reviewer. Judge SUMMARY against NOTES. "
    "Mark as wrong any claim not supported by NOTES. Mark as wrong any number not supported by NOTES. Mark as wrong any dataset not supported by NOTES. Mark as wrong any metric not supported by NOTES. Mark as wrong any conclusion not supported by NOTES.\n\n"
    "STRICT RULES:\n\n"
    "1) Title: Check if NOTES Title is 'not reported'. If it is not 'not reported', SUMMARY must include exact same title. If title is different, treat as error.\n"
    "2) Quantitative results: Check if NOTES Results contains metrics. If it does, SUMMARY should include numeric outcomes from NOTES. If NOTES has no metrics, SUMMARY must not contain performance numbers. If missing expected numbers, lower Details score. State what numbers to add. Quote the exact part of NOTES that supports or contradicts.\n"
    "3) No made-up numbers: Check if SUMMARY includes numbers not in NOTES Results. Examples: years, section numbers, invented scores. If found, lower Accuracy score. Quote the exact missing or contradicting part of NOTES, or state 'not found in NOTES'.\n"
    "4) If NOTES says 'No quantitative metrics reported in provided text.', SUMMARY must not contain performance numbers. Results should use that exact sentence.\n\n"
    "SCORING (0-5 integers):\n"
    "- Makes sense: logical flow, no contradictions.\n"
    "- Accuracy: claims supported by NOTES.\n"
    "- Coverage: objective covered, method covered, results covered, limitations covered.\n"
    "- Details: important details included. If metrics missing in SUMMARY but exist in NOTES, lower score sharply. If NOTES have no metrics, do not reward high details score.\n\n"
    "OUTPUT FORMAT:\n"
    "Makes sense: <0-5>\n"
    "Accuracy: <0-5>\n"
    "Coverage: <0-5>\n"
    "Details: <0-5>\n"
    "Improvements:\n"
    "- <short fix #1>\n"
    "- <short fix #2>\n"
    "- <optional fix #3>\n\n"
    "NOTES:\n{notes}\n\nSUMMARY:\n{summary}"
)


def _clean_output_text(raw_output: str) -> str:
    """Removes leading/trailing whitespace."""
    return (raw_output or "").strip()


def run(notes: str = "", summary: str = "", *args, **kwargs) -> Dict[str, Any]:
    if args and not kwargs:
        notes_text = args[0]
        summary_text = args[1] if len(args) > 1 else ""
    else:
        notes_text = kwargs.get("notes", notes) or ""
        summary_text = kwargs.get("summary", summary) or ""
    
    prompt_chain = CRITIC_PROMPT | llm
    llm_response = prompt_chain.invoke({"notes": notes_text, "summary": summary_text})
    critique_text = _clean_output_text(getattr(llm_response, "content", llm_response))
    
    return {"critic": critique_text, "critique": critique_text}
