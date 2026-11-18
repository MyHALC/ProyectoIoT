from fastapi import (
    APIRouter,
    Request,
    Response
)

from controllers.sesiones_controller import (
    sesiones_controller
)

from db.redis.session_repository import (
    SESSION_COOKIE,
    COOKIE_PATH
)


router = APIRouter()


# ============================
# CONSULTAR SESIÓN ACTUAL
# ============================

@router.get("/actual")
def consultar_sesion(
    request: Request
):

    session_id = request.cookies.get(
        SESSION_COOKIE
    )

    return sesiones_controller.consultar_sesion(
        session_id
    )


# ============================
# CERRAR SESIÓN
# ============================

@router.post("/cerrar")
def cerrar_sesion(
    request: Request,
    response: Response
):

    session_id = request.cookies.get(
        SESSION_COOKIE
    )

    resultado = sesiones_controller.cerrar_sesion(
        session_id
    )

    response.delete_cookie(
        key=SESSION_COOKIE,
        path=COOKIE_PATH
    )

    return resultado