from __future__ import annotations
import re
from typing import Dict, List, Tuple, Optional

def _normalize_text(raw_text: str) -> str:
    """
    Behebt PDF-Formatierungsprobleme.
    
    PDFs sind unordentlich. Wörter über Zeilen getrennt, seltsame Abstände,
    mehrere Zeilenumbrüche. Bereinigt Text damit LLM lesbaren Text bekommt.
    
    Bindestrich-Korrektur wichtig. PDFs trennen oft Wörter wie "ex-am-ple"
    über Zeilen. Fügen sie wieder zusammen. Bereinigung mehrfacher Zeilenumbrüche
    verhindert große Lücken, die Modelle verwirren.
    """
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
    """
    Entfernt Metadaten-Header.
    
    PDFs haben oft Autorennamen, Zugehörigkeiten, E-Mails oben. Nicht nützlich
    für Analyse. Scannen erste 200 Zeilen und filtern Metadaten-Muster heraus.
    Nach Zeile 200 sind wir im eigentlichen Inhalt. Abstract, Einleitung usw.
    Alles behalten.
    
    Muster etwas heuristisch. Probierte ML-basierte Klassifikation. War übertrieben.
    Einfache Regex schneller.
    """
    if not raw_text:
        return ""
    
    text_lines = raw_text.splitlines()
    cleaned_lines: List[str] = []
    
    # Erste 200 Zeilen prüfen, Metadaten meist oben. Danach kommt Inhalt vom Paper.
    for line_index, line in enumerate(text_lines[:200]):
        stripped_line = line.strip()
        
        if not stripped_line:
            continue
        
        # Abstract behalten, aber normalisieren
        if re.fullmatch(r"(abstract|ABSTRACT)", stripped_line):
            cleaned_lines.append("Abstract")
            continue
        
        # E-Mails, ORCIDs, URLs
        if re.search(r"@|orcid\.org|https?://", stripped_line, re.I):
            continue
        
        # Keywords wie "university", "department" usw.
        if re.search(_METADATA_KEYWORDS_PATTERN, stripped_line, re.I):
            continue
        
        # GROSSBUCHSTABEN zu lang meist Header oder Zugehörigkeiten
        if stripped_line.isupper() and len(stripped_line) > 6:
            continue
        
        # Autorenname: "First Last" oder "First M. Last"
        if re.match(r"^[A-Z][a-z]+(?: [A-Z]\.)?(?: [A-Z][a-z]+)+(?:, [A-Z][a-z]+.*)*$", stripped_line):
            continue
        
        # Konferenz auch manchmal in Headern
        if re.search(r"(proceedings of|iclr|neurips|icml|acl|emnlp)\b", stripped_line, re.I):
            continue
        
        # Hat alle Filter überstanden, wahrscheinlich echter Inhalt
        cleaned_lines.append(line)
    
    # Alles nach Zeile 200 ist meist Inhalt, alles behalten
    cleaned_lines.extend(text_lines[200:])
    
    return _normalize_text("\n".join(cleaned_lines))


def strip_references_tail(raw_text: str) -> str:
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
    Bereitet Text vor für Analyse.

    Normalisiert PDF-Formatierung. Entfernt Metadaten und Referenzen.
    """
    cleaned_text = _normalize_text(raw_text or "")
    cleaned_text = strip_meta_head(cleaned_text)
    cleaned_text = strip_references_tail(cleaned_text)
    return cleaned_text


_METRIC_KEYWORDS = [
    "table", "%", "p=", "p<", "±", "≈",
    "accuracy", "f1", "rouge", "bleu", "em", "auc"
]


def _is_plausible_metric_number(number_text: str) -> bool:
    cleaned = re.sub(r"[^\d]", "", number_text or "")
    if not cleaned:
        return False
    if len(cleaned) == 4 and 1800 <= int(cleaned) <= 2100:
        return False
    return True


def detect_quantitative_signal(text: str) -> Dict[str, object]:
    """
    Erkennt, ob Text quantitative Metriken enthält.
    
    Suchen nach zwei Dingen: Metrik-Schlüsselwörtern wie "accuracy", "F1"
    und Zahlen, die wie Metriken aussehen. Prozentsätze, Dezimalzahlen,
    p-Werte. Ziel: wissen ob Paper tatsächlich Ergebnisse hat, die man
    extrahieren kann, oder ob es theoretisch ist.
    
    Gibt YES/MAYBE/NO zurück. MAYBE bedeutet Schlüsselwörter aber keine Zahlen.
    Vielleicht Tabelle nicht geparst. Oder Metriken erwähnt, aber nicht quantifiziert.
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
    
    # Jetzt nach tatsächlichen Zahlen suchen, die Metriken sein könnten
    # Muster erfasst: 87.3, 0.912, 12.4±0.3, 87.3%, p=0.03 usw.
    number_samples: List[str] = []
    number_pattern = re.compile(r"\d+(?:[.,]\d+)?(?:\s*[±≈]\s*\d+)?(?:\s*%|(?:\s*(?:p=|p<)\s*\d*[.,]?\d+))?", re.I)
    for match in number_pattern.finditer(text):
        snippet_start = max(0, match.start() - 20)
        snippet_end = min(len(text), match.end() + 20)
        snippet = text[snippet_start:snippet_end].strip()
        if _is_plausible_metric_number(match.group(0)):
            number_samples.append(snippet)
            # Nicht mehr als 6 Beispiele, wollen nur wissen ob Metriken existieren
            if len(number_samples) >= 6:
                break
    
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
    if not notes_text:
        return ""
    match = re.search(r"Results:\s*(.*?)(?:\n[A-Z][A-Za-z/ ]+:|\Z)", notes_text, flags=re.S)
    if match:
        return match.group(1).strip()
    return notes_text


def count_numeric_results(notes_text: str) -> int:
    """
    Zählt numerische Ergebnisse in Notizen.
    
    Gehen Results-Abschnitt Zeile für Zeile durch und prüfen ob jede Zeile
    quantitative Metriken enthält. Gibt grobe Anzahl wie viele Ergebnisse
    Paper hat. Nützlich für Telemetrie. Papers mit mehr Ergebnissen brauchen
    vielleicht länger zur Verarbeitung. Oder haben bessere Zusammenfassungen.
    
    Zählen nur Zeilen mit "YES"-Signal. "MAYBE" zu unsicher.
    """
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
    if not meta_text:
        return ""
    match = re.search(r"Confidence\s*:\s*([^\n]+)", meta_text, re.I)
    return match.group(0).strip() if match else ""
