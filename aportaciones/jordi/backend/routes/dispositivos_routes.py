from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from controllers.autenticacion_controller import AutenticacionController
from controllers.sesiones_controller import SesionesController
from db.sql import obtener_db
from schemas.cifrado_schema import PeticionCifrada, PeticionLoginCifrada, RespuestaCifrada
from schemas.peticiones import SolicitudReto

router = APIRouter()
autenticacion = AutenticacionController()


@router.post('/registro/', response_model=RespuestaCifrada)
def registrar(datos: PeticionCifrada, db: Session = Depends(obtener_db)):
    return SesionesController().comunicar(datos, db, 'registrar_dispositivo')


@router.post('/reto/')
def reto(datos: SolicitudReto, db: Session = Depends(obtener_db)):
    return autenticacion.reto(db, 'dispositivo', datos.id_cliente)


@router.post('/autenticar/', response_model=RespuestaCifrada)
def login(datos: PeticionLoginCifrada, db: Session = Depends(obtener_db)):
    return autenticacion.iniciar(db, 'dispositivo', datos)
