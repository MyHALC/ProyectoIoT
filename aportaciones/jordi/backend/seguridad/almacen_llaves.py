from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import secrets
from seguridad.cifrado import cifrar_con_contexto, descifrar_con_contexto, decodificar
from .protocolo import Protocolo
import base64


class AlmacenLlaves:
    def __init__(self, tipo):
        if tipo not in Protocolo.tipos:
            raise ValueError('Tipo de almacén inválido.')
        self.tipo = tipo
        raiz = Path(__file__).resolve().parents[2]
        base = os.getenv('IOT_CLIENTE_DIR')
        self.carpeta = Path(base) / tipo if base else raiz / (
            'privado_dispositivos_iot2' if tipo == 'dispositivo' else 'frontend/privado_iot2')

    def contexto(self, alias):
        if not isinstance(alias, str) or not alias.strip():
            raise ValueError('Identificador vacío.')
        return f'iot2/cliente/{self.tipo}/{alias.strip().lower()}'.encode('utf-8')

    def ruta(self, alias):
        return self.carpeta / (hashlib.sha256(self.contexto(alias)).hexdigest() + '.json')

    @staticmethod
    def escribir(ruta, contenido):
        temporal = ruta.with_suffix('.' + secrets.token_hex(8) + '.tmp')
        try:
            fd = os.open(temporal, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as salida:
                salida.write(contenido)
            os.replace(temporal, ruta)
        finally:
            temporal.unlink(missing_ok=True)

    def maestra(self, crear=False):
        ruta = self.carpeta / 'maestra.key'
        if crear:
            self.carpeta.mkdir(parents=True, exist_ok=True, mode=0o700)
            if not ruta.exists() and any(self.carpeta.glob('*.json')):
                raise ValueError('Falta la llave maestra del almacén local existente.')
            if not ruta.exists():
                try:
                    with os.fdopen(os.open(ruta, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as archivo:
                        archivo.write(base64.b64encode(secrets.token_bytes(32)))
                except FileExistsError:
                    pass
        return decodificar(ruta.read_bytes())

    def cargar(self, alias):
        ruta = self.ruta(alias)
        if not ruta.is_file():
            return None
        datos = json.loads(ruta.read_text(encoding='utf-8'))
        if datos['version'] != 2:
            raise ValueError('Versión de almacén desconocida.')
        plano = descifrar_con_contexto(self.maestra(), base64.b64decode(datos['pl_c'], validate=True),
                          base64.b64decode(datos['iv'], validate=True), self.contexto(alias))
        identidad = Protocolo.leer_json(plano)
        decodificar(identidad['llave'])
        return identidad

    @contextmanager
    def instalar(self, aliases, identidad):
        llave = self.maestra(crear=True)
        anteriores = {}
        try:
            for alias in sorted({a.strip().lower() for a in aliases if a}):
                ruta = self.ruta(alias)
                prev = self.cargar(alias)
                if prev and prev['id_cliente'] != identidad['id_cliente']:
                    raise ValueError('El alias local pertenece a otra identidad.')
                anteriores[ruta] = ruta.read_bytes() if ruta.exists() else None
                iv = secrets.token_bytes(12)
                plano = Protocolo.json(identidad)
                paquete = {'version': 2, 'iv': Protocolo.base64(iv),
                           'pl_c': Protocolo.base64(cifrar_con_contexto(llave, plano, iv, self.contexto(alias)))}
                self.escribir(ruta, Protocolo.json(paquete))
            yield
        except BaseException:
            for ruta, anterior in anteriores.items():
                if anterior is None:
                    ruta.unlink(missing_ok=True)
                else:
                    self.escribir(ruta, anterior)
            raise
