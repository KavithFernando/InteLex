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

INDEX_PATH = os.path.join(_BACKEND_DIR, "index_store", "case_chunks.index")
CHUNK_MAP_PATH = os.path.join(_BACKEND_DIR, "index_store", "case_chunks_map.json")

EMBED_MODEL = "bhavyagiri/InLegal-Sbert"
CHUNK_TOKENS_APPROX = 400
OVERLAP_TOKENS_APPROX = 80
MIN_CHUNK_TOKENS = 100

DATA_JSON_PATH = os.path.join(_BACKEND_DIR, "data", "casedata.json")

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24
