"""
FastAPI application: create app, add CORS, include routers.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import auth as auth_router
from api.routes import chat as chat_router
from api.routes import cases as cases_router

app = FastAPI(title="Legal Assistant (Groq + Retrieval)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(chat_router.router, tags=["chat"])
app.include_router(cases_router.router, tags=["cases"])
