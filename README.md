# t1-ti-backend

IntegraTrip — Tarea 1 de Taller de Integración - Javiera Martínez.

API en Python (FastAPI) que hace de cliente MCP hacia Andes Air (PRE), StayWell (DCR) y Cielo Sur (CMID). El frontend vive aparte, en [`t1-ti-frontend`](https://github.com/javiera9/t1-ti-frontend) (React + Vite).

## Herramientas y referencias usadas

Se utilizó Claude Sonnet 5 para la construcción de código, estudio de contenidos y apoyo en general para la tarea. También, se contó con la documentación proporcionada por el equipo docente en el enunciado de la tarea, además de la documentación de Authlib y OAuth 2.0, además de material sobre los protocolos PRE, DCR, CMID y videos en YouTube para entender MCP y los flujos.

Links referencias:
- https://www.scalekit.com/blog/dynamic-client-registration-oauth2
- https://www.mcpjam.com/blog/mcp-oauth-guide
- https://auth0.com/docs/get-started/authentication-and-authorization-flow/which-oauth-2-0-flow-should-i-use
- https://auth0.com/docs/get-started/authentication-and-authorization-flow/authorization-code-flow
- https://auth0.com/docs/secure/attack-protection/state-parameters
- https://blog.modelcontextprotocol.io/posts/client_registration/
- https://www.youtube.com/watch?v=ZDuRmhLSLOY&t=176s

## URL en producción

**API desplegada: https://t1-t1-backend.onrender.com**

La app para usar (login, conectar MCPs, tools) es el frontend: https://t1-ti-frontend.onrender.com — este backend es solo la API, no sirve HTML.

## Setup local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

El schema de base de datos vive en [`db/schema.sql`](db/schema.sql) — se aplica pegándolo en el SQL Editor de tu proyecto Supabase.

Completa `.env` con:
- `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`: desde el dashboard de tu proyecto Supabase (Settings > API).
- `ENCRYPTION_KEY` / `COOKIE_SECRET`: generar cada uno con `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
- `AS_CLIENT_ID` / `AS_CLIENT_SECRET`: cliente OAuth (realm `pre`) creado en `/console` del AS, solo para el login de esta app.
- `FRONTEND_URL`: origen donde corre el frontend (`http://localhost:5173` en dev).

## Correr localmente

```bash
uvicorn app.main:app --reload
```

Luego `http://localhost:8000/health` deberia responder `{"status": "ok"}`.

## Deploy (Render)

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Variables de entorno: las mismas de `.env`, configuradas en el dashboard de Render (nunca en el codigo). `FRONTEND_URL` debe apuntar a la URL de produccion del frontend.
