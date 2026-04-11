import os

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = _BACKEND_DIR

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_TOOL_MODEL = os.getenv("OPENAI_TOOL_MODEL", "gpt-4o-mini")
OPENAI_SYNTHESIS_MODEL = os.getenv("OPENAI_SYNTHESIS_MODEL", "gpt-4o-mini")

# Legacy chunk index (only used by backend/legacy/index_cases.py if you still run that pipeline)
INDEX_PATH = os.path.join(_BACKEND_DIR, "index_store", "case_chunks.index")
CHUNK_MAP_PATH = os.path.join(_BACKEND_DIR, "index_store", "case_chunks_map.json")

# Clause / interpretation-frame index (FAISS over constitution clause text per frame)
CLAUSE_INDEX_PATH = os.path.join(_BACKEND_DIR, "index_store", "clause_frames.index")
CLAUSE_MAP_PATH = os.path.join(_BACKEND_DIR, "index_store", "clause_frames_map.json")

EMBED_MODEL = "bhavyagiri/InLegal-Sbert"
CHUNK_TOKENS_APPROX = 400
OVERLAP_TOKENS_APPROX = 80
MIN_CHUNK_TOKENS = 100

DATA_JSON_PATH = os.path.join(_BACKEND_DIR, "data", "casedata.json")

# Corpus import: frame JSONs + manifest (PDF filenames)
FRAMES_DIR = os.path.join(_BACKEND_DIR, "data", "frames")
MANIFEST_PATH = os.path.join(_BACKEND_DIR, "data", "manifest.json")
# ── Cloudflare R2 object storage ──────────────────────────────────────────────
R2_ACCOUNT_ID        = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID     = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME       = os.getenv("R2_BUCKET_NAME", "intelex-pdfs")
R2_PUBLIC_URL        = os.getenv("R2_PUBLIC_URL", "")

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

# Ingest feature
CONSTITUTION_PATH = os.path.join(_BACKEND_DIR, "data", "constitution", "articles.json")
INGEST_WORK_DIR   = os.path.join(_BACKEND_DIR, "data", "_ingest_work")
PDF_DIR           = os.path.join(_BACKEND_DIR, "data", "pdfs")
