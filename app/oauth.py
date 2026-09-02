from authlib.integrations.starlette_client import OAuth

from app.config import settings

oauth = OAuth()

# Cliente para el LOGIN de la app (no confundir con los clientes de cada MCP,
# que se registran aparte y viven en la tabla mcp_servers). Mismo realm "pre"
# que Andes Air, pero con credenciales propias (AS_CLIENT_ID/AS_CLIENT_SECRET).
#
# server_metadata_url apunta al discovery document del realm (para el authorize/token
# endpoint). code_challenge_method NO se activa solo porque la metadata declare
# code_challenge_methods_supported -- hay que pedirlo explicito aca, si no Authlib
# arma la URL de authorize sin code_challenge/code_challenge_method (verificado
# leyendo authlib/integrations/base_client/sync_app.py: _create_oauth2_authorization_url
# revisa client.code_challenge_method, que solo se setea si se lo pasamos nosotros).
oauth.register(
    name="as_login",
    client_id=settings.as_client_id,
    client_secret=settings.as_client_secret,
    server_metadata_url=f"{settings.as_base_url}/realms/pre/.well-known/openid-configuration",
    client_kwargs={
        "scope": "mcp:tools",
        "code_challenge_method": "S256",
        # Authlib manda el client_secret por HTTP Basic Auth por defecto
        # (client_secret_basic). El AS del curso solo acepta "none" o
        # "client_secret_post" (secret en el body del POST) -- sin esto,
        # el intercambio de code por token falla con "invalid_client".
        "token_endpoint_auth_method": "client_secret_post",
    },
)
