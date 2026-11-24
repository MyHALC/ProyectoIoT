from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


Tipo = Literal['usuario', 'administrador', 'dispositivo']


class ModeloEstricto(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class SolicitudReto(ModeloEstricto):
    id_cliente: int = Field(ge=1, le=4294967295)


class Reto(ModeloEstricto):
    reto_id: str = Field(pattern=r'^[0-9a-f]{48}$')
    nonce: str = Field(pattern=r'^[0-9a-f]{64}$')
    id_cliente: int = Field(ge=1, le=4294967295)
    tipo: Tipo
    servidor: str
    epoca: str = Field(max_length=120)
    huella: str = Field(pattern=r'^[0-9a-f]{64}$')
    expira: int


class LoginBase(ModeloEstricto):
    proposito: Literal['login']
    servidor: str
    id_cliente: int = Field(ge=1, le=4294967295)
    tipo: Tipo
    contrasena: str | None = Field(default=None, min_length=1, max_length=128)


class LoginReto(LoginBase):
    metodo: Literal['reto']
    reto: Reto


class LoginHmac(LoginBase):
    metodo: Literal['hmac']
    nonce: str = Field(pattern=r'^[0-9a-f]{64}$')
    emitida: int
    epoca: str = Field(max_length=120)
    firma: str = Field(pattern=r'^[0-9a-f]{64}$')


class PeticionSesion(ModeloEstricto):
    proposito: Literal['comunicacion']
    direccion: Literal['peticion']
    servidor: str
    id_cliente: int = Field(ge=1, le=4294967295)
    tipo: Tipo
    id_sesion: str = Field(pattern=r'^[A-Za-z0-9_-]{43}$')
    emitida: int
    peticion_id: str = Field(pattern=r'^[0-9a-f]{48}$')
    accion: Literal['perfil', 'usuarios', 'eco', 'salir', 'sesion_actual', 'registrar_dispositivo',
                    'registrar_administrador', 'dispositivos', 'registrar_lectura', 'ultima_lectura']
    datos: dict = Field(default_factory=dict)
