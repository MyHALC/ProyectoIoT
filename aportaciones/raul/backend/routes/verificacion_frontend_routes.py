from fastapi import APIRouter, Header, Request

from controllers.verificacion_frontend_controller import (
    verificacion_frontend_controller
)

from schemas.verificacion_frontend_schema import (
    VerificacionFrontendRequest,
    VerificacionFrontendResponse
)


router = APIRouter()


@router.post(
    "/verificar",
    response_model=VerificacionFrontendResponse
)
def verificar_paquete_frontend(
    datos: VerificacionFrontendRequest,
    request: Request,
    x_app_session_id: str | None = Header(default=None),
    x_app_origin: str | None = Header(default=None)
):
    origen = request.headers.get("origin") or x_app_origin

    return verificacion_frontend_controller.verificar_paquete_frontend(
        datos, x_app_session_id, origen
    )
