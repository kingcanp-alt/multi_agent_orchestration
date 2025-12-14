"""
Reader-Agent: Extrahiert strukturierte Notizen aus Papern.
"""

from __future__ import annotations
from langchain_core.prompts import ChatPromptTemplate
from llm import llm

READER_PROMPT = ChatPromptTemplate.from_template(
    "You are a precise scientific note-taker for arbitrary scientific PDFs. Work ONLY with the TEXT below. "
    "Do NOT invent facts. Do NOT paraphrase. Do NOT include author names, emails, or affiliations.\n\n"
    "Return notes in EXACTLY this Markdown schema (keep headings and punctuation exactly as written):\n\n"
    "Title: <paper title copied verbatim from the TEXT; if the title spans multiple lines, join those lines with single spaces while preserving exact characters/case/punctuation; use 'not reported' ONLY if no title exists anywhere in the provided TEXT>\n"
    "Objective: <1-2 sentences or 'not reported'>\n"
    "Methods:\n"
    "- <technique/model>\n"
    "- <training/eval setup>\n"
    "- <tooling/frameworks>\n"
    "Datasets/Corpora: <names or 'not reported'>\n"
    "Results:\n"
    "<EITHER list quantitative outcomes as bullets OR, if none exist anywhere in the provided TEXT, write exactly this single sentence on its own line: No quantitative metrics reported in provided text.>\n"
    "Metrics (BLEU/F1/Acc/etc): List ONLY metric names explicitly mentioned in the TEXT (no values).\n"
    "Contributions:\n"
    "- <main contribution>\n"
    "- <secondary>\n"
    "Limitations: <short phrase or 'not reported'>\n"
    "Applications/Use-cases: <short phrase or 'not reported'>\n"
    "Notes:\n"
    "- <any other salient detail>\n\n"
    "TITLE RULES (strict):\n"
    "- The Title must be copied verbatim from the provided TEXT (no shortening, no normalization).\n"
    "- The title is usually near the beginning; scan at least the first ~80 lines and also any explicit 'Title' field if present.\n"
    "- Multi-line title: identify the contiguous title block (often 1-3 consecutive lines) and join lines with single spaces; keep hyphenation and punctuation exactly as shown.\n"
    "- Do not mistake section headings like 'Abstract', 'Introduction', 'Contents', or venue/arXiv/footer lines as the title.\n"
    "- Output 'not reported' ONLY if you cannot find any plausible paper title anywhere in the provided TEXT.\n\n"
    "QUANTITATIVE RESULTS RULES (strict):\n"
    "- First decide whether the provided TEXT contains ANY quantitative performance/result metrics at all (tables, scores, percentages, p-values, confidence intervals, ROUGE/BLEU/F1/Acc/EM/AUC, etc.).\n"
    "- If the text contains the word 'Table', you MUST extract at least 2 numeric entries from the nearest table region.\n"
    "- If YES, you MUST extract at least TWO concrete numeric results into Results with context, in this exact pattern:\n"
    "  - <Task/Dataset>: <Metric>=<Value> (Model/Split/Baseline/Setup if present)\n"
    "  Examples of acceptable values: 87.3%, 0.912, 12.4±0.3, p=0.03, p<0.05.\n"
    "- Prefer true evaluation outcomes over irrelevant numbers. Do NOT treat years, section numbers, citation indices, page numbers, or parameter counts as 'Results' unless they are explicitly presented as an outcome/metric.\n"
    "- Use the numeric values exactly as written in the TEXT; never compute, round, average, or infer missing values.\n"
    "- If tables are present, pull numeric entries with their row/column context (model/system, dataset/task, metric name, split like dev/test).\n"
    "- If only one result is clearly present, still extract it and then extract the next-best quantitative outcome (e.g., a baseline vs. method, ablation, another metric, or a p-value) so that Results contains at least two items.\n"
    "- If NO quantitative metrics exist anywhere in the provided TEXT, then under Results write exactly: No quantitative metrics reported in provided text. (and do not list any numbers in Results).\n\n"
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
