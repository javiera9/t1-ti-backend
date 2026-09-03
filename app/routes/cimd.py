from fastapi import APIRouter

router = APIRouter(prefix="/cimd", tags=["cimd"])

# URL fija, siempre la de produccion (nunca localhost): el client_id de CMID
# tiene que ser una URL HTTPS publica y estable -- no depende de en que
# entorno corre este proceso ahora mismo, tiene que ser siempre la misma.
CIELO_SUR_METADATA_URL = "https://t1-t1-backend.onrender.com/cimd/cielo_sur.json"


@router.get("/cielo_sur.json")
async def cielo_sur_client_metadata():
    """Documento de metadata autorreferencial (CIMD). El AS lo descarga el
    solo durante /authorize, usando como client_id la URL de este mismo
    endpoint -- este documento ES el registro, no hay paso previo.
    """
    return {
        "client_id": CIELO_SUR_METADATA_URL,
        "client_name": "IntegraTrip",
        "redirect_uris": [
            "http://localhost:8000/connect/cielo_sur/callback",
            "https://t1-t1-backend.onrender.com/connect/cielo_sur/callback",
        ],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
    }
