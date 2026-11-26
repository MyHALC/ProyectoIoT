"""Comunicación cifrada entre el frontend y el backend.

Formato (igual para petición y respuesta):

    Texto plano:  la estructura normal del endpoint, en JSON.
                  p. ej. {"id": 3, "identificador": "ESP32-01", "estado": "activo"}

    En el cable:  {"datos_cifrados": "<token Fernet>"}

El token es Fernet (AES-128-CBC + HMAC-SHA256, en base64 url-safe) del JSON en UTF-8.
Ambos lados usan la misma LLAVE_SECRETA del .env. Para generarla:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
import json
import os

from cryptography.fernet import Fernet, InvalidToken

CAMPO = "datos_cifrados"


def _fernet():
    llave = os.getenv("LLAVE_SECRETA")
    if not llave:
        raise RuntimeError("Define LLAVE_SECRETA en .env (la misma que usa el backend).")
    return Fernet(llave.encode())


def cifrar_datos(datos) -> str:
    """dict/list -> JSON -> token cifrado (str)."""
    texto_plano = json.dumps(datos, ensure_ascii=False, default=str)
    return _fernet().encrypt(texto_plano.encode("utf-8")).decode()


def descifrar_datos(token: str):
    """token cifrado (str) -> dict/list. ValueError si el token no es válido."""
    try:
        texto_plano = _fernet().decrypt(token.encode())
    except (InvalidToken, AttributeError) as e:
        raise ValueError("Los datos cifrados no son válidos o la llave no coincide.") from e
    return json.loads(texto_plano.decode("utf-8"))


def empaquetar(datos) -> dict:
    """Respuesta/petición de un endpoint -> sobre {"datos_cifrados": ...} listo para enviar."""
    return {CAMPO: cifrar_datos(datos)}


def desempaquetar(sobre):
    """Sobre recibido -> estructura original del endpoint."""
    if not isinstance(sobre, dict) or not isinstance(sobre.get(CAMPO), str):
        raise ValueError(f'Se esperaba un JSON con la forma {{"{CAMPO}": "..."}}.')
    return descifrar_datos(sobre[CAMPO])
