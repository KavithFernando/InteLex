from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.limiter import limiter
from api.routes import auth as auth_router
from api.routes import chat as chat_router
from api.routes import cases as cases_router
from api.routes import admin as admin_router
from config import FRONTEND_ORIGIN
from services.clause_retrieval import ClauseFrameRetrievalService

app = FastAPI(title="Legal Assistant (Groq + Retrieval)")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(chat_router.router, tags=["chat"])
app.include_router(cases_router.router, tags=["cases"])
app.include_router(admin_router.router)

# Shared retrieval service — attached to app.state so the ingest pipeline can call reload()
_retrieval_service = ClauseFrameRetrievalService()

@app.on_event("startup")
async def _startup() -> None:
    app.state.retrieval_service = _retrieval_service
    logger.info("[App] Retrieval service attached to app.state")

logger.info("[App] InteLex backend starting | CORS origin={}", FRONTEND_ORIGIN)
