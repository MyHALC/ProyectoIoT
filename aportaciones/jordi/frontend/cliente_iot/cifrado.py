import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def cifrar(llave, pl, iv, aad=None):
    aesgcm = AESGCM(llave)
    return aesgcm.encrypt(iv, pl, aad)


def descifrar(llave, pl_c, iv, aad=None):
    aesgcm = AESGCM(llave)
    return aesgcm.decrypt(iv, pl_c, aad)


def decodificar(llave):
    datos = base64.b64decode(llave, altchars=b'-_', validate=True)
    if len(datos) != 32:
        raise ValueError('La llave debe tener 32 bytes.')
    return datos
