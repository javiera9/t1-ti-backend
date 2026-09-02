from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings

app = FastAPI(title="IntegraTrip API")

# Firma la cookie de sesion (login + state/PKCE en transito OAuth). Ver CLAUDE.md.
app.add_middleware(SessionMiddleware, secret_key=settings.cookie_secret)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}
