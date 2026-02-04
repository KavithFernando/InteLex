"""
Centralized configuration: env loading, paths, DB, Groq, indexing constants.
"""
from dotenv import load_dotenv

load_dotenv()

from config.settings import (
    BACKEND_DIR,
    DB_CONFIG,
    GROQ_API_KEY,
    INDEX_PATH,
    CHUNK_MAP_PATH,
    EMBED_MODEL,
    CHUNK_TOKENS_APPROX,
    OVERLAP_TOKENS_APPROX,
    MIN_CHUNK_TOKENS,
    DATA_JSON_PATH,
)

__all__ = [
    "BACKEND_DIR",
    "DB_CONFIG",
    "GROQ_API_KEY",
    "INDEX_PATH",
    "CHUNK_MAP_PATH",
    "EMBED_MODEL",
    "CHUNK_TOKENS_APPROX",
    "OVERLAP_TOKENS_APPROX",
    "MIN_CHUNK_TOKENS",
    "DATA_JSON_PATH",
]
