"""
Hilfsfunktionen für Text-Verarbeitung und Abschnitts-Erkennung.
"""

from __future__ import annotations
import re
from typing import Dict, List, Tuple, Optional

# ============================================================================
# Basis-Text-Verarbeitung
# ============================================================================

def _normalize_text(raw_text: str) -> str:
    """Behebt typische PDF-Probleme: getrennte Wörter, überflüssige Leerzeichen, Leerzeilen."""
    if not raw_text:
        return ""
    
    normalized_text = raw_text
    normalized_text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", normalized_text)
    normalized_text = re.sub(r"(?<!\n)\n(?!\n)", "\n", normalized_text)
    normalized_text = re.sub(r"[ \t]+", " ", normalized_text)
    normalized_text = "\n".join([line.rstrip() for line in normalized_text.splitlines()])
    normalized_text = re.sub(r"\n{3,}", "\n\n", normalized_text)
    
    return normalized_text.strip()


def truncate_text(text: str, max_characters: Optional[int]) -> str:
    """Kürzt Text auf max_characters (None = kein Limit)."""
    if not text or not max_characters:
        return text or ""
    
    if len(text) <= max_characters:
        return text
    
    return text[:max_characters]


# ============================================================================
# Metadaten und Boilerplate entfernen
# ============================================================================

# Pattern für typische Metadaten-Keywords (Unis, Autoren, etc.)
_METADATA_KEYWORDS_PATTERN = r"(?:university|institute|faculty|department|school of|affiliation|corresponding author|preprint|arxiv|doi|copyright|acknowledg(e)?ments?)"


def strip_meta_head(raw_text: str) -> str:
    """Entfernt Metadaten am Anfang (Autoren, Affiliations, Copyright, etc.), behält aber Abstract."""
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
    """Entfernt Literaturverzeichnis am Ende (nur wenn Header nicht zu früh kommt)."""
    if not raw_text:
        return ""
    
    references_match = re.search(r"\n\s*(references|bibliography)\s*\n", raw_text, re.I)
    
    if references_match:
        characters_after_match = len(raw_text) - references_match.start()
        if characters_after_match > 800:
            return raw_text[:references_match.start()].rstrip()
    
    return raw_text


# ============================================================================
# Abschnitts-Erkennung
# ============================================================================

_SECTION_PATTERNS: List[Tuple[str, str]] = [
    ("abstract",     r"\babstract\b"),
    ("introduction", r"\b(introduction|background)\b"),
    ("methods",      r"\b(methods?|methodology|materials? and methods?)\b"),
    ("experiments",  r"\b(experiments?|experimental setup)\b"),
    ("evaluation",   r"\b(evaluation|metrics?)\b"),
    ("results",      r"\bresults?\b"),
    ("discussion",   r"\bdiscussion(s| and results)?\b"),
    ("conclusion",   r"\b(conclusion|conclusions|concluding remarks|summary)\b"),
    ("related",      r"\brelated work\b"),
    ("limitations",  r"\blimitations?\b"),
]

_NUMERIC_HEADING_PATTERN = (
    r"^\s*(?:\d+(?:\.\d+){0,2})\s+"
    r"(abstract|introduction|background|methods?|methodology|materials? and methods?|"
    r"experiments?|experimental setup|evaluation|metrics?|results?|discussion(?:s| and results)?|"
    r"conclusion|conclusions|concluding remarks|summary|related work|limitations?)\b"
)


def split_sections(text: str) -> Dict[str, str]:
    """Findet Abschnitte durch Keywords und nummerierte Überschriften. Fallback: {"body": text}."""
    if not text:
        return {}
    
    section_markers: List[Tuple[int, str]] = []
    
    for section_name, pattern in _SECTION_PATTERNS:
        for match in re.finditer(pattern, text, flags=re.I):
            section_markers.append((match.start(), section_name))
    
    for match in re.finditer(_NUMERIC_HEADING_PATTERN, text, flags=re.I | re.M):
        detected_section = match.group(1).lower()
        section_markers.append((match.start(), detected_section))
    
    section_markers.sort(key=lambda marker: marker[0])
    
    if not section_markers:
        return {"body": text}
    
    sections: Dict[str, str] = {}
    
    for marker_index, (start_position, detected_name) in enumerate(section_markers):
        if marker_index + 1 < len(section_markers):
            end_position = section_markers[marker_index + 1][0]
        else:
            end_position = len(text)
        
        section_content = text[start_position:end_position].strip()
        normalized_section_name = _normalize_section_name(detected_name)
        existing_content = sections.get(normalized_section_name, "")
        sections[normalized_section_name] = (existing_content + "\n\n" + section_content).strip()
    
    return sections


def _normalize_section_name(detected_name: str) -> str:
    """Normalisiert Abschnittsnamen (z.B. 'conclusions' zu 'conclusion', 'methodology' zu 'methods')."""
    detected_lower = detected_name.lower()
    
    if "conclusion" in detected_lower:
        return "conclusion"
    elif detected_lower.startswith("method") or "materials" in detected_lower:
        return "methods"
    elif detected_lower.startswith("result"):
        return "results"
    elif detected_lower.startswith("discussion"):
        return "discussion"
    elif detected_lower.startswith("background"):
        return "introduction"
    else:
        return detected_lower


