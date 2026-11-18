from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.mysql.connection import obtener_db

from controllers.usuarios_controller import (
    usuarios_controller
)

from schemas.usuario_schema import (
    RegistroRequest,
    LoginRequest,
    UsuarioConsultaCorreo,
    UsuarioListado,
    UsuarioResponse,
    LoginRespuesta
)

from fastapi import Response

from db.redis.session_repository import (
    SESSION_COOKIE,
    SESSION_TTL,
    COOKIE_PATH,
    COOKIE_SECURE
)

router = APIRouter()


# ============================
# REGISTRO
# ============================

@router.post(
    "/registro/",
    status_code=201,
    response_model=UsuarioResponse
)
def crear_usuario(
    datos: RegistroRequest,
    db: Session = Depends(obtener_db)
):
    return usuarios_controller.crear_usuario(
        datos, db
    )


# ============================
# LOGIN
# ============================

@router.post(
    "/login/",
    response_model=LoginRespuesta
)
def validar_usuario(
    datos: LoginRequest,
    response: Response,
    db: Session = Depends(obtener_db)
):

    resultado, session_id = (
        usuarios_controller.validar_usuario(datos, db)
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


# ============================
# CONSULTAR POR CORREO
# ============================

@router.get(
    "/por-correo",
    response_model=UsuarioResponse
)
def consultar_usuario(
    datos: Annotated[
        UsuarioConsultaCorreo,
        Query()
    ],
    db: Session = Depends(obtener_db)
):
    return usuarios_controller.obtener_usuario_por_correo(
        datos, db
    )


# ============================
# LISTAR USUARIOS
# ============================

@router.get(
    "/",
    response_model=list[UsuarioResponse]
)
def listar_usuarios(
    datos: Annotated[
        UsuarioListado,
        Query()
    ],
    db: Session = Depends(obtener_db)
):
    return usuarios_controller.listar_usuarios(
        datos, db
    )