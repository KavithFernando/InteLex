"""
Centralized configuration: env loading, paths, DB, Groq, indexing constants.
"""
from dotenv import load_dotenv

load_dotenv()

from config.settings import (
    BACKEND_DIR,
    DB_CONFIG,
    GROQ_API_KEY,
    OPENAI_API_KEY,
    OPENAI_TOOL_MODEL,
    OPENAI_SYNTHESIS_MODEL,
    EMBED_MODEL,
    CHUNK_TOKENS_APPROX,
    OVERLAP_TOKENS_APPROX,
    MIN_CHUNK_TOKENS,
    DATA_JSON_PATH,
    JWT_SECRET,
    JWT_ALGORITHM,
    JWT_EXPIRE_MINUTES,
    FRONTEND_ORIGIN,
)

__all__ = [
    "BACKEND_DIR",
    "DB_CONFIG",
    "GROQ_API_KEY",
    "OPENAI_API_KEY",
    "OPENAI_TOOL_MODEL",
    "OPENAI_SYNTHESIS_MODEL",
    "EMBED_MODEL",
    "CHUNK_TOKENS_APPROX",
    "OVERLAP_TOKENS_APPROX",
    "MIN_CHUNK_TOKENS",
    "DATA_JSON_PATH",
    "JWT_SECRET",
    "JWT_ALGORITHM",
    "JWT_EXPIRE_MINUTES",
    "FRONTEND_ORIGIN",
]
