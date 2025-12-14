"""
Reader-Agent: Extrahiert strukturierte Notizen aus Papern.
"""

from __future__ import annotations
from langchain_core.prompts import ChatPromptTemplate
from llm import llm

READER_PROMPT = ChatPromptTemplate.from_template(
    "You are a precise scientific note-taker. Work ONLY with the TEXT below. "
    "If an item is not explicitly stated, write 'not reported'. "
    "Do NOT invent facts. Do NOT include author names, emails, or affiliations.\n\n"
    "Return notes in EXACTLY this Markdown schema (keep the headings as written):\n\n"
    "Title: <paper title or 'not reported'>\n"
    "Objective: <1-2 sentences>\n"
    "Methods:\n"
    "- <technique/model>\n"
    "- <training/eval setup>\n"
    "- <tooling/frameworks>\n"
    "Datasets/Corpora: <names or 'not reported'>\n"
    "Results (key numbers if present):\n"
    "- <metric: value on dataset>\n"
    "- <ablation/comparison>\n"
    "Metrics (BLEU/F1/Acc/etc):\n"
    "- <metric: value>\n"
    "- <metric: value>\n"
    "Contributions:\n"
    "- <main contribution>\n"
    "- <secondary>\n"
    "Limitations: <short phrase or 'not reported'>\n"
    "Applications/Use-cases: <short phrase or 'not reported'>\n"
    "Notes:\n"
    "- <any other salient detail>\n\n"
    "If tables are present (e.g., BLEU-1/2/3/4), extract the numeric values. If no numbers exist, write 'not reported'.\n"
    "NEVER guess or interpolate metrics. If you cannot find explicit numbers, set metrics to 'not reported'.\n"
    "TEXT:\n{content}"
)


def _clean_output_text(raw_output: str) -> str:
    """Entfernt Leerzeichen am Anfang/Ende."""
    return (raw_output or "").strip()


def run(input_text: str) -> str:
    """Extrahiert strukturierte Notizen aus Paper-Text."""
    prompt_chain = READER_PROMPT | llm
    llm_response = prompt_chain.invoke({"content": input_text})
    output_text = getattr(llm_response, "content", llm_response)
    return _clean_output_text(output_text)
