from authlib.integrations.starlette_client import OAuth

from app.security import decrypt_from_db

# Un solo registro Authlib reutilizado para los 3 MCPs (y el login, que vive
# en app/oauth.py aparte). Cada mcp_servers.name se registra la primera vez
# que se necesita y despues queda cacheado en este mismo proceso.
oauth = OAuth()
_registered_names = set()


def get_client(server: dict):
    """server = una fila de la tabla mcp_servers (dict). Registra el cliente
    Authlib la primera vez que se pide ese nombre, y reutiliza despues.
    """
    name = server["name"]
    if name not in _registered_names:
        client_secret = None
        if server.get("client_secret_enc"):
            client_secret = decrypt_from_db(server["client_secret_enc"])

        oauth.register(
            name=name,
            client_id=server["client_id"],
            client_secret=client_secret,
            server_metadata_url=server["metadata_url"],
            client_kwargs={
                "scope": "mcp:tools",
                "code_challenge_method": "S256",
                # CIMD (Cielo Sur) no tiene client_secret -> "none".
                # PRE/DCR si tienen -> "client_secret_post" (ver app/oauth.py
                # sobre por que no "client_secret_basic", el default de Authlib).
                "token_endpoint_auth_method": "client_secret_post" if client_secret else "none",
            },
        )
        _registered_names.add(name)

    return oauth.create_client(name)
