import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from cryptography.exceptions import InvalidTag
from .almacen_llaves import AlmacenLlaves
from .protocolo import Protocolo


class ClienteBackend:
    rutas = {'usuario': ('usuarios', 'login'), 'administrador': ('administradores', 'login'),
             'dispositivo': ('dispositivos', 'autenticar')}
    rutas_telemetria = {'registrar_lectura': '/api/registros-iot/', 'ultima_lectura': '/api/registros-iot/ultimo'}

    def __init__(self, direccion=None):
        self.direccion = (direccion or os.getenv('BACKEND_URL', 'http://127.0.0.1:8000')).rstrip('/')

    def peticion(self, ruta, datos=None):
        cuerpo = Protocolo.json(datos) if datos is not None else None
        req = Request(self.direccion + ruta, data=cuerpo, headers={'Content-Type': 'application/json'})
        try:
            with urlopen(req, timeout=6) as respuesta:
                return True, json.load(respuesta)
        except HTTPError as error:
            try:
                detalle = json.load(error).get('detail')
                return False, detalle if isinstance(detalle, str) else 'Revisa los datos enviados.'
            except (ValueError, AttributeError):
                return False, 'El backend no aceptó la solicitud.'
        except (URLError, TimeoutError, ValueError):
            return False, 'No se pudo comunicar con el backend.'

    def iniciar(self, tipo, alias, contrasena=None):
        try:
            identidad = AlmacenLlaves(tipo).cargar(alias)
            if not identidad:
                return False, 'Esta identidad no está vinculada a este cliente.'
            ok, config = self.peticion('/api/autenticacion/configuracion/')
            if not ok:
                return False, config
            grupo, ruta = self.rutas[tipo]
            reto = None
            if config['metodo'] == 'reto':
                ok, reto = self.peticion(f'/api/{grupo}/reto/', {'id_cliente': identidad['id_cliente']})
                if not ok:
                    return False, reto
            paquete = Protocolo.login(identidad, tipo, config, contrasena, reto)
            ok, respuesta = self.peticion(f'/api/{grupo}/{ruta}/', paquete)
            if not ok:
                return False, respuesta
            Protocolo.abrir_sesion(respuesta, identidad, tipo)
            return True, {'inicio': respuesta, 'alias': alias, 'tipo': tipo}
        except (ValueError, OSError, KeyError, TypeError, InvalidTag):
            return False, 'No se pudo preparar la autenticación. Revisa la vinculación y la llave local.'

    def comunicar(self, token, accion, datos=None):
        try:
            identidad = AlmacenLlaves(token['tipo']).cargar(token['alias'])
            sesion = Protocolo.abrir_sesion(token['inicio'], identidad, token['tipo'])
            paquete, pid = Protocolo.peticion(sesion, accion, datos)
            ruta = self.rutas_telemetria.get(accion, '/api/comunicacion/')
            ok, respuesta = self.peticion(ruta, paquete)
            if not ok:
                return False, respuesta
            salida = Protocolo.abrir_respuesta(respuesta, sesion, pid)
            return salida['ok'], salida['resultado']
        except (ValueError, OSError, KeyError, TypeError, InvalidTag):
            return False, 'Sesión inválida o vencida.'
