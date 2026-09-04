from datetime import datetime, timedelta, timezone

import httpx
from fastapi import HTTPException

from app.security import decrypt_from_db, encrypt_for_db


def get_valid_access_token(server: dict, connection: dict) -> tuple[str, dict | None]:
    """Devuelve un access_token utilizable para este MCP. Si el guardado ya
    vencio (o esta por vencer), lo refresca contra el AS usando el
    refresh_token guardado -- probado empiricamente: el AS rota el
    refresh_token en cada uso, hay que guardar el nuevo tambien.

    Devuelve (access_token, updates). `updates` es None si no hizo falta
    refrescar, o un dict con los campos nuevos para que el caller los guarde
    en mcp_connections (este modulo no toca la base de datos directamente).
    """
    expires_at = datetime.fromisoformat(connection["token_expires_at"])
    if datetime.now(timezone.utc) < expires_at - timedelta(seconds=30):
        return decrypt_from_db(connection["access_token_enc"]), None

    if not connection.get("refresh_token_enc"):
        raise HTTPException(401, "El token vencio y no hay refresh_token guardado; reconecta este MCP")

    refresh_token = decrypt_from_db(connection["refresh_token_enc"])
    metadata = httpx.get(server["metadata_url"], timeout=15).json()

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": server["client_id"],
    }
    if server.get("client_secret_enc"):
        data["client_secret"] = decrypt_from_db(server["client_secret_enc"])

    resp = httpx.post(metadata["token_endpoint"], data=data, timeout=15)
    if resp.status_code >= 400:
        raise HTTPException(401, "No se pudo refrescar el token; reconecta este MCP")
    token = resp.json()

    new_expires_at = (
        datetime.now(timezone.utc) + timedelta(seconds=token.get("expires_in", 3600))
    ).isoformat()
    updates = {
        "access_token_enc": encrypt_for_db(token["access_token"]),
        "token_expires_at": new_expires_at,
    }
    if token.get("refresh_token"):
        updates["refresh_token_enc"] = encrypt_for_db(token["refresh_token"])

    return token["access_token"], updates


def call_mcp(server_url: str, access_token: str, method: str, params: dict) -> dict:
    """POST JSON-RPC 2.0 al endpoint /mcp del servidor (probado empiricamente
    contra Andes Air: no requiere handshake/sesion previa, responde JSON
    plano con este Accept header).
    """
    resp = httpx.post(
        server_url,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise HTTPException(502, f"Error del MCP: {data['error']}")
    return data["result"]
