import httpx

from app.config import settings


def register_dcr_client(name: str, redirect_uris: list[str]) -> tuple[str, str]:
    """POST /realms/dcr/register (RFC 7591). Se llama una sola vez por MCP
    (la primera vez que alguien lo conecta) -- ver app/routes/mcp.py, donde
    se guarda el resultado en mcp_servers para no volver a registrar.

    No mandamos el header Authorization opcional (asociaria el cliente a la
    cuenta de quien lo registra y apareceria en /console) -- decision
    consciente por simplicidad, no cambia el funcionamiento.
    """
    resp = httpx.post(
        f"{settings.as_base_url}/realms/dcr/register",
        json={
            "client_name": f"IntegraTrip - {name}",
            "redirect_uris": redirect_uris,
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "client_secret_post",
        },
    )
    resp.raise_for_status()
    data = resp.json()
    return data["client_id"], data["client_secret"]
