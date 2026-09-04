from authlib.integrations.base_client.errors import AuthlibBaseError
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.config import settings
from app.db import supabase
from app.oauth import oauth
from app.security import decode_jwt_payload

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request):
    """Punto de entrada del login. Navegacion completa del navegador (no fetch):
    redirige a la pagina de autorizacion del AS, donde el usuario escribe su
    email/contraseña UC. Authlib genera state + code_verifier/code_challenge
    (PKCE) y los guarda en la cookie de sesion firmada durante el transito.
    """
    redirect_uri = f"{settings.app_base_url}/auth/callback"
    return await oauth.as_login.authorize_redirect(
        request,
        redirect_uri,
        resource=settings.app_base_url,  # "resource" != el de un MCP: aca es el origen de la app
        prompt="login",  # fuerza reautenticacion aunque el AS recuerde una sesion previa
    )


@router.get("/callback")
async def callback(request: Request):
    """El AS redirige aca con ?code=...&state=.... Authlib se encarga de:
    verificar que el state coincide con el guardado, y cambiar el code por un
    access_token llamando al token endpoint del AS (mandando tambien el
    code_verifier guardado, para PKCE).
    """
    try:
        token = await oauth.as_login.authorize_access_token(
            request, resource=settings.app_base_url
        )
    except AuthlibBaseError:
        # El usuario le dio "Denegar" en la pantalla del AS (o el state
        # vencio/no coincide) -- el AS vuelve con ?error=... en vez de
        # ?code=.... Sin este catch, Authlib lanza y FastAPI devuelve 500.
        return RedirectResponse(f"{settings.frontend_url}/?login_error=1")

    claims = decode_jwt_payload(token["access_token"])
    email = claims["email"]

    existing = supabase.table("users").select("id").eq("email", email).execute()
    if existing.data:
        user_id = existing.data[0]["id"]
    else:
        inserted = supabase.table("users").insert({"email": email}).execute()
        user_id = inserted.data[0]["id"]

    # Limpiamos cualquier resto del state/code_verifier de transito y dejamos
    # la sesion "real" de la app: de aca en adelante, esta cookie es lo que
    # identifica al usuario logueado (no el JWT del AS -- ese ya cumplio su
    # proposito, autenticar, y no lo guardamos).
    request.session.clear()
    request.session["user_id"] = user_id
    request.session["email"] = email

    return RedirectResponse(f"{settings.frontend_url}/dashboard")


@router.get("/me")
async def me(request: Request):
    """Para que el frontend (o tu, probando a mano) sepa si hay sesion activa."""
    user_id = request.session.get("user_id")
    if not user_id:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "user_id": user_id,
        "email": request.session.get("email"),
    }


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(f"{settings.frontend_url}/?logged_out=1")
