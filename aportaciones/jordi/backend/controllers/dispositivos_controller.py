from fastapi import HTTPException
from db.mysql.repositorio import RepositorioIdentidades
from seguridad.confianza import Confianza


class DispositivosController:
    def registrar(self, datos, db, responsable):
        if responsable.tipo != 'administrador':
            raise HTTPException(403, detail='Se requiere un administrador autorizado.')
        entidad = RepositorioIdentidades(db).crear_dispositivo(datos, responsable)
        Confianza(db).establecer(entidad, responsable)
        return entidad.publica()

    def listar(self, db):
        return [entidad.publica() for entidad in RepositorioIdentidades(db).listar('dispositivo')]
