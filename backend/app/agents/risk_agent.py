"""Agent 3 - Risk Auditor: cross-reference clauses with a legal-risk vector DB (ChromaDB)."""
import json
from pathlib import Path

import chromadb

from ..config import CHROMA_DIR, RISK_DISTANCE

PLAYBOOK = Path(__file__).resolve().parent.parent / "data" / "risk_playbook.json"
WEIGHT = {"high": 3, "medium": 2, "low": 1}
_collection = None


def get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        col = client.get_or_create_collection("risk_playbook", metadata={"hnsw:space": "cosine"})
        if col.count() == 0:
            entries = json.loads(PLAYBOOK.read_text())
            col.add(
                ids=[e["id"] for e in entries],
                documents=[e["pattern"] for e in entries],
                metadatas=[{k: e[k] for k in ("title", "severity", "explanation", "recommendation")} for e in entries],
            )
        _collection = col
    return _collection


def assess(clauses):
    col = get_collection()
    findings, seen = [], set()
    for c in clauses:
        res = col.query(query_texts=[c["text"][:2000]], n_results=1)
        if not res["ids"][0]:
            continue
        dist, meta, rid = res["distances"][0][0], res["metadatas"][0][0], res["ids"][0][0]
        if dist <= RISK_DISTANCE:
            findings.append({
                "clause_type": c["type"],
                "clause_text": c["text"],
                "title": meta["title"],
                "severity": meta["severity"],
                "similarity": round((1 - dist) * 100),
                "explanation": meta["explanation"],
                "recommendation": meta["recommendation"],
            })
            seen.add(rid)
    findings.sort(key=lambda f: (-WEIGHT[f["severity"]], -f["similarity"]))
    score = min(100, sum(WEIGHT[f["severity"]] * 10 for f in findings))
    level = "High" if score >= 60 else "Medium" if score >= 30 else "Low"
    return findings, {"score": score, "level": level, "flagged": len(findings), "clauses_checked": len(clauses)}
