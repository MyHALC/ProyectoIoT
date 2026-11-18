from typing import Annotated

from fastapi import APIRouter, Query

from controllers.registros_iot_controller import (
    verificar_conexion_mongo,
    registrar_datos_iot,
    obtener_ultimo_registro
)

from schemas.registro_iot_schema import (
    RegistroIoTEntrada,
    RegistroIoTConsulta,
    RegistroIoTResponse,
    MongoConexionResponse
)


router = APIRouter()


# ===============================
# VERIFICAR CONEXIÓN
# ===============================

@router.get(
    "/conexion",
    response_model=MongoConexionResponse
)
def consultar_conexion():

    return verificar_conexion_mongo()


# ===============================
# REGISTRAR DATOS
# ===============================

@router.post(
    "/",
    response_model=RegistroIoTResponse,
    status_code=201
)
def crear_registro(
    datos: RegistroIoTEntrada
):

    return registrar_datos_iot(datos)


# ===============================
# CONSULTAR ÚLTIMO REGISTRO
# ===============================

@router.get(
    "/ultimo",
    response_model=RegistroIoTResponse
)
def consultar_ultimo_registro(
    datos: Annotated[
        RegistroIoTConsulta,
        Query()
    ]
):

    return obtener_ultimo_registro(datos)