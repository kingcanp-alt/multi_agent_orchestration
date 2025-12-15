from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from llm import llm

SUMMARIZER_PROMPT = ChatPromptTemplate.from_template(
    "Produce a concise scientific summary from NOTES. Do not invent facts. Do not include citations.\n\n"
    "Output format:\n"
    "Title: <copy exactly from NOTES Title. If 'not reported', write 'not reported'>\n"
    "Objective: <1-2 sentences or 'not reported'>\n"
    "Method: <brief: what/how or 'not reported'>\n"
    "Results: <include numeric outcomes only if present in NOTES Results; otherwise write exactly 'No quantitative metrics reported in provided text.'>\n"
    "Limitations: <brief or 'not reported'>\n"
    "Practical Takeaways:\n"
    "- <bullet or 'not reported'>\n"
    "- <bullet or 'not reported'>\n"
    "- <bullet or 'not reported'>\n\n"
    "STRICT RULES:\n\n"
    "Results:\n"
    "- Include numeric outcomes only if present in NOTES Results. Otherwise write exactly 'No quantitative metrics reported in provided text.'\n"
    "- Never infer numbers. Never guess numbers. Never add numbers that are not in NOTES Results.\n"
    "- If NOTES Results contains metrics, copy them exactly. Keep values exactly as they are.\n"
    "- Do not add other numbers. Do not add years. Do not add section numbers. Do not add paper IDs. Do not add counts. Do not add hyperparameters.\n\n"
    "NOTES:\n{notes}"
)


def _clean_output_text(raw_output: str) -> str:
    return (raw_output or "").strip()


def run(structured_notes: str) -> str:
    prompt_chain = SUMMARIZER_PROMPT | llm
    llm_response = prompt_chain.invoke({"notes": structured_notes})
    output_text = getattr(llm_response, "content", llm_response)
    return _clean_output_text(output_text)
