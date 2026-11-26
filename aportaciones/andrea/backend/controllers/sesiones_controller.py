import hashlib
import hmac
import secrets
import time
from cryptography.exceptions import InvalidTag
from fastapi import HTTPException
from config import config
from db.mysql.repositorio import RepositorioIdentidades
from seguridad.sesiones import RepositorioSesiones
from seguridad.cifrado import cifrar_generico, descifrar_generico
from schemas.identidad import RegistroDispositivo, RegistroPersona
from schemas.peticiones import PeticionSesion
from seguridad.auditoria import Auditoria
from seguridad.confianza import Confianza
from seguridad.protocolo import Protocolo
from .administradores_controller import AdministradoresController
from .dispositivos_controller import DispositivosController
from .registros_iot_controller import RegistrosIoTController
from .usuarios_controller import UsuariosController


class SesionesController:
    def comunicar(self, paquete, db, accion_requerida=None):
        #Busca la sesión, valida la petición, ejecuta y devuelve la respuesta cifrada.
        repo = RepositorioSesiones()
        id_sesion = paquete.id_sesion
        sesion = repo.obtener(id_sesion)
        if sesion is None:
            raise HTTPException(401, detail='Sesión inválida o vencida.')

        entidad, peticion = self._abrir_peticion(paquete, sesion, db, accion_requerida)
        self._registrar_peticion(repo, id_sesion, peticion, sesion)

        try:
            ok, resultado = self.operar(peticion, entidad, db, sesion)
        except ValueError:
            ok = False
            resultado = 'Los datos de la operación no son válidos.'

        # Cifrar antes de cerrar: el cierre retira la llave de sesión de Redis.
        respuesta = self._cifrar_respuesta(id_sesion, peticion, entidad, ok, resultado)
        if peticion.accion == 'salir':
            repo.cerrar(id_sesion, sesion)
            Auditoria.registrar('sesion_cerrada', tipo=entidad.tipo, id_cliente=entidad.id_pub)
        Auditoria.registrar('operacion', tipo=entidad.tipo, id_cliente=entidad.id_pub,
                           accion=peticion.accion, ok=ok)
        return respuesta

    @staticmethod
    def _abrir_peticion(paquete, sesion, db, accion_requerida):
        """Comprueba la identidad y descifra los datos antes de aceptarlos."""
        error = HTTPException(401, detail='Petición cifrada inválida.')
        try:
            repo_identidades = RepositorioIdentidades(db)
            entidad = repo_identidades.por_id(sesion['tipo'], int(sesion['id_cliente']))
            llave = Confianza.llave(entidad)
            huella_actual = hashlib.sha256(llave).hexdigest()

            if entidad.id_priv != int(sesion['id_priv']):
                raise error
            if not hmac.compare_digest(huella_actual, sesion['huella']):
                raise error

            contenido = descifrar_generico(paquete.id_sesion, paquete.pl_c, paquete.iv)
            datos = Protocolo.leer_json(contenido)
            peticion = PeticionSesion.model_validate(datos)

            if peticion.id_sesion != paquete.id_sesion:
                raise error
            if peticion.servidor != config.servidor:
                raise error
            if peticion.id_cliente != entidad.id_pub:
                raise error
            if peticion.tipo != entidad.tipo:
                raise error
            if abs(time.time() - peticion.emitida) > 60:
                raise error
            if accion_requerida and peticion.accion != accion_requerida:
                raise error
        except (ValueError, TypeError, KeyError, InvalidTag):
            raise error from None
        return entidad, peticion

    @staticmethod
    def _registrar_peticion(repo, id_sesion, peticion, sesion):
        """Solo deja ejecutar una vez cada identificador de petición."""
        estado = repo.consumir_peticion(id_sesion, peticion.peticion_id, sesion['epoca'])
        if estado == 0:
            raise HTTPException(409, detail='Petición ya utilizada.')
        if estado < 0:
            raise HTTPException(401, detail='Sesión vencida.')

    @staticmethod
    def _cifrar_respuesta(id_sesion, peticion, entidad, ok, resultado):
        respuesta = {
            'proposito': 'comunicacion',
            'direccion': 'respuesta',
            'servidor': config.servidor,
            'id_sesion': id_sesion,
            'id_cliente': entidad.id_pub,
            'tipo': entidad.tipo,
            'peticion_id': peticion.peticion_id,
            'ok': ok,
            'resultado': resultado,
        }
        iv = secrets.token_bytes(12)
        cifrado = cifrar_generico(id_sesion, Protocolo.json(respuesta), iv)
        if cifrado is None:
            raise HTTPException(401, detail='Sesión inválida o vencida.')
        return {'pl_c': Protocolo.base64(cifrado), 'iv': Protocolo.base64(iv)}

    def operar(self, pl, entidad, db, registro):
        """Mantiene los permisos de cada acción y delega en su controlador."""
        peticion = pl
        accion = peticion.accion
        datos = peticion.datos
        if accion == 'registrar_lectura':
            return True, RegistrosIoTController.registrar(datos, entidad)
        if accion == 'ultima_lectura':
            return True, RegistrosIoTController.ultima(datos, entidad, db)
        if accion == 'eco':
            return True, datos
        if accion == 'salir':
            return True, {'mensaje': 'Sesión cerrada.'}
        if accion == 'sesion_actual':
            return True, {'tipo': entidad.tipo, 'id_pub': entidad.id_pub, 'expira': int(registro['expira'])}
        if accion == 'perfil' and entidad.tipo != 'dispositivo':
            return True, entidad.publica()
        if entidad.tipo != 'administrador':
            return False, 'Operación no autorizada.'

        if accion == 'usuarios':
            return True, UsuariosController.listar(db)
        if accion == 'dispositivos':
            return True, DispositivosController().listar(db)
        if accion == 'registrar_dispositivo':
            registro_dispositivo = RegistroDispositivo.model_validate(datos)
            return True, DispositivosController().registrar(registro_dispositivo, db, entidad)
        if accion == 'registrar_administrador':
            registro_persona = RegistroPersona.model_validate(datos)
            return True, AdministradoresController().registrar(registro_persona, db, entidad)
        return False, 'Operación no autorizada.'
