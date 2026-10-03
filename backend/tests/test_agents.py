import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.agents.pii_agent import redact_regex
from app.agents.clause_agent import keyword_fallback


def test_regex_redaction_removes_pii():
    text = "Contact ravi@acme.in or +91 98765 43210. PAN ABCDE1234F, Aadhaar 1234 5678 9012."
    out, reg = redact_regex(text)
    for secret in ("ravi@acme.in", "98765", "ABCDE1234F", "1234 5678 9012"):
        assert secret not in out
    assert reg.counts["EMAIL"] == 1 and reg.counts["PAN"] == 1 and reg.counts["AADHAAR"] == 1


def test_same_value_gets_same_token():
    out, _ = redact_regex("a@x.com wrote to a@x.com")
    assert out.count("[EMAIL_1]") == 2


def test_keyword_fallback_classifies():
    text = "The Receiving Party shall indemnify and hold harmless the Disclosing Party against all losses."
    assert keyword_fallback(text)[0]["type"] == "indemnification"
