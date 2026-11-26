import json

from db.redis.connection import redis_client


PREFIJO = "datos:"


# ============================
# OBTENER NOMBRE DE CLAVE
# ============================

def _clave(nombre: str) -> str:

    if not isinstance(nombre, str) or not nombre.strip():
        raise ValueError("La clave no puede estar vacía")

    return f"{PREFIJO}{nombre}"


# ============================
# GUARDAR O ACTUALIZAR
# ============================

def guardar_valor(
    nombre: str,
    valor,
    ttl: int | None = None
) -> bool:

    if ttl is not None and (
        type(ttl) is not int or ttl <= 0
    ):
        raise ValueError("El TTL debe ser positivo")

    datos = json.dumps(valor, ensure_ascii=False)

    return bool(
        redis_client.set(
            _clave(nombre),
            datos,
            ex=ttl
        )
    )


# ============================
# CONSULTAR VALOR
# ============================

def obtener_valor(nombre: str):

    datos = redis_client.get(
        _clave(nombre)
    )

    if datos is None:
        return None

    return json.loads(datos)


# ============================
# ELIMINAR CLAVE
# ============================

def eliminar_clave(nombre: str) -> bool:

    return redis_client.delete(
        _clave(nombre)
    ) > 0


# ============================
# COMPROBAR EXISTENCIA
# ============================

def existe_clave(nombre: str) -> bool:

    return redis_client.exists(
        _clave(nombre)
    ) > 0


# ============================
# ESTABLECER EXPIRACIÓN
# ============================

def establecer_ttl(
    nombre: str,
    segundos: int
) -> bool:

    if type(segundos) is not int or segundos <= 0:
        raise ValueError("El TTL debe ser positivo")

    return bool(
        redis_client.expire(
            _clave(nombre),
            segundos
        )
    )


# ============================
# CONSULTAR EXPIRACIÓN
# ============================

def consultar_ttl(nombre: str) -> int:

    return redis_client.ttl(
        _clave(nombre)
    )


# ============================
# ELIMINAR EXPIRACIÓN
# ============================

def quitar_ttl(nombre: str) -> bool:

    return bool(
        redis_client.persist(
            _clave(nombre)
        )
    )


# ============================
# LISTAR CLAVES
# ============================

def listar_claves() -> list[str]:

    claves = redis_client.scan_iter(
        match=f"{PREFIJO}*",
        count=100
    )

    return [
        clave.removeprefix(PREFIJO)
        for clave in claves
    ]