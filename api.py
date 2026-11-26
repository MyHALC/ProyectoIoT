"""API JSON del frontend: login, cuentas (usuarios/administradores) y dispositivos.

Todas las consultas a MySQL son parametrizadas. Las rutas protegidas vuelven a leer
la cuenta en la base en cada petición, así que desactivar una cuenta le quita el
acceso de inmediato, aunque conserve su cookie de sesión.
"""
import re
import secrets
import time
from collections import defaultdict, deque
from functools import wraps

import pymysql
from flask import Blueprint, g, jsonify, request, session

import db
import seguridad
from utils.email import enviar_correo_bienvenida

api = Blueprint("api", __name__, url_prefix="/api")

PATRON_USUARIO = re.compile(r"^[A-Za-z0-9._-]{3,30}$")
PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PATRON_IDENTIFICADOR = re.compile(r"^[A-Za-z0-9._-]{1,30}$")

# Hash de relleno: si el usuario no existe se verifica contra este para que
# la respuesta tarde lo mismo y no revele qué cuentas existen.
HASH_FALSO = seguridad.hashear(secrets.token_hex(16))

MAX_INTENTOS = 5
VENTANA_SEGUNDOS = 300
_intentos = defaultdict(deque)


class Invalido(ValueError):
    """Datos mal formados (400)."""


class Prohibido(Exception):
    """El rol de la cuenta no permite la operación (403)."""


def error(codigo, detalle):
    return jsonify({"detail": detalle}), codigo


@api.errorhandler(Invalido)
def _invalido(e):
    return error(400, str(e))


@api.errorhandler(Prohibido)
def _prohibido(e):
    return error(403, str(e) or "No tienes permiso para esta operación.")


@api.errorhandler(pymysql.err.OperationalError)
def _sin_base_de_datos(e):
    return error(503, "La base de datos no está disponible. Revisa que Docker esté en ejecución.")


@api.before_request
def exigir_json():
    # Un formulario de otro sitio no puede enviar application/json sin permiso previo (CORS).
    if request.method in ("POST", "PATCH", "PUT", "DELETE") and not request.is_json:
        return error(415, "El contenido debe enviarse como JSON.")


# ---------------------------------------------------------------- utilidades

def cuerpo():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        raise Invalido("El cuerpo de la petición no es válido.")
    return datos


def texto(datos, campo, etiqueta, maximo, minimo=1):
    valor = datos.get(campo)
    if not isinstance(valor, str):
        raise Invalido(f"{etiqueta} es obligatorio.")
    valor = valor.strip()
    if not minimo <= len(valor) <= maximo:
        raise Invalido(f"{etiqueta} debe tener entre {minimo} y {maximo} caracteres.")
    return valor


def fecha(valor):
    if valor is None:
        return None
    return valor.isoformat() if hasattr(valor, "isoformat") else str(valor)


def cuenta_publica(f):
    return {
        "id": f["id"],
        "rol": f["rol"],
        "nombre_completo": f["nombre_completo"],
        "usuario": f["usuario"],
        "correo": f["correo"],
        "estado": f["estado"],
        "fecha_registro": fecha(f["fecha_registro"]),
    }


def dispositivo_publico(f):
    return {
        "id": f["id"],
        "identificador": f["identificador"],
        "zona": f["zona"],
        "descripcion": f["descripcion"],
        "estado": f["estado"],
        "fecha_registro": fecha(f["fecha_registro"]),
    }


def consultar(sql, parametros=()):
    with db.obtener().cursor() as cur:
        cur.execute(sql, parametros)
        return cur.fetchall()


def consultar_uno(sql, parametros=()):
    with db.obtener().cursor() as cur:
        cur.execute(sql, parametros)
        return cur.fetchone()


# ------------------------------------------------------------ sesión y roles

def cuenta_actual():
    """Cuenta de la sesión, leída de la base. None si no hay sesión o ya no está activa."""
    id_cuenta = session.get("cuenta_id")
    if not isinstance(id_cuenta, int) or session.get("solo_cambio_contrasena"):
        return None
    fila = consultar(
        "SELECT id, rol, nombre_completo, usuario, correo, estado "
        "FROM cuentas WHERE id = %s", (id_cuenta,))
    if not fila or fila[0]["estado"] != "activo":
        session.clear()
        return None
    return fila[0]


def requiere(*roles):
    def decorador(vista):
        @wraps(vista)
        def interna(*args, **kwargs):
            cuenta = cuenta_actual()
            if cuenta is None:
                return error(401, "Inicia sesión para continuar.")
            if cuenta["rol"] not in roles:
                return error(403, "No tienes permiso para esta operación.")
            g.cuenta = cuenta
            return vista(*args, **kwargs)
        return interna
    return decorador


def _rol_gestionable(rol):
    """El master gestiona administradores y usuarios; un administrador solo usuarios."""
    if rol not in ("usuario", "administrador"):
        raise Invalido("Indica el rol: usuario o administrador.")
    if rol == "administrador" and g.cuenta["rol"] != "master":
        raise Prohibido("Solo el administrador master gestiona administradores.")
    return rol


