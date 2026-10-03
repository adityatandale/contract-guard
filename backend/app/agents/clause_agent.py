"""Agent 2 - Clause Extractor: local LLM (Llama-3 8B / Mistral via Ollama) pulls out key clauses."""
import json
import re

from ..config import OLLAMA_MODEL, OLLAMA_URL

CLAUSE_TYPES = [
    "non_compete", "indemnification", "limitation_of_liability", "termination",
    "auto_renewal", "confidentiality", "ip_assignment", "governing_law",
    "payment", "data_protection", "other",
]

PROMPT = """You are a contract analyst. The text below is a PII-redacted contract excerpt.
Extract every important clause. Return ONLY JSON in this exact shape:
{{"clauses": [{{"type": "<one of {types}>", "text": "<verbatim clause text>", "summary": "<one plain-English sentence>"}}]}}

CONTRACT EXCERPT:
{chunk}"""

KEYWORDS = {
    "non_compete": ["non-compete", "not compete", "competing business", "restrict"],
    "indemnification": ["indemnif", "hold harmless"],
    "limitation_of_liability": ["limitation of liability", "liable", "liability"],
    "termination": ["terminat"],
    "auto_renewal": ["renew", "automatically extend"],
    "confidentiality": ["confidential", "non-disclosure"],
    "ip_assignment": ["intellectual property", "assigns all", "work product"],
    "governing_law": ["governing law", "jurisdiction", "arbitration"],
    "payment": ["fee", "payment", "invoice", "late charge"],
    "data_protection": ["personal data", "data protection", "data processing"],
}


def _chunks(text, size=3500):
    out, cur = [], ""
    for para in re.split(r"\n\s*\n", text):
        if len(cur) + len(para) > size and cur:
            out.append(cur)
            cur = ""
        cur += para + "\n\n"
    if cur.strip():
        out.append(cur)
    return out


def keyword_fallback(text):
    """Used only if Ollama is unreachable, so the demo never crashes."""
    clauses = []
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if len(para) < 40:
            continue
        low = para.lower()
        ctype = next((t for t, kws in KEYWORDS.items() if any(k in low for k in kws)), "other")
        clauses.append({"type": ctype, "text": para, "summary": para[:120] + "..."})
    return clauses


def extract_clauses(text):
    """Returns (clauses, mode) where mode is 'llm' or 'keyword-fallback'."""
    try:
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_URL, format="json", temperature=0)
        clauses = []
        for chunk in _chunks(text):
            msg = PROMPT.format(types=", ".join(CLAUSE_TYPES), chunk=chunk)
            data = json.loads(llm.invoke(msg).content)
            for c in data.get("clauses", []):
                if isinstance(c, dict) and c.get("text"):
                    c["type"] = c.get("type") if c.get("type") in CLAUSE_TYPES else "other"
                    c.setdefault("summary", "")
                    clauses.append(c)
        return clauses, "llm"
    except Exception:
        return keyword_fallback(text), "keyword-fallback"
