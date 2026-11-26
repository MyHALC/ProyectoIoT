import secrets

from db.redis.connection import redis_client
from seguridad.criptografia import (
    cifrar_llave_para_bd,
    descifrar_llave_desde_bd,
)

APP_SESSION_TTL = 7200  # 2 horas para sesiones de aplicaciones web


def _clave_app(id_ses_app: str) -> str:
    return f"session_app:{id_ses_app}"


def crear_sesion_aplicacion(
    id_pub_app: int,
    tipo_app: str,
    nombre_app: str,
    origen_cors: str,
) -> tuple[str, bytes]:
    if tipo_app not in ("admin", "users"):
        raise ValueError("El tipo_app debe ser 'admin' o 'users'")

    id_ses_app = secrets.token_hex(16)
    llave_ses_app = secrets.token_bytes(32)
    key_app_cifrada = cifrar_llave_para_bd(llave_ses_app)
    clave = _clave_app(id_ses_app)

    with redis_client.pipeline(transaction=True) as pipe:
        pipe.hset(clave, "APP", str(id_pub_app))
        pipe.hset(clave, "ID_ses_app", id_ses_app)
        pipe.hset(clave, "Key_app", key_app_cifrada)
        pipe.hset(clave, "tipo_app", tipo_app)
        pipe.hset(clave, "nombre_app", nombre_app)
        pipe.hset(clave, "origen_cors", origen_cors)
        pipe.expire(clave, APP_SESSION_TTL)
        pipe.execute()

    return id_ses_app, llave_ses_app


def obtener_sesion_aplicacion(id_ses_app: str) -> dict | None:
    if not id_ses_app:
        return None
    clave = _clave_app(id_ses_app.strip())

    with redis_client.pipeline(transaction=False) as pipe:
        pipe.hgetall(clave)
        pipe.ttl(clave)
        datos, tiempo_restante = pipe.execute()

    if not datos or tiempo_restante <= 0:
        return None

    try:
        id_pub_app = int(datos["APP"])
        key_app_cifrada = datos["Key_app"]
        llave_ses_app_bytes = descifrar_llave_desde_bd(key_app_cifrada)
    except (KeyError, TypeError, ValueError):
        return None

    return {
        "APP": id_pub_app,
        "ID_ses_app": datos["ID_ses_app"],
        "Key_app": key_app_cifrada,
        "llave_ses_app_bytes": llave_ses_app_bytes,
        "llave_ses_app_hex": llave_ses_app_bytes.hex(),
        "tipo_app": datos.get("tipo_app", ""),
        "nombre_app": datos.get("nombre_app", ""),
        "origen_cors": datos.get("origen_cors", ""),
        "segundos_restantes": tiempo_restante,
    }


def registrar_nonce_sal(contexto: str, sal: str) -> bool:
    clave = f"nonce:{contexto}:{sal.strip()}"
    if redis_client.exists(clave):
        return False
    redis_client.setex(clave, 300, "1")
    return True
