"""LangGraph multi-agent workflow:
   privacy_guard -> clause_extractor -> (has clauses?) -> risk_auditor -> END
"""
from typing import TypedDict

from langgraph.graph import END, StateGraph

from .agents import clause_agent, pii_agent, risk_agent


class State(TypedDict, total=False):
    raw_text: str
    redacted_text: str
    redaction_report: dict
    clauses: list
    extraction_mode: str
    findings: list
    summary: dict
    trace: list


def privacy_guard(state: State):
    text, report = pii_agent.redact(state["raw_text"])
    step = f"Agent 1 (Privacy Guard): redacted {report['total']} PII items (spaCy NER: {'on' if report['ner_used'] else 'off - regex only'})"
    # raw_text is dropped from state so later agents can never see it
    return {"redacted_text": text, "redaction_report": report, "raw_text": "", "trace": state.get("trace", []) + [step]}


def clause_extractor(state: State):
    clauses, mode = clause_agent.extract_clauses(state["redacted_text"])
    step = f"Agent 2 (Clause Extractor): found {len(clauses)} clauses via {mode}"
    return {"clauses": clauses, "extraction_mode": mode, "trace": state["trace"] + [step]}


def risk_auditor(state: State):
    findings, summary = risk_agent.assess(state["clauses"])
    step = f"Agent 3 (Risk Auditor): flagged {summary['flagged']} risky clauses, overall risk {summary['level']}"
    return {"findings": findings, "summary": summary, "trace": state["trace"] + [step]}


def route(state: State):
    return "risk_auditor" if state["clauses"] else END


def build_graph():
    g = StateGraph(State)
    g.add_node("privacy_guard", privacy_guard)
    g.add_node("clause_extractor", clause_extractor)
    g.add_node("risk_auditor", risk_auditor)
    g.set_entry_point("privacy_guard")
    g.add_edge("privacy_guard", "clause_extractor")
    g.add_conditional_edges("clause_extractor", route, {"risk_auditor": "risk_auditor", END: END})
    g.add_edge("risk_auditor", END)
    return g.compile()
