import base64
import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def obtener_maestra_servidor() -> bytes:
    load_dotenv(BASE_DIR / ".env", override=True)
    valor_hex = os.getenv("LLAVE_MAESTRA_SERVIDOR", "").strip()
    if len(valor_hex) == 64:
        try:
            return bytes.fromhex(valor_hex)
        except ValueError:
            pass
    return hashlib.sha256(b"maestra-servidor-iot2").digest()


def derivar_llave_con_sal(llave_32: bytes, sal: str) -> bytes:
    return hashlib.sha256(llave_32 + sal.strip().encode("utf-8")).digest()


def _cifrar_bytes_aes_gcm(llave_32: bytes, datos: bytes, aad: bytes | None = None) -> str:
    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(llave_32)
    ct = aesgcm.encrypt(nonce, datos, aad)
    n_b64 = base64.urlsafe_b64encode(nonce).decode("ascii").rstrip("=")
    c_b64 = base64.urlsafe_b64encode(ct).decode("ascii").rstrip("=")
    return f"s1.{n_b64}.{c_b64}"


def _descifrar_bytes_aes_gcm(llave_32: bytes, token: str, aad: bytes | None = None) -> bytes:
    partes = token.strip().split(".")
    if len(partes) != 3 or partes[0] != "s1":
        raise ValueError("Formato de token AES-256-GCM inválido (se esperaba s1.<iv>.<ct>)")

    def _pad(s: str) -> str:
        return s + "=" * (-len(s) % 4)

    nonce = base64.urlsafe_b64decode(_pad(partes[1]))
    ct = base64.urlsafe_b64decode(_pad(partes[2]))
    aesgcm = AESGCM(llave_32)
    return aesgcm.decrypt(nonce, ct, aad)


def cifrar_llave_para_bd(llave_32: bytes) -> str:
    return _cifrar_bytes_aes_gcm(obtener_maestra_servidor(), llave_32, b"bd-iot2")


def descifrar_llave_desde_bd(llave_cifrada: str) -> bytes:
    return _descifrar_bytes_aes_gcm(obtener_maestra_servidor(), llave_cifrada, b"bd-iot2")


def cifrar_payload_aes_gcm(llave_32: bytes, payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
    return _cifrar_bytes_aes_gcm(llave_32, raw)


def calcular_codigo_hmac_app(
    llave_ses_app_32: bytes, id_c: int | str, pl_c: str, sal: str
) -> str:
    mensaje = f"{id_c}|{pl_c}|{sal}".encode("utf-8")
    return hmac.new(llave_ses_app_32, mensaje, hashlib.sha256).hexdigest()


def verificar_codigo_hmac_app(
    llave_ses_app_32: bytes, id_c: int | str, pl_c: str, sal: str, codigo: str
) -> bool:
    esperado = calcular_codigo_hmac_app(llave_ses_app_32, id_c, pl_c, sal)
    return hmac.compare_digest(esperado, codigo.strip().lower())
