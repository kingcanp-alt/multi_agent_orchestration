"""
Helper for text processing.
"""

from __future__ import annotations
import re
from typing import Dict, List, Tuple, Optional

def _normalize_text(raw_text: str) -> str:
    """Fix PDF formatting issues."""
    if not raw_text:
        return ""
    
    normalized_text = raw_text
    normalized_text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", normalized_text)
    normalized_text = re.sub(r"(?<!\n)\n(?!\n)", "\n", normalized_text)
    normalized_text = re.sub(r"[ \t]+", " ", normalized_text)
    normalized_text = "\n".join([line.rstrip() for line in normalized_text.splitlines()])
    normalized_text = re.sub(r"\n{3,}", "\n\n", normalized_text)
    
    return normalized_text.strip()


# Remove metadata and boilerplate

_METADATA_KEYWORDS_PATTERN = r"(?:university|institute|faculty|department|school of|affiliation|corresponding author|preprint|arxiv|doi|copyright|acknowledg(e)?ments?)"


def strip_meta_head(raw_text: str) -> str:
    """Drop metadata header."""
    if not raw_text:
        return ""
    
    text_lines = raw_text.splitlines()
    cleaned_lines: List[str] = []
    
    for line_index, line in enumerate(text_lines[:200]):
        stripped_line = line.strip()
        
        if not stripped_line:
            continue
        
        if re.fullmatch(r"(abstract|ABSTRACT)", stripped_line):
            cleaned_lines.append("Abstract")
            continue
        
        if re.search(r"@|orcid\.org|https?://", stripped_line, re.I):
            continue
        
        if re.search(_METADATA_KEYWORDS_PATTERN, stripped_line, re.I):
            continue
        
        if stripped_line.isupper() and len(stripped_line) > 6:
            continue
        
        if re.match(r"^[A-Z][a-z]+(?: [A-Z]\.)?(?: [A-Z][a-z]+)+(?:, [A-Z][a-z]+.*)*$", stripped_line):
            continue
        
        if re.search(r"(proceedings of|iclr|neurips|icml|acl|emnlp)\b", stripped_line, re.I):
            continue
        
        cleaned_lines.append(line)
    
    cleaned_lines.extend(text_lines[200:])
    
    return _normalize_text("\n".join(cleaned_lines))


def strip_references_tail(raw_text: str) -> str:
    """Drop bibliography section."""
    if not raw_text:
        return ""
    
    references_match = re.search(r"\n\s*(references|bibliography)\s*\n", raw_text, re.I)
    
    if references_match:
        characters_after_match = len(raw_text) - references_match.start()
        if characters_after_match > 800:
            return raw_text[:references_match.start()].rstrip()
    
    return raw_text


# Public API

def build_analysis_context(raw_text: str, config: dict) -> str:
    """
    Prepare text for analysis.

    Normalize PDF formatting. Drop metadata and references.
    """
    cleaned_text = _normalize_text(raw_text or "")
    cleaned_text = strip_meta_head(cleaned_text)
    cleaned_text = strip_references_tail(cleaned_text)
    return cleaned_text


# Quantitative signal detection and confidence parsing

_METRIC_KEYWORDS = [
    "table", "%", "p=", "p<", "±", "≈",
    "accuracy", "f1", "rouge", "bleu", "em", "auc"
]


def _is_plausible_metric_number(number_text: str) -> bool:
    """Filter out obvious years or page numbers."""
    cleaned = re.sub(r"[^\d]", "", number_text or "")
    if not cleaned:
        return False
    if len(cleaned) == 4 and 1800 <= int(cleaned) <= 2100:
        return False
    return True


def detect_quantitative_signal(text: str) -> Dict[str, object]:
    """Detects if text contains quantitative metrics."""
    if not text or not text.strip():
        return {"signal": "NO", "label": "NO (no quantitative signal detected)", "keyword_hits": [], "number_samples": []}
    
    lowered = text.lower()
    keyword_hits: List[str] = []
    for kw in _METRIC_KEYWORDS:
        if kw == "%":
            if "%" in text:
                keyword_hits.append("%")
        elif re.search(re.escape(kw), lowered):
            keyword_hits.append(kw)
    
    number_samples: List[str] = []
    number_pattern = re.compile(r"\d+(?:[.,]\d+)?(?:\s*[±≈]\s*\d+)?(?:\s*%|(?:\s*(?:p=|p<)\s*\d*[.,]?\d+))?", re.I)
    for match in number_pattern.finditer(text):
        snippet_start = max(0, match.start() - 20)
        snippet_end = min(len(text), match.end() + 20)
        snippet = text[snippet_start:snippet_end].strip()
        if _is_plausible_metric_number(match.group(0)):
            number_samples.append(snippet)
            if len(number_samples) >= 6:
                break
    
    # Additional check: numbers near metric keywords within a short window
    context_hits = 0
    for sample in number_samples:
        if re.search(r"(accuracy|f1|rouge|bleu|em|auc|precision|recall|score|table)", sample, re.I):
            context_hits += 1
    
    if number_samples or context_hits:
        label = "YES (numbers detected)"
        signal = "YES"
    elif keyword_hits:
        label = "MAYBE (tables/metric keywords detected)"
        signal = "MAYBE"
    else:
        label = "NO (no quantitative signal detected)"
        signal = "NO"
    
    return {
        "signal": signal,
        "label": label,
        "keyword_hits": keyword_hits,
        "number_samples": number_samples,
    }


def _extract_results_block(notes_text: str) -> str:
    """Extracts Results block from notes."""
    if not notes_text:
        return ""
    match = re.search(r"Results:\s*(.*?)(?:\n[A-Z][A-Za-z/ ]+:|\Z)", notes_text, flags=re.S)
    if match:
        return match.group(1).strip()
    return notes_text


def count_numeric_results(notes_text: str) -> int:
    """Counts numeric results in notes."""
    results_block = _extract_results_block(notes_text)
    if not results_block:
        return 0
    count = 0
    for line in results_block.splitlines():
        if not line.strip():
            continue
        info = detect_quantitative_signal(line)
        if info.get("signal") == "YES":
            count += 1
    return count


def extract_confidence_line(meta_text: str) -> str:
    """Extracts confidence line from meta summary."""
    if not meta_text:
        return ""
    match = re.search(r"Confidence\s*:\s*([^\n]+)", meta_text, re.I)
    return match.group(0).strip() if match else ""
