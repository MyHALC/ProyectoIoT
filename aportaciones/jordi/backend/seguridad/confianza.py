import hmac
import secrets
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from redis.exceptions import RedisError
from config import config
from seguridad.sesiones import RepositorioSesiones
from seguridad.cifrado import ProtectorLlaves, contexto_identidad, decodificar
from .almacen_llaves import AlmacenLlaves
from .auditoria import Auditoria
from .protocolo import Protocolo


class Contrasenas:
    hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1, salt_len=16, hash_len=32)

    @classmethod
    def guardar(cls, contrasena):
        return cls.hasher.hash(contrasena)

    @classmethod
    def comprobar(cls, contrasena, guardada):
        if not isinstance(contrasena, str) or not isinstance(guardada, str) or not guardada.startswith('$argon2id$'):
            return False
        try:
            return cls.hasher.verify(guardada, contrasena)
        except (VerificationError, InvalidHashError, TypeError):
            return False


class Confianza:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def llave(entidad):
        if entidad is None or not entidad.fila.activo or not entidad.llave:
            raise ValueError('La identidad no tiene confianza vigente.')
        return ProtectorLlaves(config.maestra).abrir(entidad.llave, contexto_identidad(entidad))

    @staticmethod
    def invalidar(entidad):
        try:
            RepositorioSesiones().invalidar(entidad)
        except RedisError:
            # La próxima petición vuelve a comprobar la llave y el estado en SQL.
            Auditoria.registrar('redis_invalidacion_pendiente', tipo=entidad.tipo, id_cliente=entidad.id_pub)

    def establecer(self, entidad, responsable=None, *, despliegue=False, llave=None):
        if despliegue:
            if entidad.tipo != 'administrador' or responsable is not None:
                raise ValueError('El despliegue solo establece al primer administrador.')
        else:
            if responsable is None or responsable.tipo != 'administrador':
                raise ValueError('Se requiere un administrador autorizado.')
            self.llave(responsable)
        if entidad.fila not in self.db:
            raise ValueError('La identidad debe pertenecer a la sesión SQL actual.')
        llave = secrets.token_bytes(32) if llave is None else llave
        protector = ProtectorLlaves(config.maestra)
        protegida = protector.proteger(llave, contexto_identidad(entidad))
        servidor = protector.abrir(protegida, contexto_identidad(entidad))
        identidad = {'id_cliente': entidad.id_pub, 'llave': Protocolo.base64(llave)}
        almacen = AlmacenLlaves(entidad.tipo)
        try:
            with almacen.instalar(entidad.alias(), identidad):
                for alias in entidad.alias():
                    cliente = decodificar(almacen.cargar(alias)['llave'])
                    for direccion, emisor, receptor in (('servidor', servidor, cliente), ('cliente', cliente, servidor)):
                        reto = {'proposito': 'alta', 'direccion': direccion, 'id_cliente': entidad.id_pub,
                                'tipo': entidad.tipo, 'nonce': secrets.token_hex(32)}
                        if Protocolo.abrir(Protocolo.paquete(reto, emisor), receptor) != reto:
                            raise ValueError('No se pudo verificar la llave del cliente.')
                entidad.seguridad.llave_hmac_cifrada = protegida
                entidad.fila.activo = 1
                self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
        self.invalidar(entidad)
        Auditoria.registrar('confianza_establecida', tipo=entidad.tipo, id_cliente=entidad.id_pub,
                           responsable=responsable.id_pub if responsable else None)

    def revocar(self, entidad, responsable):
        if responsable.tipo != 'administrador':
            raise ValueError('Se requiere un administrador autorizado.')
        self.llave(responsable)
        entidad.fila.activo = 0
        entidad.seguridad.llave_hmac_cifrada = None
        self.db.commit()
        self.invalidar(entidad)
        Auditoria.registrar('confianza_revocada', tipo=entidad.tipo, id_cliente=entidad.id_pub,
                           responsable=responsable.id_pub)
