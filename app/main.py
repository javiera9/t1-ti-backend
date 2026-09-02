from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.routes import auth, mcp

app = FastAPI(title="IntegraTrip API")

# Firma la cookie de sesion (login + state/PKCE en transito OAuth). Ver CLAUDE.md.
# same_site="none" + https_only=True son necesarios en produccion porque el
# frontend (t1-ti-frontend.onrender.com) y el backend (t1-t1-backend.onrender.com)
# son dominios distintos: sin esto, el navegador no manda la cookie de sesion
# cuando el frontend le hace fetch al backend. En local (http) se relaja porque
# los navegadores rechazan cookies "Secure" fuera de HTTPS.
is_https = settings.app_base_url.startswith("https")
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.cookie_secret,
    same_site="none" if is_https else "lax",
    https_only=is_https,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(mcp.router)


@app.get("/health")
def health():
    return {"status": "ok"}
