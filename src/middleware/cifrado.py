'''
Modulo de cifrado con AES-GCM con cryptography
'''
import base64
import os
from dotenv import load_dotenv                                          # Cargar variables de entorno desde el archivo .env
from sqlalchemy import select
from db.mysql.models import Usuario, Contrasena
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from db.redis.connection import redis_client

load_dotenv()

TIEMPO_SESION = 1800 

'''
````````````````````Funciones micelaneas para uso general dentro del módulo de cifrado````````````````````
'''

def cifrar(llave, pl, iv):                                              # Cifra el texto plano usando AES-GCM con la llave y el IV proporcionados
    aesgcm = AESGCM(llave)
    texto_cifrado = aesgcm.encrypt(iv, pl, None)
    return texto_cifrado

def descifrar(llave, pl_c, iv):                                         # Descifra el texto cifrado usando AES-GCM con la llave y el IV proporcionados
    aesgcm = AESGCM(llave)
    pl = aesgcm.decrypt(iv, pl_c, None)
    return pl

def obtener_llave_usuario(db, id_cliente):                              # Obtiene la llave del usuario descifrada del usuario usando la llave maestra
    consulta = (
        select(Contrasena.llave_hmac_cifrada)                           # Selecciona en la tabla Contrasena la columna de la llave cifrada
        .join(Usuario, Usuario.id_priv == Contrasena.id_priv_usuario)   # Une Usuario con Contrasena: id_priv_usuario apunta al ID privado del usuario
        .where(Usuario.id_pub == id_cliente)                            # Filtra por el ID público del cliente
    )
    llave_usuario_guardada = db.scalar(consulta)                       # Ejecuta la consulta y obtiene la llave del usuario cifrada del usuario

    if llave_usuario_guardada is None:                                 # Si no se encuentra la llave del usuario cifrada, devuelve None
        return None

    llave_maestra = base64.b64decode(os.getenv("LLAVE_MAESTRA"))       # Decodifica la llave maestra desde base64
    llave_usuario_bytes = base64.b64decode(llave_usuario_guardada)     # Decodifica la llave del usuario cifrada desde base64
    iv = llave_usuario_bytes[:12]                                      # Extrae el vector de inicialización (IV) de los primeros 12 bytes
    llave_usuario_cifrada = llave_usuario_bytes[12:]                   # Extrae la parte cifrada de la llave del usuario

    llave_usuario = descifrar(llave_maestra, llave_usuario_cifrada, iv) # Descifra la llave del usuario usando la llave maestra y el IV
    return llave_usuario                                               # Devuelve la llave del usuario descifrada

def obtener_llave_sesion(id_sesion):
    llave_texto = redis_client.hget(f"sesion:{id_sesion}", "llave_sesion")  # hget obtiene el valor de un campo específico en un hash de Redis
    if llave_texto is None:
        return None
    return base64.b64decode(llave_texto)

'''
````````````````````Funciones para cifrar y descifrar datos de login y sesiones genéricas usando llaves de usuario y llaves de sesión.````````````````````
'''

def descifrar_login(db, id_cliente, pl_c, iv):
    sub = obtener_llave_usuario(db, id_cliente)
    if sub is None:
        return None
    return descifrar(sub, pl_c, iv)


def cifrar_login(db, id_cliente, pl, iv):
    sub = obtener_llave_usuario(db, id_cliente)
    if sub is None:
        return None
    return cifrar(sub, pl, iv)


def descifrar_generico(id_sesion, pl_c, iv):
    llave_sesion = obtener_llave_sesion(id_sesion)
    if llave_sesion is None:
        return None
    return descifrar(llave_sesion, pl_c, iv)


def cifrar_generico(id_sesion, pl, iv):
    llave_sesion = obtener_llave_sesion(id_sesion)
    if llave_sesion is None:
        return None
    return cifrar(llave_sesion, pl, iv)
