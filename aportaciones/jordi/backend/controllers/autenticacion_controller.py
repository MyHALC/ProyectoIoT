import hmac
import secrets
import time
from cryptography.exceptions import InvalidTag
from fastapi import HTTPException
from config import config
from db.mysql.repositorio import RepositorioIdentidades
from seguridad.sesiones import RepositorioSesiones
from seguridad.cifrado import descifrar_login, cifrar_login
from schemas.peticiones import LoginHmac, LoginReto
from seguridad.auditoria import Auditoria
from seguridad.confianza import Confianza, Contrasenas
from seguridad.protocolo import Protocolo


class AutenticacionController:
    @staticmethod
    def configuracion():
        datos = {'metodo': config.modo, 'servidor': config.servidor, 'version': 2}
        if config.modo == 'hmac':
            datos['epoca'] = RepositorioSesiones().epoca()
        return datos

    def reto(self, db, tipo, id_cliente):
        if config.modo != 'reto':
            raise HTTPException(409, detail='El servidor utiliza HMAC.')
        entidad = RepositorioIdentidades(db).por_id(tipo, id_cliente)
        try:
            Confianza.llave(entidad)
        except (ValueError, InvalidTag):
            raise HTTPException(401, detail='Identidad sin confianza vigente.') from None
        return RepositorioSesiones().emitir_reto(entidad)

    @staticmethod
    def huella(entidad):
        import hashlib
        return hashlib.sha256(entidad.llave.encode('ascii')).hexdigest()

    def iniciar(self, db, tipo, paquete):
        error = HTTPException(401, detail='Autenticación inválida, vencida o ya utilizada.')
        entidad = RepositorioIdentidades(db).por_id(tipo, paquete.id_cliente)
        sesiones = RepositorioSesiones()
        try:
            llave = Confianza.llave(entidad)
            datos = Protocolo.leer_json(descifrar_login(db, paquete.id_cliente, paquete.pl_c, paquete.iv, tipo))
            modelo = LoginReto if config.modo == 'reto' else LoginHmac
            pl = modelo.model_validate(datos)
            if pl.servidor != config.servidor or pl.tipo != tipo or pl.id_cliente != paquete.id_cliente:
                raise error
            if tipo == 'dispositivo' and pl.contrasena is not None:
                raise error
            if config.modo == 'reto':
                reto = pl.reto.model_dump()
                if (reto['id_cliente'] != entidad.id_pub or reto['tipo'] != tipo or
                        reto['servidor'] != config.servidor or reto['huella'] != self.huella(entidad)
                        or not sesiones.consumir_reto(reto)):
                    raise error
            else:
                mensaje = {k: v for k, v in datos.items() if k != 'firma'}
                if (abs(time.time() - pl.emitida) > config.hmac_ttl
                        or not hmac.compare_digest(pl.firma, Protocolo.firma(llave, tipo, mensaje))
                        or not sesiones.reservar_hmac(entidad, pl.nonce, pl.epoca)):
                    raise error
        except (ValueError, TypeError, KeyError, InvalidTag):
            raise error from None
        if tipo != 'dispositivo' and not Contrasenas.comprobar(pl.contrasena, entidad.seguridad.contrasena):
            raise HTTPException(401, detail='Usuario o contraseña incorrectos.')
        resultado = sesiones.crear(entidad, llave)
        iv = secrets.token_bytes(12)
        cifrado = cifrar_login(db, paquete.id_cliente, Protocolo.json(resultado), iv, tipo)
        if cifrado is None:
            raise error
        Auditoria.registrar('sesion_creada', metodo=config.modo, tipo=tipo, id_cliente=entidad.id_pub)
        return {'pl_c': Protocolo.base64(cifrado), 'iv': Protocolo.base64(iv)}
