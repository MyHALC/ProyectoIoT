import hashlib
import secrets
import os

from db.redis.connection import redis_client


SESSION_TTL = 1800  # 30 minutos
SESSION_COOKIE = "iot_sid"
COOKIE_PATH = "/api"

COOKIE_SECURE = (
    os.getenv("COOKIE_SECURE", "false").lower() == "true"
)


def _clave(session_id: str) -> str:

    identificador = hashlib.sha256(
        session_id.encode("utf-8")
    ).hexdigest()

    return f"session:{identificador}"


def crear_sesion(
    tipo_cuenta: str,
    id_pub: int
) -> str:

    if tipo_cuenta not in ("usuario", "administrador"):
        raise ValueError("Tipo de cuenta no válido")

    if id_pub <= 0:
        raise ValueError("Identificador no válido")

    session_id = secrets.token_urlsafe(32)
    clave = _clave(session_id)

    with redis_client.pipeline(transaction=True) as pipe:

        pipe.hset(
            clave,
            mapping={
                "tipo_cuenta": tipo_cuenta,
                "id_pub": str(id_pub)
            }
        )

        pipe.expire(clave, SESSION_TTL)

        pipe.execute()

    return session_id


def obtener_sesion(session_id: str) -> dict | None:

    with redis_client.pipeline(transaction=False) as pipe:

        pipe.hgetall(_clave(session_id))
        pipe.ttl(_clave(session_id))

        datos, tiempo_restante = pipe.execute()

    if not datos or tiempo_restante <= 0:
        return None

    try:
        tipo_cuenta = datos["tipo_cuenta"]
        id_pub = int(datos["id_pub"])

    except (KeyError, TypeError, ValueError):
        return None

    if tipo_cuenta not in ("usuario", "administrador"):
        return None

    if id_pub <= 0:
        return None

    return {
        "tipo_cuenta": tipo_cuenta,
        "id_pub": id_pub,
        "segundos_restantes": tiempo_restante
    }

def eliminar_sesion(session_id: str) -> None:

    redis_client.delete(
        _clave(session_id)
    )