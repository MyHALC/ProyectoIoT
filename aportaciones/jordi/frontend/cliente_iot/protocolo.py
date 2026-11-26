import base64
import hashlib
import hmac
import json
import secrets
import time
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from .cifrado import cifrar, descifrar, decodificar


class Protocolo:
    servidor = 'iot-hogar-local-v1'
    tipos = {'usuario', 'administrador', 'dispositivo'}

    @staticmethod
    def json(datos):
        return json.dumps(datos, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('utf-8')

    @staticmethod
    def base64(datos):
        return base64.b64encode(datos).decode('ascii')

    @classmethod
    def paquete(cls, datos, llave, **identificador):
        iv = secrets.token_bytes(12)
        cuerpo = cifrar(llave, cls.json(datos), iv)
        return {**identificador, 'pl_c': cls.base64(cuerpo), 'iv': cls.base64(iv)}

    @classmethod
    def abrir(cls, paquete, llave):
        iv = base64.b64decode(paquete['iv'], validate=True)
        if len(iv) != 12:
            raise ValueError('IV inválido.')
        return cls.leer_json(descifrar(llave, base64.b64decode(paquete['pl_c'], validate=True), iv))

    @staticmethod
    def leer_json(cuerpo):
        datos = json.loads(cuerpo)
        if not isinstance(datos, dict):
            raise ValueError('Se requiere un objeto JSON.')
        return datos

    @classmethod
    def firma(cls, llave, tipo, mensaje):
        if tipo not in cls.tipos:
            raise ValueError('Tipo de identidad inválido.')
        info = cls.json(['IoT-Hogar/auth-hmac/v2', cls.servidor, tipo])
        llave_hmac = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info).derive(llave)
        return hmac.digest(llave_hmac, cls.json(mensaje), hashlib.sha256).hex()

    @classmethod
    def login(cls, identidad, tipo, config, contrasena=None, reto=None):
        if config.get('servidor') != cls.servidor or config.get('version') != 2 or config.get('metodo') not in ('reto', 'hmac'):
            raise ValueError('Configuración de autenticación incompatible.')
        publico = identidad['id_cliente']
        llave = decodificar(identidad['llave'])
        modo = config['metodo']
        datos = {'proposito': 'login', 'servidor': cls.servidor, 'id_cliente': publico, 'tipo': tipo, 'metodo': modo}
        if contrasena is not None:
            datos['contrasena'] = contrasena
        if modo == 'reto':
            if (not reto or reto['id_cliente'] != publico or reto['tipo'] != tipo or
                    reto['servidor'] != cls.servidor or reto['expira'] <= time.time()):
                raise ValueError('El reto no corresponde a esta identidad.')
            datos['reto'] = reto
        else:
            datos.update(nonce=secrets.token_hex(32), emitida=int(time.time()), epoca=config['epoca'])
            datos['firma'] = cls.firma(llave, tipo, datos)
        return cls.paquete(datos, llave, id_cliente=publico)

    @classmethod
    def abrir_sesion(cls, respuesta, identidad, tipo):
        datos = cls.abrir(respuesta, decodificar(identidad['llave']))
        if (datos['proposito'] != 'inicio-sesion' or datos['id_cliente'] != identidad['id_cliente']
                or datos['tipo'] != tipo or datos['servidor'] != cls.servidor or datos['expira'] <= time.time()):
            raise ValueError('Respuesta de sesión inválida.')
        decodificar(datos['llave_sesion'])
        return datos

    @classmethod
    def peticion(cls, sesion, accion, datos=None):
        if sesion['expira'] <= time.time():
            raise ValueError('Sesión vencida.')
        peticion_id = secrets.token_hex(24)
        plano = {'proposito': 'comunicacion', 'direccion': 'peticion', 'servidor': cls.servidor,
                 'id_cliente': sesion['id_cliente'], 'tipo': sesion['tipo'], 'id_sesion': sesion['id_sesion'],
                 'emitida': int(time.time()), 'peticion_id': peticion_id, 'accion': accion, 'datos': datos or {}}
        return cls.paquete(plano, decodificar(sesion['llave_sesion']), id_sesion=sesion['id_sesion']), peticion_id

    @classmethod
    def abrir_respuesta(cls, respuesta, sesion, peticion_id):
        datos = cls.abrir(respuesta, decodificar(sesion['llave_sesion']))
        if (datos['proposito'] != 'comunicacion' or datos['direccion'] != 'respuesta'
                or datos['servidor'] != cls.servidor or datos['id_sesion'] != sesion['id_sesion']
                or datos['id_cliente'] != sesion['id_cliente'] or datos['tipo'] != sesion['tipo']
                or datos['peticion_id'] != peticion_id):
            raise ValueError('La respuesta no corresponde a la petición.')
        return datos
