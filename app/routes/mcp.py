from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.config import settings
from app.db import supabase
from app.mcp_oauth import get_client
from app.security import encrypt_for_db

router = APIRouter(tags=["mcp"])

# Los 3 MCPs son fijos y conocidos -- no hay que pedirle al usuario que
# escriba URLs. protocol es solo para mostrar el badge en el frontend.
FIXED_SERVERS = [
    {"name": "andes_air", "label": "Andes Air", "protocol": "PRE"},
    {"name": "staywell", "label": "StayWell", "protocol": "DCR"},
    {"name": "cielo_sur", "label": "Cielo Sur", "protocol": "CMID"},
]


@router.get("/mcp/status")
async def status(request: Request):
    user_id = _require_user(request)

    conns = (
        supabase.table("mcp_connections")
        .select("mcp_servers(name)")
        .eq("user_id", user_id)
        .execute()
    )
    connected_names = {
        c["mcp_servers"]["name"] for c in conns.data if c.get("mcp_servers")
    }

    return [
        {**s, "connected": s["name"] in connected_names} for s in FIXED_SERVERS
    ]


def _get_server_or_404(server_name: str) -> dict:
    res = supabase.table("mcp_servers").select("*").eq("name", server_name).execute()
    if not res.data:
        raise HTTPException(404, f"MCP '{server_name}' no existe en mcp_servers")
    return res.data[0]


def _require_user(request: Request) -> str:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(401, "No hay sesion activa")
    return user_id


@router.get("/connect/{server_name}")
async def connect(server_name: str, request: Request):
    """Arranca el flujo OAuth para conectar un MCP especifico. Requiere estar
    logueado (esto es distinto del login de la app: aqui el 'resource' es la
    URL del MCP en si, no el origen de nuestra app).
    """
    _require_user(request)
    server = _get_server_or_404(server_name)
    client = get_client(server)

    redirect_uri = f"{settings.app_base_url}/connect/{server_name}/callback"
    return await client.authorize_redirect(
        request,
        redirect_uri,
        resource=server["server_url"],
        prompt="login",
    )


@router.get("/connect/{server_name}/callback")
async def connect_callback(server_name: str, request: Request):
    user_id = _require_user(request)
    server = _get_server_or_404(server_name)
    client = get_client(server)

    token = await client.authorize_access_token(request, resource=server["server_url"])

    expires_in = token.get("expires_in", 3600)
    token_expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()

    row = {
        "user_id": user_id,
        "mcp_server_id": server["id"],
        "access_token_enc": encrypt_for_db(token["access_token"]),
        "token_expires_at": token_expires_at,
    }
    if token.get("refresh_token"):
        row["refresh_token_enc"] = encrypt_for_db(token["refresh_token"])

    # unique(user_id, mcp_server_id) en el schema -> upsert por esa pareja
    supabase.table("mcp_connections").upsert(
        row, on_conflict="user_id,mcp_server_id"
    ).execute()

    return RedirectResponse(f"{settings.frontend_url}/dashboard")
