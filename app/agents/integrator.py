"""
Integrator-Agent: Erstellt finale Meta-Zusammenfassung aus allen vorherigen Schritten.
"""

from __future__ import annotations
from langchain_core.prompts import ChatPromptTemplate
from llm import llm

INTEGRATOR_PROMPT = ChatPromptTemplate.from_template(
    "Create an executive Meta Summary by fusing SUMMARY with the reviewer signal (CRITIC), grounded strictly in NOTES. "
    "Do not invent facts, metrics, numbers, or citations.\n\n"
    "Start with a Title line:\n"
    "Title: <copy verbatim from NOTES Title; if NOTES Title is 'not reported', write 'not reported'>\n\n"
    "Then output:\n"
    "1) Five bullets with **bold labels**: Objective, Method, Results, Limitations, Takeaways\n"
    "2) Two open technical questions\n"
    "3) A one-line Confidence (High/Medium/Low) based on rubric: High if all ≥4; Medium if any 3; Low if any ≤2. Mention missing/weak numeric evidence if relevant. "
    "Confidence MUST be formatted exactly as: Confidence: <High/Medium/Low> - <one short reason>.\n\n"
    "STRICT RESULTS RULE:\n"
    "- If NOTES Results contains quantitative metrics/outcomes, Results MUST include at least one (preferably two) concrete numeric outcomes with context, copied from NOTES (or SUMMARY if it matches NOTES) without changing the numbers.\n"
    "- If NOTES Results contains the exact sentence 'No quantitative metrics reported in provided text.', then write Results: No quantitative metrics reported in provided text. and do not include any performance numbers anywhere in the Meta Summary.\n"
    "- Do not add years, section numbers, paper IDs, or other irrelevant numbers.\n\n"
    "NOTES:\n{notes}\n\nSUMMARY:\n{summary}\n\nCRITIC:\n{critic}"
)


def _clean_output_text(raw_output: str) -> str:
    """Entfernt Leerzeichen am Anfang/Ende."""
    return (raw_output or "").strip()


def run(notes: str = "", summary: str = "", critic: str = "", *args, **kwargs) -> str:
    """Erstellt finale Meta-Zusammenfassung aus Notizen, Summary und Critic."""
    # Rückwärtskompatibilität
    if args and not kwargs:
        notes_text = args[0]
        summary_text = args[0]
        critic_text = args[1] if len(args) > 1 else ""
    else:
        notes_text = kwargs.get("notes", notes) or ""
        summary_text = kwargs.get("summary", summary) or ""
        critic_text = kwargs.get("critic", critic) or ""
    
    prompt_chain = INTEGRATOR_PROMPT | llm
    llm_response = prompt_chain.invoke({"notes": notes_text, "summary": summary_text, "critic": critic_text})
    output_text = getattr(llm_response, "content", llm_response)
    return _clean_output_text(output_text)
