"""Agent 1 - Privacy Guard: parse the document and redact PII before any LLM sees it."""
import re

# Order matters: more specific patterns first so PHONE does not swallow them.
PATTERNS = {
    "EMAIL": r"[\w.+-]+@[\w-]+\.[\w.-]+",
    "AADHAAR": r"\b\d{4}\s\d{4}\s\d{4}\b",
    "PAN": r"\b[A-Z]{5}\d{4}[A-Z]\b",
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    "PHONE": r"(?<![\w])(?:\+\d{1,3}[\s-]?)?(?:\d{5}[\s-]?\d{5}|\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4})(?!\d)",
}

_nlp = None
_nlp_failed = False


def extract_text(data: bytes, filename: str) -> str:
    """PDF -> text with PyMuPDF; .txt -> decoded text."""
    if filename.lower().endswith(".pdf"):
        import fitz  # PyMuPDF (lazy import keeps unit tests light)
        with fitz.open(stream=data, filetype="pdf") as doc:
            return "\n\n".join(page.get_text() for page in doc)
    return data.decode("utf-8", errors="ignore")


def _get_nlp():
    global _nlp, _nlp_failed
    if _nlp is None and not _nlp_failed:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
        except Exception:
            _nlp_failed = True  # run regex-only; reported in the trace
    return _nlp


class _Registry:
    """Stable placeholders: the same value always maps to the same token."""

    def __init__(self):
        self.seen, self.counts = {}, {}

    def token(self, label, value):
        key = (label, value.lower())
        if key not in self.seen:
            self.counts[label] = self.counts.get(label, 0) + 1
            self.seen[key] = f"[{label}_{self.counts[label]}]"
        return self.seen[key]


def redact_regex(text: str, reg: _Registry = None):
    reg = reg or _Registry()
    for label, pattern in PATTERNS.items():
        text = re.sub(pattern, lambda m, l=label: reg.token(l, m.group()), text)
    return text, reg


def redact(text: str):
    """Returns (redacted_text, report). The original text is never returned."""
    text, reg = redact_regex(text)
    nlp = _get_nlp()
    if nlp is not None:
        doc = nlp(text)
        for ent in reversed(doc.ents):
            if ent.label_ == "PERSON":
                text = text[: ent.start_char] + reg.token("PERSON", ent.text) + text[ent.end_char:]
    report = {"counts": reg.counts, "total": sum(reg.counts.values()), "ner_used": nlp is not None}
    return text, report
