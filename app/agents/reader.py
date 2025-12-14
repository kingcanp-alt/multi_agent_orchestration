"""
Reader Agent: Extracts notes from papers.
"""

from __future__ import annotations
from langchain_core.prompts import ChatPromptTemplate
from llm import llm

READER_PROMPT = ChatPromptTemplate.from_template(
    "You are a careful scientific note-taker. Work only with TEXT below. "
    "Do not invent facts. Do not include author info. "
    "If a field is missing in TEXT, write 'not reported'. Do not guess.\n\n"
    "Return notes in this Markdown schema:\n\n"
    "Title: <copy exactly from TEXT. If multi-line, join with spaces. Use 'not reported' only if no title exists>\n"
    "Objective: <1-2 sentences or 'not reported'>\n"
    "Methods: <technique/model, training/eval setup, tooling/frameworks, or 'not reported'>\n"
    "Datasets/Corpora: <names or 'not reported'>\n"
    "Results:\n"
    "<EITHER list quantitative outcomes as bullets OR write exactly: No quantitative metrics reported in provided text.>\n"
    "Metrics (BLEU/F1/Acc/etc): <list only metric names from TEXT, or 'not reported'. Do not include values.>\n"
    "Contributions: <main contribution, secondary, or 'not reported'>\n"
    "Limitations: <short phrase or 'not reported'>\n"
    "Applications/Use-cases: <short phrase or 'not reported'>\n"
    "Notes: <any other important detail or 'not reported'>\n\n"
    "STRICT RULES:\n\n"
    "Title:\n"
    "- Copy title exactly from TEXT. Do not shorten. Do not change.\n"
    "- Title is usually near beginning. Scan first ~80 lines.\n"
    "- Multi-line title: join lines with single spaces. Keep punctuation as shown.\n"
    "- Do not mistake 'Abstract' or 'Introduction' as title.\n"
    "- Use 'not reported' only if no reasonable title exists.\n\n"
    "Results:\n"
    "- Check if TEXT contains quantitative metrics. Look for tables, scores, percentages, p-values, ROUGE, BLEU, F1, Acc, EM, AUC.\n"
    "- If 'Table' is present, extract at least 2 numeric entries.\n"
    "- If metrics exist, extract at least TWO results. Use this pattern: <Task/Dataset>: <Metric>=<Value>. Include Model/Split/Baseline if present.\n"
    "- Examples: 87.3%, 0.912, 12.4±0.3, p=0.03, p<0.05.\n"
    "- Prefer evaluation outcomes. Do not treat years as Results. Do not treat section numbers as Results. Do not treat page numbers as Results.\n"
    "- Use values exactly as written. Never compute. Never round. Never guess missing values.\n"
    "- If tables are present, include context. Include model/system. Include dataset/task. Include metric name. Include split.\n"
    "- If only one result is present, extract it. Also extract next-best outcome. Next-best could be baseline comparison, comparison test, another metric, or p-value.\n"
    "- If no metrics exist, write exactly: No quantitative metrics reported in provided text.\n\n"
    "TEXT:\n{content}"
)


def _clean_output_text(raw_output: str) -> str:
    """Removes leading/trailing whitespace."""
    return (raw_output or "").strip()


def run(input_text: str) -> str:
    """Extracts structured notes from paper text."""
    prompt_chain = READER_PROMPT | llm
    llm_response = prompt_chain.invoke({"content": input_text})
    output_text = getattr(llm_response, "content", llm_response)
    return _clean_output_text(output_text)
