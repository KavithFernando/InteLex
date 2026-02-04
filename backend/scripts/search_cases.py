"""
Thin wrapper over services.retrieval for CLI or script use.
Run from backend/ so that 'db' and 'services' resolve (or set PYTHONPATH to backend/).
"""
import sys
import os

# Ensure backend is on path when run from repo root or scripts/
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services.retrieval import search_cases

__all__ = ["search_cases"]
