"use client";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const COLORS = { high: "#d32f2f", medium: "#ed8a00", low: "#2e7d32" };
const card = { background: "#fff", borderRadius: 10, padding: 16, marginTop: 16, boxShadow: "0 1px 3px #0002" };

export default function Home() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function analyze() {
    if (!file) return;
    setLoading(true); setError(""); setResult(null);
    try {
      const body = new FormData();
      body.append("file", file);
      const res = await fetch(`${API}/api/analyze`, { method: "POST", body });
      if (!res.ok) throw new Error((await res.json()).detail || "Request failed");
      setResult(await res.json());
    } catch (e) { setError(e.message); }
    setLoading(false);
  }

  return (
    <main style={{ maxWidth: 860, margin: "0 auto", padding: 24 }}>
      <h1>Agentic Privacy Guard & Contract Risk Auditor</h1>
      <p>Upload an NDA / SaaS agreement (PDF or TXT). PII is redacted first, then analysed by local AI agents.</p>
      <div style={card}>
        <input type="file" accept=".pdf,.txt" onChange={(e) => setFile(e.target.files[0])} />
        <button onClick={analyze} disabled={!file || loading} style={{ marginLeft: 12, padding: "8px 16px" }}>
          {loading ? "Analysing..." : "Analyse contract"}
        </button>
        {error && <p style={{ color: "#d32f2f" }}>{error}</p>}
      </div>

      {result && (<>
        <div style={card}>
          <h2>Overall risk: <span style={{ color: COLORS[result.summary.level.toLowerCase()] }}>
            {result.summary.level} ({result.summary.score}/100)</span></h2>
          <p>{result.summary.flagged} risky clauses flagged out of {result.summary.clauses_checked} checked.</p>
        </div>

        <div style={card}>
          <h3>Agent workflow</h3>
          <ol>{result.trace.map((t, i) => <li key={i}>{t}</li>)}</ol>
          <p>Redacted: {Object.entries(result.redaction.counts).map(([k, v]) => `${k} x${v}`).join(", ") || "nothing found"}</p>
        </div>

        {result.findings.map((f, i) => (
          <div key={i} style={{ ...card, borderLeft: `6px solid ${COLORS[f.severity]}` }}>
            <b>{f.title}</b> <span style={{ color: COLORS[f.severity] }}>[{f.severity.toUpperCase()}]</span>
            <small> &nbsp;match {f.similarity}%</small>
            <blockquote style={{ margin: "8px 0", color: "#555" }}>{f.clause_text.slice(0, 300)}</blockquote>
            <p><b>Why it matters:</b> {f.explanation}</p>
            <p><b>Suggested fix:</b> {f.recommendation}</p>
          </div>
        ))}

        <div style={card}>
          <h3>Redacted text preview</h3>
          <pre style={{ whiteSpace: "pre-wrap" }}>{result.redacted_preview}</pre>
        </div>
        <p><small>{result.disclaimer}</small></p>
      </>)}
    </main>
  );
}
