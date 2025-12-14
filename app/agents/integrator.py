"""
Integrator Agent: Creates final meta-summary from all previous steps.
"""

from __future__ import annotations
from langchain_core.prompts import ChatPromptTemplate
from llm import llm

INTEGRATOR_PROMPT = ChatPromptTemplate.from_template(
    "Create a final Meta Summary. Combine SUMMARY with CRITIC. Base everything on NOTES. "
    "Do not invent facts. Do not invent metrics. Do not invent numbers. Do not invent citations.\n\n"
    "Start with Title:\n"
    "Title: <copy exactly from NOTES Title. If 'not reported', write 'not reported'>\n\n"
    "Then output:\n"
    "1) Five bullets with **bold labels**: Objective, Method, Results, Limitations, Takeaways\n"
    "2) Two open technical questions\n"
    "3) One-line Confidence. Use High if all scores ≥4. Use Medium if any score is 3. Use Low if any score is ≤2. Mention missing/weak numeric evidence if relevant.\n"
    "Format: Confidence: <High/Medium/Low> - <one short reason>.\n\n"
    "STRICT RULES:\n\n"
    "Results:\n"
    "- Check if NOTES Results contains quantitative metrics. If it does, include numeric outcomes from NOTES. Include context. Copy from NOTES. Or copy from SUMMARY if it matches NOTES. Do not change numbers.\n"
    "- If NOTES Results says 'No quantitative metrics reported in provided text.', write that exact sentence. Do not include any performance numbers.\n"
    "- If CRITIC flags unsupported numbers or claims, remove them or mark as 'not reported'. Do not keep claims that CRITIC says are not in NOTES.\n"
    "- Do not add years. Do not add section numbers. Do not add paper IDs. Do not add other irrelevant numbers.\n\n"
    "NOTES:\n{notes}\n\nSUMMARY:\n{summary}\n\nCRITIC:\n{critic}"
)


def _clean_output_text(raw_output: str) -> str:
    """Removes leading/trailing whitespace."""
    return (raw_output or "").strip()


def run(notes: str = "", summary: str = "", critic: str = "", *args, **kwargs) -> str:
    """Creates final meta-summary from notes, summary, and critic."""
    # Backward compatibility
    if args and not kwargs:
        notes_text = args[0]
        summary_text = args[1] if len(args) > 1 else ""
        critic_text = args[2] if len(args) > 2 else ""
    else:
        notes_text = kwargs.get("notes", notes) or ""
        summary_text = kwargs.get("summary", summary) or ""
        critic_text = kwargs.get("critic", critic) or ""
    
    prompt_chain = INTEGRATOR_PROMPT | llm
    llm_response = prompt_chain.invoke({"notes": notes_text, "summary": summary_text, "critic": critic_text})
    output_text = getattr(llm_response, "content", llm_response)
    return _clean_output_text(output_text)
