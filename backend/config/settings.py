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
# Stored in cases.pdf_relative_path; app resolves against PDF_ROOT or static mount
PDF_RELATIVE_PREFIX = os.getenv("PDF_RELATIVE_PREFIX", "")
# Absolute path to the directory on disk where PDF files are stored.
PDF_ROOT = os.getenv("PDF_ROOT", "")

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
