"""
Summarizer-Agent: Erstellt Zusammenfassung aus strukturierten Notizen.
"""

from __future__ import annotations
from langchain_core.prompts import ChatPromptTemplate
from llm import llm

SUMMARIZER_PROMPT = ChatPromptTemplate.from_template(
    "Produce a concise scientific summary (200-300 words) of the paper described in the NOTES. "
    "Cover, in this order: Objective -> Method (what/how) -> Results (numbers if present; otherwise say 'not reported') "
    "-> Limitations -> 3-5 Practical Takeaways (bulleted). "
    "Avoid speculation or citations. Do NOT invent metrics; if NOTES have no numbers, write 'not reported'.\n\n"
    "NOTES:\n{notes}"
)


def _clean_output_text(raw_output: str) -> str:
    """Entfernt Leerzeichen am Anfang/Ende."""
    return (raw_output or "").strip()


def run(structured_notes: str) -> str:
    """Erstellt Zusammenfassung aus strukturierten Notizen."""
    prompt_chain = SUMMARIZER_PROMPT | llm
    llm_response = prompt_chain.invoke({"notes": structured_notes})
    output_text = getattr(llm_response, "content", llm_response)
    return _clean_output_text(output_text)
