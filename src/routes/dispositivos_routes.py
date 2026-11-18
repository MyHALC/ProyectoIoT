from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.mysql.connection import obtener_db

from controllers.dispositivos_controller import (
    dispositivos_controller
)

from schemas.dispositivo_schema import (
    DispositivoRegistroRequest,
    DispositivoConsultaID,
    DispositivoConsultaAdministrador,
    DispositivoListado,
    DispositivoResponse,
    DispositivoRegistroResponse
)


router = APIRouter()


# ============================
# REGISTRAR DISPOSITIVO
# ============================

@router.post(
    "/registro/",
    status_code=201,
    response_model=DispositivoRegistroResponse
)
def registrar_dispositivo(
    datos: DispositivoRegistroRequest,
    db: Session = Depends(obtener_db)
):

    return dispositivos_controller.registrar_dispositivo(
        datos, db
    )


# ============================
# CONSULTAR POR ID
# ============================

@router.get(
    "/por-id",
    response_model=DispositivoResponse
)
def consultar_dispositivo(
    datos: Annotated[
        DispositivoConsultaID,
        Query()
    ],
    db: Session = Depends(obtener_db)
):

    return dispositivos_controller.obtener_dispositivo_por_id(
        datos, db
    )


# ============================
# CONSULTAR POR ADMINISTRADOR
# ============================

@router.get(
    "/por-administrador",
    response_model=list[DispositivoResponse]
)
def consultar_dispositivos_administrador(
    datos: Annotated[
        DispositivoConsultaAdministrador,
        Query()
    ],
    db: Session = Depends(obtener_db)
):

    return dispositivos_controller.obtener_dispositivos_administrador(
        datos, db
    )


# ============================
# LISTAR DISPOSITIVOS
# ============================

@router.get(
    "/",
    response_model=list[DispositivoResponse]
)
def listar_dispositivos(
    datos: Annotated[
        DispositivoListado,
        Query()
    ],
    db: Session = Depends(obtener_db)
):

    return dispositivos_controller.listar_dispositivos(
        datos, db
    )