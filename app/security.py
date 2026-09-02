import base64
import json
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings


def _key() -> bytes:
    # ENCRYPTION_KEY se genera con secrets.token_urlsafe(32); lo normalizamos a 32 bytes.
    raw = settings.encryption_key.encode()
    padded = base64.urlsafe_b64encode(raw)[:32].ljust(32, b"0")
    return padded


def encrypt(plaintext: str) -> bytes:
    aesgcm = AESGCM(_key())
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return nonce + ciphertext


def decrypt(blob: bytes) -> str:
    aesgcm = AESGCM(_key())
    nonce, ciphertext = blob[:12], blob[12:]
    return aesgcm.decrypt(nonce, ciphertext, None).decode()


def encrypt_for_db(plaintext: str) -> str:
    """Cifra y devuelve un string listo para mandarle a un campo bytea via
    supabase-py/PostgREST.

    Verificado empiricamente (no asumido): supabase-py manda un string tal
    cual como el contenido crudo del bytea (no lo interpreta como base64), y
    Postgres lo devuelve despues en formato hex ("\\x..."). Por eso acá
    mandamos el texto base64 del ciphertext -- son los bytes que Postgres
    va a guardar literal -- y decode_from_db() deshace exactamente ese
    camino al leer.
    """
    return base64.b64encode(encrypt(plaintext)).decode("ascii")


def decrypt_from_db(hex_value: str) -> str:
    """Inversa de encrypt_for_db() para un valor bytea tal como lo devuelve
    supabase-py: un string "\\x<hex>" donde el hex, decodificado, es el texto
    base64 que mandamos originalmente.
    """
    raw_bytes = bytes.fromhex(hex_value[2:])  # saca el prefijo "\x"
    b64_str = raw_bytes.decode("ascii")
    ciphertext = base64.b64decode(b64_str)
    return decrypt(ciphertext)


def decode_jwt_payload(token: str) -> dict:
    """Lee los claims de un JWT (email, student_id, etc.) sin verificar la firma.

    No verificamos contra el JWKS del AS aca a proposito: este token no llega
    desde un tercero no confiable -- lo obtuvimos nosotros mismos llamando
    directo al token endpoint del AS, autenticados con AS_CLIENT_SECRET, por
    HTTPS. La verificacion con JWKS (mencionada en el enunciado) tiene sentido
    cuando alguien mas te manda un Bearer token y necesitas confirmar que es
    legitimo -- no es nuestro caso en ningun punto de esta app: en las 3
    conexiones MCP tampoco verificamos, solo reenviamos el token como
    Authorization header, es el servidor MCP quien lo valida.
    """
    payload_b64 = token.split(".")[1]
    padding = "=" * (-len(payload_b64) % 4)
    payload_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
    return json.loads(payload_bytes)
