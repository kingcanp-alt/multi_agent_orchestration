"""
Summarizer-Agent: Erstellt Zusammenfassung aus strukturierten Notizen.
"""

from __future__ import annotations
from langchain_core.prompts import ChatPromptTemplate
from llm import llm

SUMMARIZER_PROMPT = ChatPromptTemplate.from_template(
    "Produce a concise scientific summary of the paper described in the NOTES, grounded strictly in the NOTES. "
    "Do NOT invent facts, numbers, datasets, or metrics. Do NOT include citations.\n\n"
    "Output format (use these labels in this order):\n"
    "Title: <copy verbatim from NOTES Title; if NOTES Title is 'not reported', write 'not reported'>\n"
    "Objective: <1-2 sentences>\n"
    "Method: <brief: what/how>\n"
    "Results: <EITHER include at least one (preferably two) concrete numeric outcomes copied from NOTES Results with context OR write exactly 'No quantitative metrics reported in provided text.'>\n"
    "Limitations: <brief>\n"
    "Practical Takeaways:\n"
    "- <bullet>\n"
    "- <bullet>\n"
    "- <bullet>\n\n"
    "STRICT RESULTS RULE:\n"
    "- Only include numbers in the SUMMARY if (and only if) the NOTES section 'Results' contains explicit quantitative metrics/outcomes.\n"
    "- If NOTES Results contains the exact sentence 'No quantitative metrics reported in provided text.', then write Results: No quantitative metrics reported in provided text. and do not include any numbers anywhere in the summary.\n"
    "- When including numbers, copy at least one (preferably two) Results bullets verbatim (numbers and metric names), preserving the values exactly; do not add any other numbers (avoid years, section numbers, paper IDs, counts, or hyperparameters).\n\n"
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
