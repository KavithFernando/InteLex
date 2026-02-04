"""
Thin launcher: expose the API app so `uvicorn app:app` from backend/ works.
"""
from api.app import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
