from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from controllers.sesiones_controller import SesionesController
from db.sql import obtener_db
from schemas.cifrado_schema import PeticionCifrada, RespuestaCifrada

router = APIRouter()
comunicacion = APIRouter()
controller = SesionesController()


@comunicacion.post('/', response_model=RespuestaCifrada)
def comunicar(datos: PeticionCifrada, db: Session = Depends(obtener_db)):
    return controller.comunicar(datos, db)


@router.post('/actual', response_model=RespuestaCifrada)
def actual(datos: PeticionCifrada, db: Session = Depends(obtener_db)):
    return controller.comunicar(datos, db, 'sesion_actual')


@router.post('/cerrar', response_model=RespuestaCifrada)
def cerrar(datos: PeticionCifrada, db: Session = Depends(obtener_db)):
    return controller.comunicar(datos, db, 'salir')
