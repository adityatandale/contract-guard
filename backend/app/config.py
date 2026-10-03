import os

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")   # or "mistral"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_db")
# cosine distance: lower = more similar. Clause is flagged if distance <= threshold.
RISK_DISTANCE = float(os.getenv("RISK_DISTANCE", "0.55"))
MAX_UPLOAD_MB = 10