# ---------------------------------------------------------------------- login

def _bloqueado(clave):
    ahora = time.monotonic()
    cola = _intentos[clave]
    while cola and cola[0] <= ahora - VENTANA_SEGUNDOS:
        cola.popleft()
    return len(cola) >= MAX_INTENTOS


def _registrar_fallo(clave):
    if len(_intentos) > 10000:
        _intentos.clear()
    _intentos[clave].append(time.monotonic())


@api.post("/usuarios/login/")
def login():
    datos = cuerpo()
    alias = datos.get("usuario")
    contrasena = datos.get("contraseña", datos.get("contrasena"))
    if not isinstance(alias, str) or not isinstance(contrasena, str) \
            or not alias.strip() or not contrasena:
        raise Invalido("Escribe tu usuario y contraseña.")
    alias = alias.strip()

    clave = (request.remote_addr, alias.lower())
    if _bloqueado(clave):
        return error(429, "Demasiados intentos. Espera unos minutos.")

    filas = consultar("SELECT * FROM cuentas WHERE usuario = %s OR correo = %s",
                      (alias, alias.lower()))
    fila = filas[0] if len(filas) == 1 else None
    guardado = fila["contrasena_hash"] if fila else HASH_FALSO
    correcta = seguridad.verificar(contrasena[:128], guardado) and fila is not None
    if not correcta:
        _registrar_fallo(clave)
        return error(401, "Usuario o contraseña incorrectos.")

    if fila["estado"] == "pendiente":
        return error(403, "Tu cuenta está pendiente de activación por un administrador.")
    if fila["estado"] != "activo":
        return error(403, "Tu cuenta está inactiva.")

    _intentos.pop(clave, None)
    session.clear()
    session["cuenta_id"] = fila["id"]
    # Con contraseña provisional la sesión sirve solo para cambiarla.
    if not fila["contra_cambiada"]:
        session["solo_cambio_contrasena"] = True
    session.permanent = True
    return jsonify({
        "estado": "exito",
        "usuario": {
            "id": fila["id"],
            "rol": fila["rol"],
            "nombre_completo": fila["nombre_completo"],
            "usuario": fila["usuario"],
            "correo": fila["correo"],
            # Esto es lo que el equipo debe usar para pedir el cambio de contraseña.
            "requiere_cambio_contrasena": not fila["contra_cambiada"],
        },
    })


@api.post("/cambiar-contrasena")
def cambiar_contrasena():
    id_cuenta = session.get("cuenta_id")
    if not isinstance(id_cuenta, int) or not session.get("solo_cambio_contrasena"):
        return error(401, "Inicia sesión para continuar.")
    nueva = cuerpo().get("contrasena_nueva")
    if not isinstance(nueva, str) or not 8 <= len(nueva) <= 128:
        raise Invalido("La contraseña nueva debe tener entre 8 y 128 caracteres.")

    fila = consultar_uno(
        "SELECT contrasena_hash, estado, contra_cambiada FROM cuentas WHERE id = %s",
        (id_cuenta,))
    if not fila or fila["estado"] != "activo" or fila["contra_cambiada"]:
        session.clear()
        return error(401, "Inicia sesión para continuar.")
    if seguridad.verificar(nueva, fila["contrasena_hash"]):
        raise Invalido("La contraseña nueva debe ser distinta de la provisional.")

    conexion = db.obtener()
    with conexion.cursor() as cur:
        cur.execute(
            "UPDATE cuentas SET contrasena_hash = %s, contra_cambiada = 1 WHERE id = %s",
            (seguridad.hashear(nueva), id_cuenta))
    conexion.commit()
    session.clear()
    return jsonify({"estado": "exito"})


@api.post("/salir")
def salir():
    session.clear()
    return jsonify({"estado": "exito"})


# --------------------------------------------------------------------- cuentas

@api.get("/cuentas")
@requiere("master", "administrador")
def listar_cuentas():
    rol = _rol_gestionable(request.args.get("rol"))
    filas = consultar(
        "SELECT id, rol, nombre_completo, usuario, correo, estado, fecha_registro "
        "FROM cuentas WHERE rol = %s ORDER BY id", (rol,))
    return jsonify([cuenta_publica(f) for f in filas])


