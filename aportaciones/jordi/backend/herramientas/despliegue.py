if __package__ in (None, ''):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import secrets
from cryptography.exceptions import InvalidTag
from dotenv import set_key
from sqlalchemy import delete, func, select, text, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from pydantic import ValidationError
from config import config
from db.comprobaciones import comprobar_redis, error_mariadb
from db.sql import obtener_engine
from db.mysql.esquema import EsquemaIoT2
from db.mysql.models import Administrador, Contrasena, Correo, DispositivoRegistrado, DispositivoSeguridad
from db.mysql.repositorio import RepositorioIdentidades
from seguridad.cifrado import ProtectorLlaves, contexto_identidad
from seguridad.almacen_llaves import AlmacenLlaves
from seguridad.confianza import Confianza, Contrasenas
from seguridad.protocolo import Protocolo
from herramientas.comun import Consola


class Despliegue:
    @staticmethod
    def validar_llave_maestra(db):
        """Comprueba que la llave sirva para abrir los secretos ya guardados."""
        guardadas = 0
        for tabla in (Contrasena, DispositivoSeguridad):
            consulta = select(func.count()).select_from(tabla)
            consulta = consulta.where(tabla.llave_hmac_cifrada.is_not(None))
            guardadas += db.scalar(consulta)

        if not config.maestra:
            hay_administrador = db.scalar(select(Administrador.id_priv).limit(1))
            if guardadas > 0 or hay_administrador is not None:
                raise ValueError('Falta la llave maestra de esta instalación. Recupera la original; no se generó otra.')
            return 0
        try:
            protector = ProtectorLlaves(config.maestra)
            comprobadas = 0
            repo = RepositorioIdentidades(db)
            for tipo in ('usuario', 'administrador', 'dispositivo'):
                for entidad in repo.listar(tipo):
                    if entidad.llave:
                        protector.abrir(entidad.llave, contexto_identidad(entidad))
                        comprobadas += 1
        except (ValueError, InvalidTag):
            raise ValueError(
                'La llave maestra tiene formato incorrecto, no corresponde a esta instancia '
                'o hay una llave cifrada dañada. No se cambió ninguna llave.'
            ) from None
        if comprobadas != guardadas:
            raise ValueError('Existen llaves sin una identidad completa. Revisa la base antes de reinstalar.')
        return comprobadas

    @staticmethod
    def administrador_master(db):
        """Busca la cuenta que tiene el indicador de instalación."""
        consulta = select(Administrador).where(Administrador.instalacion_asegurada.is_not(None))
        filas = list(db.scalars(consulta))

        if len(filas) > 1:
            raise ValueError('El indicador de instalación es inconsistente; no se modificó la instancia.')
        if not filas:
            if db.scalar(select(Administrador.id_priv).limit(1)) is not None:
                raise ValueError('Hay administradores sin identificar al máster. Debe asignarse el indicador a su cuenta existente.')
            return None

        if filas[0].instalacion_asegurada not in (0, 1):
            raise ValueError('El indicador de instalación es inconsistente; no se modificó la instancia.')
        master = RepositorioIdentidades(db).componer('administrador', filas[0])
        if master is None:
            raise ValueError('El administrador máster tiene datos incompletos; no se modificó la instancia.')
        return master

    @staticmethod
    def _copiar_llaves_master(master):
        """Lee sus archivos para poder recuperarlos si el reemplazo falla."""
        almacen = AlmacenLlaves('administrador')
        copias = {}
        for alias in master.alias():
            identidad = almacen.cargar(alias)
            if identidad and identidad['id_cliente'] == master.id_pub:
                ruta = almacen.ruta(alias)
                copias[ruta] = ruta.read_bytes()
        return copias

    def _crear_master(self, db, datos=None):
        """Instalación nueva: pide los datos y  prepara la llave y crea la cuenta."""
        if datos is None:
            datos = Consola.datos_persona()

        if not config.maestra:
            config.maestra = Protocolo.base64(secrets.token_bytes(32))
            set_key(str(config.archivo), 'LLAVE_MAESTRA', config.maestra, quote_mode='never')

        repo = RepositorioIdentidades(db)
        contrasena_protegida = Contrasenas.guardar(datos.contrasena)
        admin = repo.crear_persona('administrador', datos, contrasena_protegida)
        admin.fila.instalacion_asegurada = 1
        Confianza(db).establecer(admin, despliegue=True)
        print('Administrador máster creado y vinculado. Identificador público:', admin.id_pub)
        return admin.id_pub

    def reinstalar(self, db, master):
        """Pide autorizacin y permite conservar o reemplazar al máster."""
        if master.fila.instalacion_asegurada != 0:
            raise ValueError('La instalación está asegurada. No se permite reinstalar.')
        responsable = Consola.administrador(db)
        if responsable.id_priv != master.id_priv:
            raise ValueError('Solo el administrador máster puede autorizar esta reinstalación.')
        respuesta = input('¿Conservar los datos del administrador máster? [S/n]: ').strip().lower()
        if respuesta in ('', 's', 'si', 'sí'):
            master.fila.instalacion_asegurada = 1
            db.commit()
            print('Datos y llaves conservados. Instalación asegurada.')
            return None
        if respuesta not in ('n', 'no'):
            print('Operación cancelada. No se modificaron los datos.')
            return None
        print('Se reemplazará solo al máster. Las otras cuentas, dispositivos y la llave maestra se conservan.')
        datos = Consola.datos_persona()
        if input('Escribe REEMPLAZAR para confirmar el nuevo administrador máster: ').strip() != 'REEMPLAZAR':
            print('Operación cancelada. No se modificaron los datos.')
            return None
        return self._reemplazar_master(db, master, datos)

    def _reemplazar_master(self, db, master, datos):
        """Reemplaza la cuenta y recupera los datos anteriores si falla."""
        copias = self._copiar_llaves_master(master)
        try:
            # Permite reutilizar el correo y usuario del máster anterior.
            for ruta in copias:
                ruta.unlink()
            db.execute(delete(Correo).where(Correo.id_priv_admin == master.id_priv))
            db.execute(delete(Contrasena).where(Contrasena.id_priv_admin == master.id_priv))
            repo = RepositorioIdentidades(db)
            contrasena_protegida = Contrasenas.guardar(datos.contrasena)
            nuevo = repo.crear_persona('administrador', datos, contrasena_protegida)
            nuevo.fila.instalacion_asegurada = 1
            # Los dispositivos siguen registrados al máster que administra la instalación.
            db.execute(update(DispositivoRegistrado).where(DispositivoRegistrado.id_priv_admin == master.id_priv)
                       .values(id_priv_admin=nuevo.id_priv))
            db.delete(master.fila)
            db.flush()
            Confianza(db).establecer(nuevo, despliegue=True)
        except BaseException:
            # rollback recupera SQL; las copias recuperan sus archivos locales.
            db.rollback()
            if db.get(Administrador, master.id_priv) is not None:
                almacen = AlmacenLlaves('administrador')
                for ruta, contenido in copias.items():
                    almacen.escribir(ruta, contenido)
            raise
        Confianza.invalidar(master)
        print('Administrador máster reemplazado y vinculado. Instalación asegurada. Identificador público:', nuevo.id_pub)
        return nuevo.id_pub

    def _revisar_instalacion(self, db, datos=None, interactivo=False):
        """Decide entre instalación nueva, bloqueo y reinstalación autorizada."""
        master = self.administrador_master(db)
        comprobadas = self.validar_llave_maestra(db)
        if comprobadas > 0:
            print('Llave maestra válida: se comprobaron las llaves cifradas de esta instancia.')

        if master is None:
            comprobar_redis()
            return self._crear_master(db, datos)

        if master.fila.instalacion_asegurada == 1:
            print('La instalación está asegurada. No se permite reinstalar. El proceso termina.')
            return None

        comprobar_redis()
        if interactivo:
            return self.reinstalar(db, master)

        print('La instalación permite revisión. Ejecuta la herramienta en la terminal para autorizarla.')
        return None

    def ejecutar(self, datos=None, *, interactivo=False):
        """Abre MariaDB y evita dos despliegues simultáneos."""
        engine = obtener_engine()
        nombre_lock = 'despliegue:' + config.bd
        with engine.connect() as conn:
            if conn.scalar(text('SELECT GET_LOCK(:nombre, 10)'), {'nombre': nombre_lock}) != 1:
                raise RuntimeError('Otro despliegue está en curso.')
            conn.commit()
            try:
                EsquemaIoT2(engine).preparar()
                with Session(bind=conn, expire_on_commit=False) as db:
                    return self._revisar_instalacion(db, datos, interactivo)
            finally:
                conn.execute(text('SELECT RELEASE_LOCK(:nombre)'), {'nombre': nombre_lock})
                conn.commit()


if __name__ == '__main__':
    try:
        Despliegue().ejecutar(interactivo=True)
    except ValidationError:
        raise SystemExit('Revisa los datos ingresados y la longitud de los campos.') from None
    except OperationalError as error:
        raise SystemExit(f'MariaDB: {error_mariadb(error)}') from None
    except (ValueError, RuntimeError) as error:
        raise SystemExit(str(error)) from None
