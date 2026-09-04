from datetime import datetime, timedelta, timezone

from authlib.integrations.base_client.errors import AuthlibBaseError
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.config import settings
from app.db import supabase
from app.dcr import register_dcr_client
from app.routes.cimd import CIELO_SUR_METADATA_URL
from app.mcp_client import call_mcp, get_valid_access_token
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

# Las 2 URLs de backend donde este servicio corre (local + Render). Se usan
# para registrar redirect_uris validos para AMBOS entornos de una sola vez,
# porque mcp_servers es una tabla compartida entre local y produccion (misma
# Supabase) -- si solo registraramos la del entorno que provisiona primero,
# el otro entorno quedaria con un redirect_uri no registrado.
BACKEND_URLS = [
    "http://localhost:8000",
    "https://t1-t1-backend.onrender.com",
]

# Catalogo fijo con lo necesario para poder provisionar un MCP la primera vez,
# antes de que exista su fila en mcp_servers (protocol_type/server_url/
# metadata_url no cambian nunca, a diferencia de client_id/client_secret que
# si se generan recien al conectar, en el caso DCR).
KNOWN_SERVERS = {
    "andes_air": {
        "protocol_type": "PRE",
        "server_url": "https://tarea1-mcp-pre-z2fqxmm2ja-uc.a.run.app/mcp",
        "metadata_url": f"{settings.as_base_url}/realms/pre/.well-known/openid-configuration",
    },
    "staywell": {
        "protocol_type": "DCR",
        "server_url": "https://tarea1-mcp-dcr-z2fqxmm2ja-uc.a.run.app/mcp",
        "metadata_url": f"{settings.as_base_url}/realms/dcr/.well-known/openid-configuration",
    },
    "cielo_sur": {
        "protocol_type": "CMID",
        "server_url": "https://tarea1-mcp-cimd-z2fqxmm2ja-uc.a.run.app/mcp",
        "metadata_url": f"{settings.as_base_url}/realms/cimd/.well-known/openid-configuration",
    },
}


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


def _get_or_provision_server(server_name: str) -> dict:
    """Busca la fila en mcp_servers. Si no existe y el MCP es de protocolo
    DCR, la crea ahora mismo (registro dinamico + guardar resultado) -- es
    "la primera vez que cualquier usuario conecta [este MCP]" de la que habla
    el enunciado. PRE y CMID no se auto-provisionan aca: PRE se registra a
    mano en /console (scripts/seed_mcp_server.py), y CMID necesita el
    endpoint de metadata propio (todavia no construido).
    """
    res = supabase.table("mcp_servers").select("*").eq("name", server_name).execute()
    if res.data:
        return res.data[0]

    known = KNOWN_SERVERS.get(server_name)
    if not known:
        raise HTTPException(404, f"MCP '{server_name}' desconocido")

    row = {
        "name": server_name,
        "protocol_type": known["protocol_type"],
        "server_url": known["server_url"],
        "metadata_url": known["metadata_url"],
    }

    if known["protocol_type"] == "DCR":
        redirect_uris = [f"{base}/connect/{server_name}/callback" for base in BACKEND_URLS]
        client_id, client_secret = register_dcr_client(server_name, redirect_uris)
        row["client_id"] = client_id
        row["client_secret_enc"] = encrypt_for_db(client_secret)
    elif known["protocol_type"] == "CMID":
        # No hay registro que hacer: el client_id ES la URL del documento de
        # metadata que exponemos nosotros mismos (app/routes/cimd.py). No usa
        # client_secret.
        row["client_id"] = CIELO_SUR_METADATA_URL
    else:
        # PRE necesita client_id creado a mano en /console + scripts/seed_mcp_server.py
        raise HTTPException(
            404,
            f"MCP '{server_name}' (protocolo {known['protocol_type']}) todavia no esta provisionado",
        )

    inserted = supabase.table("mcp_servers").upsert(row, on_conflict="name").execute()
    return inserted.data[0]


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
    server = _get_or_provision_server(server_name)
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
    server = _get_or_provision_server(server_name)
    client = get_client(server)

    try:
        token = await client.authorize_access_token(request, resource=server["server_url"])
    except AuthlibBaseError:
        # Denegado en el AS, o state vencido/no coincide -- mismo caso que
        # en /auth/callback, ver ese comentario.
        return RedirectResponse(f"{settings.frontend_url}/dashboard?connect_error={server_name}")

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


def _get_connection_or_404(user_id: str, server: dict) -> dict:
    res = (
        supabase.table("mcp_connections")
        .select("*")
        .eq("user_id", user_id)
        .eq("mcp_server_id", server["id"])
        .execute()
    )
    if not res.data:
        raise HTTPException(404, f"No estas conectado a '{server['name']}' todavia")
    return res.data[0]


def _access_token_for(user_id: str, server: dict) -> str:
    """Junta lo comun a list_tools/call_tool: busca la conexion, consigue un
    access_token valido (refrescando si hace falta), y si hubo refresh,
    guarda los campos nuevos antes de devolver el token.
    """
    connection = _get_connection_or_404(user_id, server)
    access_token, updates = get_valid_access_token(server, connection)
    if updates:
        supabase.table("mcp_connections").update(updates).eq("id", connection["id"]).execute()
    return access_token


@router.get("/mcp/{server_name}/tools")
async def list_tools(server_name: str, request: Request):
    user_id = _require_user(request)
    server = _get_or_provision_server(server_name)
    access_token = _access_token_for(user_id, server)

    result = call_mcp(server["server_url"], access_token, "tools/list", {})
    return result["tools"]


@router.post("/mcp/{server_name}/tools/{tool_name}/call")
async def call_tool(server_name: str, tool_name: str, request: Request):
    user_id = _require_user(request)
    server = _get_or_provision_server(server_name)
    access_token = _access_token_for(user_id, server)

    arguments = await request.json() if await request.body() else {}
    result = call_mcp(
        server["server_url"], access_token, "tools/call", {"name": tool_name, "arguments": arguments}
    )
    return result
