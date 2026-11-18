from datetime import datetime, timezone

from fastapi import HTTPException

from mongoengine.connection import get_db, ConnectionFailure
from mongoengine.errors import ValidationError, OperationError
from pymongo.errors import PyMongoError

from db.mongodb.connection import (
    MONGO_ALIAS,
    MONGO_COLECCION,
    conectar_mongodb
)

from db.mongodb.models import RegistroIoT

from schemas.registro_iot_schema import (
    RegistroIoTEntrada,
    RegistroIoTConsulta,
    RegistroIoTResponse,
    MongoConexionResponse
)


# ===============================
# CONVERTIR MODELO A RESPUESTA
# ===============================

def convertir_respuesta(
    registro: RegistroIoT
) -> RegistroIoTResponse:

    return RegistroIoTResponse(
        id=str(registro.id),
        id_priv_dispositivo=registro.id_priv_dispositivo,
        fecha_generacion=registro.fecha_generacion,
        fecha_recepcion=registro.fecha_recepcion,
        payload=dict(registro.payload)
    )


# ===============================
# VERIFICAR CONEXIÓN
# ===============================

def verificar_conexion_mongo() -> MongoConexionResponse:

    try:
        cliente = conectar_mongodb()

        cliente.admin.command("ping")

        db = get_db(alias=MONGO_ALIAS)

        colecciones = list(
            db.list_collections(
                filter={"name": MONGO_COLECCION}
            )
        )

    except (PyMongoError, ConnectionFailure) as error:
        raise HTTPException(
            status_code=503,
            detail="No se pudo conectar con MongoDB"
        ) from error

    if not colecciones:
        raise HTTPException(
            status_code=503,
            detail="La colección registros_iot no existe"
        )

    opciones = colecciones[0].get("options", {})
    timeseries = opciones.get("timeseries", {})

    if (
            timeseries.get("timeField") != "fecha_generacion"
            or timeseries.get("metaField") != "id_priv_dispositivo"
    ):
        raise HTTPException(
            status_code=503,
            detail="La colección no tiene la configuración Time Series esperada"
        )

    return MongoConexionResponse(
        estado="conectada",
        base_datos=db.name,
        coleccion=MONGO_COLECCION,
        tipo="timeseries"
    )


# ===============================
# REGISTRAR LECTURA
# ===============================

def registrar_datos_iot(
    datos: RegistroIoTEntrada
) -> RegistroIoTResponse:

    # Comprobar conexión y colección
    verificar_conexion_mongo()

    # Crear el documento ODM
    registro = RegistroIoT(
        id_priv_dispositivo=datos.id_priv_dispositivo,
        fecha_generacion=datos.fecha_generacion,
        fecha_recepcion=datetime.now(timezone.utc),
        payload=datos.payload
    )

    try:
        # Insertar nuevo registro, sin actualizar otros
        registro.save(force_insert=True)

    except ValidationError as error:
        raise HTTPException(
            status_code=422,
            detail="El documento IoT no es válido"
        ) from error

    except (PyMongoError, OperationError) as error:
        raise HTTPException(
            status_code=503,
            detail="No se pudo guardar el registro IoT"
        ) from error

    return convertir_respuesta(registro)


# ===============================
# OBTENER ÚLTIMO REGISTRO
# ===============================

def obtener_ultimo_registro(
    datos: RegistroIoTConsulta
) -> RegistroIoTResponse:

    verificar_conexion_mongo()

    try:
        registro = (
            RegistroIoT.objects(
                id_priv_dispositivo=datos.id_priv_dispositivo
            )
            .order_by("-fecha_recepcion")
            .first()
        )

    except (PyMongoError, OperationError) as error:
        raise HTTPException(
            status_code=503,
            detail="No se pudo consultar MongoDB"
        ) from error

    if registro is None:
        raise HTTPException(
            status_code=404,
            detail="No existen registros para ese dispositivo"
        )

    return convertir_respuesta(registro)