def _select_sections(
    detected_sections: Dict[str, str],
    preferred_section_names: List[str],
    character_budget: int
) -> Tuple[str, Dict[str, int]]:
    """Wählt bevorzugte Abschnitte bis Budget voll, dann weitere nach Länge. Gibt (text, {section: chars}) zurück."""
    if not detected_sections:
        return "", {}
    
    selected_sections: List[str] = []
    remaining_budget = character_budget
    usage_statistics: Dict[str, int] = {}
    
    for preferred_section_name in preferred_section_names:
        if remaining_budget <= 0:
            break
        
        section_content = detected_sections.get(preferred_section_name, "")
        if not section_content:
            continue
        
        extracted_text = section_content[:remaining_budget]
        selected_sections.append(extracted_text)
        usage_statistics[preferred_section_name] = len(extracted_text)
        remaining_budget -= len(extracted_text)
    
    if remaining_budget > 0:
        remaining_sections = [
            (section_name, section_content)
            for section_name, section_content in detected_sections.items()
            if section_name not in preferred_section_names and section_content
        ]
        remaining_sections.sort(key=lambda item: len(item[1]), reverse=True)
        
        for section_name, section_content in remaining_sections:
            if remaining_budget <= 0:
                break
            
            extracted_text = section_content[:remaining_budget]
            selected_sections.append(extracted_text)
            usage_statistics[section_name] = len(extracted_text)
            remaining_budget -= len(extracted_text)
    
    if not selected_sections and "body" in detected_sections:
        body_text = detected_sections["body"]
        paragraphs = [
            paragraph.strip()
            for paragraph in body_text.split("\n\n")
            if len(paragraph.strip()) > 80
        ]
        
        paragraphs.sort(key=len, reverse=True)
        
        selected_paragraphs: List[str] = []
        total_characters = 0
        
        for paragraph in paragraphs:
            if total_characters + len(paragraph) > character_budget:
                break
            selected_paragraphs.append(paragraph)
            total_characters += len(paragraph)
        
        usage_statistics["body"] = total_characters
        return "\n\n".join(selected_paragraphs).strip(), usage_statistics
    
    combined_text = "\n\n".join(selected_sections).strip()
    return combined_text, usage_statistics


# ============================================================================
# Öffentliche API
# ============================================================================

def build_analysis_context(raw_text: str, config: dict) -> str:
    """
    Bereitet Text für Analyse vor: normalisiert, entfernt Metadaten/References.
    Kein automatisches Trunkieren mehr; vollständiger Text wird zurückgegeben.
    """
    cleaned_text = _normalize_text(raw_text or "")
    cleaned_text = strip_meta_head(cleaned_text)
    cleaned_text = strip_references_tail(cleaned_text)
    return cleaned_text


def preview_sections(raw_text: str, config: dict) -> Dict[str, int]:
    """Zeigt Vorschau welche Abschnitte genutzt würden: {section: chars}."""
    sections_enabled = bool(config.get("sections_enabled", True))
    section_budget = int(config.get("section_budget_chars", config.get("truncate_chars", 2400)))
    preferred_sections = config.get("sections_preferred") or [
        "abstract", "introduction", "methods", "results", "discussion", "conclusion"
    ]
    
    cleaned_text = _normalize_text(raw_text)
    cleaned_text = strip_meta_head(cleaned_text)
    cleaned_text = strip_references_tail(cleaned_text)
    
    if not sections_enabled:
        return {"body": min(len(cleaned_text), section_budget)}
    
    detected_sections = split_sections(cleaned_text)
    _, usage_statistics = _select_sections(detected_sections, preferred_sections, section_budget)
    
    return usage_statistics


# ============================================================================
# Quantitative Signal Detection & Confidence Parsing
# ============================================================================

_METRIC_KEYWORDS = [
    "table", "%", "p=", "p<", "±", "≈",
    "accuracy", "f1", "rouge", "bleu", "em", "auc"
]


def _is_plausible_metric_number(number_text: str) -> bool:
    """Heuristik: filtert offensichtliche Jahreszahlen/Seitenzahlen heraus."""
    cleaned = re.sub(r"[^\d]", "", number_text or "")
    if not cleaned:
        return False
    if len(cleaned) == 4 and 1800 <= int(cleaned) <= 2100:
        return False
    return True


def detect_quantitative_signal(text: str) -> Dict[str, object]:
    """
    Heuristisch erkennen, ob der INPUT TEXT quantitative Metriken enthalten könnte.
    
    Returns dict with:
    - signal: "YES" | "MAYBE" | "NO"
    - label: human readable label
    - keyword_hits: list of matched keywords
    - number_samples: list of numeric snippets
    """
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
    """Extrahiert den Results-Block aus Notes (beste Schätzung, fallback = kompletter Text)."""
    if not notes_text:
        return ""
    match = re.search(r"Results:\s*(.*?)(?:\n[A-Z][A-Za-z/ ]+:|\Z)", notes_text, flags=re.S)
    if match:
        return match.group(1).strip()
    return notes_text


def count_numeric_results(notes_text: str) -> int:
    """Zählt Zeilen im Results-Block, die plausible metrische Zahlen enthalten."""
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
    """Parst eine Confidence-Zeile aus der Meta Summary."""
    if not meta_text:
        return ""
    match = re.search(r"Confidence\s*:\s*([^\n]+)", meta_text, re.I)
    return match.group(0).strip() if match else ""
