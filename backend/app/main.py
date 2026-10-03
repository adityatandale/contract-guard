from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .agents.pii_agent import extract_text
from .config import MAX_UPLOAD_MB
from .graph import build_graph

app = FastAPI(title="Agentic Privacy Guard & Contract Risk Auditor")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"])
graph = build_graph()

DISCLAIMER = "Automated analysis for awareness only. This is not legal advice; consult a qualified lawyer."


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze")
def analyze(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(400, "Upload a .pdf or .txt file")
    data = file.file.read()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File larger than {MAX_UPLOAD_MB} MB")
    text = extract_text(data, file.filename)
    if len(text.strip()) < 50:
        raise HTTPException(422, "No readable text found (scanned PDFs need OCR)")
    out = graph.invoke({"raw_text": text, "trace": []})
    return {
        "filename": file.filename,
        "trace": out["trace"],
        "redaction": out["redaction_report"],
        "redacted_preview": out["redacted_text"][:1500],
        "extraction_mode": out["extraction_mode"],
        "clauses": out["clauses"],
        "findings": out.get("findings", []),
        "summary": out.get("summary", {"score": 0, "level": "Low", "flagged": 0, "clauses_checked": 0}),
        "disclaimer": DISCLAIMER,
    }
