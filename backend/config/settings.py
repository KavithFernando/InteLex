"""
Settings: backend dir, paths, DB, Groq, and indexing defaults.
Load dotenv in config/__init__.py so this module can assume env is loaded when imported.
"""
import os

# Backend root (parent of config/)
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = _BACKEND_DIR

# Database (used by db.connection and scripts)
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

# Groq (used by services.chat)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Index store (used by services.retrieval and scripts.index_cases)
INDEX_PATH = os.path.join(_BACKEND_DIR, "index_store", "case_chunks.index")
CHUNK_MAP_PATH = os.path.join(_BACKEND_DIR, "index_store", "case_chunks_map.json")

# Embedding and chunking (used by scripts.index_cases; retrieval uses CHUNK_MAP for model name)
EMBED_MODEL = "bhavyagiri/InLegal-Sbert"
CHUNK_TOKENS_APPROX = 400
OVERLAP_TOKENS_APPROX = 80
MIN_CHUNK_TOKENS = 100

# Data (used by scripts.import_cases)
DATA_JSON_PATH = os.path.join(_BACKEND_DIR, "data", "casedata.json")
