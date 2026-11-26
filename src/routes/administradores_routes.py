from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.mysql.connection import obtener_db

from controllers.administradores_controller import (
    administradores_controller
)

from schemas.administrador_schema import (
    AdministradorRegistroRequest,
    AdministradorLoginRequest,
    AdministradorConsultaCorreo,
    AdministradorListado,
    AdministradorResponse,
    AdministradorLoginResponse
)

from fastapi import Response

from db.redis.session_repository import (
    SESSION_COOKIE,
    SESSION_TTL,
    COOKIE_PATH,
    COOKIE_SECURE
)

router = APIRouter()

# REGISTRO

@router.post(
    "/registro/",
    status_code=201,
    response_model=AdministradorResponse
)
def crear_administrador(
    datos: AdministradorRegistroRequest,
    db: Session = Depends(obtener_db)
):
    return administradores_controller.crear_administrador(
        datos, db
    )

# LOGIN DE ADMINISTRADOR

@router.post(
    "/login/",
    response_model=AdministradorLoginResponse
)
def validar_administrador(
    datos: AdministradorLoginRequest,
    response: Response,
    db: Session = Depends(obtener_db)
):

    resultado, session_id = (
        administradores_controller.validar_administrador(
            datos, db
        )
    )

    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_id,
        max_age=SESSION_TTL,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path=COOKIE_PATH
    )

    return resultado

# CONSULTAR POR CORREO

@router.get(
    "/por-correo",
    response_model=AdministradorResponse
)
def consultar_administrador(
    datos: Annotated[
        AdministradorConsultaCorreo,
        Query()
    ],
    db: Session = Depends(obtener_db)
):
    return administradores_controller.obtener_administrador_por_correo(
        datos, db
    )

# LISTAR ADMINISTRADORES

@router.get(
    "/",
    response_model=list[AdministradorResponse]
)
def listar_administradores(
    datos: Annotated[
        AdministradorListado,
        Query()
    ],
    db: Session = Depends(obtener_db)
):
    return administradores_controller.listar_administradores(
        datos, db
    )