import base64
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
