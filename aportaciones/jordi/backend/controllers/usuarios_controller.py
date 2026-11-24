from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from config import config
from db.mysql.repositorio import RepositorioIdentidades
from db.redis.connection import redis_client
from seguridad.confianza import Confianza, Contrasenas


class UsuariosController:
    tipo = 'usuario'

    def registrar(self, datos, db, responsable=None):
        if self.tipo == 'administrador' and (responsable is None or responsable.tipo != 'administrador'):
            raise HTTPException(403, detail='Se requiere un administrador autorizado.')
        with redis_client.lock(config.prefijo + 'altas-personas', timeout=30, blocking_timeout=5):
            try:
                cuenta = RepositorioIdentidades(db).crear_persona(self.tipo, datos, Contrasenas.guardar(datos.contrasena))
                if responsable:
                    Confianza(db).establecer(cuenta, responsable)
                else:
                    db.commit()
                return cuenta.publica()
            except (ValueError, IntegrityError) as error:
                db.rollback()
                raise HTTPException(409, detail='No se pudo registrar: revisa el correo y el nombre de usuario.') from error

    @staticmethod
    def listar(db):
        return [entidad.publica() for entidad in RepositorioIdentidades(db).listar('usuario')]
