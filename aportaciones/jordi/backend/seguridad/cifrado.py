import base64
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from config import config
from middleware import cifrado as modulo_cifrado


cifrar = modulo_cifrado.cifrar
descifrar = modulo_cifrado.descifrar


def cifrar_con_contexto(llave, pl, iv, contexto):
    return AESGCM(llave).encrypt(iv, pl, contexto)


def descifrar_con_contexto(llave, pl_c, iv, contexto):
    return AESGCM(llave).decrypt(iv, pl_c, contexto)


def decodificar(llave):
    datos = base64.b64decode(llave, altchars=b'-_', validate=True)
    if len(datos) != 32:
        raise ValueError('La llave debe tener 32 bytes.')
    return datos


class ProtectorLlaves:
    def __init__(self, maestra):
        self.maestra = decodificar(maestra)

    def proteger(self, llave, contexto):
        iv = secrets.token_bytes(12)
        return base64.b64encode(iv + cifrar_con_contexto(self.maestra, llave, iv, contexto)).decode('ascii')

    def abrir(self, guardada, contexto):
        paquete = base64.b64decode(guardada, validate=True)
        if len(paquete) != 60:
            raise ValueError('Formato de llave cifrada inválido.')
        return descifrar_con_contexto(self.maestra, paquete[12:], paquete[:12], contexto)


def contexto_identidad(entidad):
    return f'iot2/identidad/{entidad.tipo}/{entidad.id_priv}/{entidad.id_pub}'.encode('ascii')


def contexto_sesion(id_sesion):
    return f'iot2/sesion/{id_sesion}'.encode('ascii')


def obtener_llave_usuario(db, id_cliente, tipo='usuario'):
    from db.mysql.repositorio import RepositorioIdentidades
    entidad = RepositorioIdentidades(db).por_id(tipo, id_cliente)
    if entidad is None or not entidad.fila.activo or not entidad.llave:
        return None
    return ProtectorLlaves(config.maestra).abrir(entidad.llave, contexto_identidad(entidad))


def obtener_llave_sesion(id_sesion):
    from db.redis.session_repository import obtener_sesion
    registro = obtener_sesion(id_sesion)
    llave = registro.get('llave_sesion') if registro else None
    if llave is None:
        return None
    return ProtectorLlaves(config.maestra).abrir(llave, contexto_sesion(id_sesion))


def cifrar_login(db, id_cliente, pl, iv, tipo='usuario'):
    llave = obtener_llave_usuario(db, id_cliente, tipo)
    return None if llave is None else cifrar(llave, pl, iv)


def descifrar_login(db, id_cliente, pl_c, iv, tipo='usuario'):
    llave = obtener_llave_usuario(db, id_cliente, tipo)
    return None if llave is None else descifrar(llave, pl_c, iv)


def cifrar_generico(id_sesion, pl, iv):
    llave = obtener_llave_sesion(id_sesion)
    return None if llave is None else cifrar(llave, pl, iv)


def descifrar_generico(id_sesion, pl_c, iv):
    llave = obtener_llave_sesion(id_sesion)
    return None if llave is None else descifrar(llave, pl_c, iv)
