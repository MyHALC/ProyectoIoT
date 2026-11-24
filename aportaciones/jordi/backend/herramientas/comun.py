from getpass import getpass
from cryptography.exceptions import InvalidTag
from db.mysql.repositorio import RepositorioIdentidades
from schemas.identidad import RegistroPersona
from seguridad.confianza import Confianza, Contrasenas


class Consola:
    @staticmethod
    def datos_persona():
        nombre = input('Nombre: ').strip()
        apellido = input('Apellido: ').strip()
        usuario = input('Nombre de usuario: ').strip()
        correo = input('Correo: ').strip()
        clave = getpass('Contraseña: ')
        if clave != getpass('Repite la contraseña: '):
            raise ValueError('Las contraseñas no coinciden.')
        return RegistroPersona(nombre=nombre, apellido=apellido, usuario=usuario or None,
                               correo=correo, contrasena=clave)

    @staticmethod
    def administrador(db):
        alias = input('Administrador responsable (correo o usuario): ').strip()
        clave = getpass('Contraseña del administrador: ')
        entidad = RepositorioIdentidades(db).buscar_persona('administrador', alias)
        try:
            Confianza.llave(entidad)
        except (ValueError, InvalidTag):
            raise ValueError('Administrador o contraseña incorrectos.') from None
        if not Contrasenas.comprobar(clave, entidad.seguridad.contrasena):
            raise ValueError('Administrador o contraseña incorrectos.')
        return entidad
