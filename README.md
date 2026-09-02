# t1-ti-backend

IntegraTrip — Tarea 1 de Taller de Integración - Javiera Martínez.

API en Python (FastAPI) que hace de cliente MCP hacia Andes Air (PRE), StayWell (DCR) y Cielo Sur (CMID). El frontend vive aparte, en [`t1-ti-frontend`](https://github.com/javiera9/t1-ti-frontend) (React + Vite).

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