@api.post("/cuentas")
@requiere("master", "administrador")
def crear_cuenta():
    datos = cuerpo()
    rol = _rol_gestionable(datos.get("rol"))
    nombre = texto(datos, "nombre_completo", "El nombre completo", 100)
    correo = texto(datos, "correo", "El correo electrónico", 254).lower()
    if not PATRON_CORREO.match(correo):
        raise Invalido("El correo electrónico no es válido.")
    usuario = texto(datos, "usuario", "El nombre de usuario", 30, 3)
    if not PATRON_USUARIO.match(usuario):
        raise Invalido("El usuario solo admite letras, números, punto, guion y guion bajo.")
    contrasena = datos.get("contrasena")
    if not isinstance(contrasena, str) or not 8 <= len(contrasena) <= 128:
        raise Invalido("La contraseña provisional debe tener entre 8 y 128 caracteres.")

    for existente in consultar(
            "SELECT correo, usuario FROM cuentas WHERE correo = %s OR usuario = %s",
            (correo, usuario)):
        if existente["correo"].lower() == correo:
            return error(409, "Ese correo electrónico ya está registrado.")
        return error(409, "Ese nombre de usuario ya está registrado.")

    conexion = db.obtener()
    try:
        with conexion.cursor() as cur:
            cur.execute(
                "INSERT INTO cuentas (rol, nombre_completo, correo, usuario, "
                "contrasena_hash, contra_cambiada, estado, creado_por) "
                "VALUES (%s, %s, %s, %s, %s, 0, 'pendiente', %s)",
                (rol, nombre, correo, usuario, seguridad.hashear(contrasena), g.cuenta["id"]))
            nuevo_id = cur.lastrowid
        conexion.commit()
    except pymysql.err.IntegrityError:
        conexion.rollback()
        return error(409, "El correo o el usuario ya están registrados.")

    fila = consultar_uno(
        "SELECT id, rol, nombre_completo, usuario, correo, estado, fecha_registro "
        "FROM cuentas WHERE id = %s", (nuevo_id,))
    respuesta = cuenta_publica(fila)

    # El correo va fuera de la transacción: si falla, la cuenta ya quedó creada.
    try:
        enviar_correo_bienvenida(correo, nombre, usuario, contrasena)
        respuesta["correo_enviado"] = True
    except Exception as e:
        print(f"Error al enviar correo de bienvenida: {e}")
        respuesta["correo_enviado"] = False
    return jsonify(respuesta), 201


@api.patch("/cuentas/<int:id_cuenta>/estado")
@requiere("master", "administrador")
def cambiar_estado_cuenta(id_cuenta):
    estado = cuerpo().get("estado")
    if estado not in ("activo", "inactivo"):
        raise Invalido("El estado debe ser activo o inactivo.")
    objetivo = consultar_uno("SELECT id, rol FROM cuentas WHERE id = %s", (id_cuenta,))
    if objetivo is None:
        return error(404, "La cuenta no existe.")
    if objetivo["rol"] == "master" or objetivo["id"] == g.cuenta["id"]:
        raise Prohibido("No puedes cambiar el estado de esa cuenta.")
    if objetivo["rol"] == "administrador" and g.cuenta["rol"] != "master":
        raise Prohibido("Solo el administrador master gestiona administradores.")

    conexion = db.obtener()
    with conexion.cursor() as cur:
        cur.execute("UPDATE cuentas SET estado = %s WHERE id = %s", (estado, id_cuenta))
    conexion.commit()
    return jsonify({"id": id_cuenta, "estado": estado})


# ---------------------------------------------------------------- dispositivos

@api.get("/dispositivos")
@requiere("master", "administrador")
def listar_dispositivos():
    filas = consultar(
        "SELECT id, identificador, zona, descripcion, estado, fecha_registro "
        "FROM dispositivos ORDER BY id")
    return jsonify([dispositivo_publico(f) for f in filas])


@api.post("/dispositivos")
@requiere("master", "administrador")
def crear_dispositivo():
    datos = cuerpo()
    identificador = texto(datos, "identificador", "El identificador", 30)
    if not PATRON_IDENTIFICADOR.match(identificador):
        raise Invalido("El identificador solo admite letras, números, punto, guion y guion bajo.")
    zona = texto(datos, "zona", "La zona de monitoreo", 50)
    descripcion = texto(datos, "descripcion", "La descripción", 255)

    if consultar("SELECT id FROM dispositivos WHERE identificador = %s", (identificador,)):
        return error(409, "Ya existe un dispositivo con ese identificador.")

    conexion = db.obtener()
    try:
        with conexion.cursor() as cur:
            cur.execute(
                "INSERT INTO dispositivos (identificador, zona, descripcion, estado, creado_por) "
                "VALUES (%s, %s, %s, 'activo', %s)",
                (identificador, zona, descripcion, g.cuenta["id"]))
            nuevo_id = cur.lastrowid
        conexion.commit()
    except pymysql.err.IntegrityError:
        conexion.rollback()
        return error(409, "Ya existe un dispositivo con ese identificador.")

    fila = consultar_uno(
        "SELECT id, identificador, zona, descripcion, estado, fecha_registro "
        "FROM dispositivos WHERE id = %s", (nuevo_id,))
    return jsonify(dispositivo_publico(fila)), 201


@api.patch("/dispositivos/<int:id_dispositivo>/estado")
@requiere("master", "administrador")
def cambiar_estado_dispositivo(id_dispositivo):
    estado = cuerpo().get("estado")
    if estado not in ("activo", "inactivo"):
        raise Invalido("El estado debe ser activo o inactivo.")
    if not consultar("SELECT id FROM dispositivos WHERE id = %s", (id_dispositivo,)):
        return error(404, "El dispositivo no existe.")
    conexion = db.obtener()
    with conexion.cursor() as cur:
        cur.execute("UPDATE dispositivos SET estado = %s WHERE id = %s", (estado, id_dispositivo))
    conexion.commit()
    return jsonify({"id": id_dispositivo, "estado": estado})
