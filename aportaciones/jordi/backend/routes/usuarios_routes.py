from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from controllers.autenticacion_controller import AutenticacionController
from controllers.usuarios_controller import UsuariosController
from db.sql import obtener_db
from schemas.cifrado_schema import PeticionLoginCifrada, RespuestaCifrada
from schemas.identidad import RegistroPersona
from schemas.peticiones import SolicitudReto

router = APIRouter()
autenticacion = AutenticacionController()
usuarios = UsuariosController()


@router.post('/registro/', status_code=201)
def registrar(datos: RegistroPersona, db: Session = Depends(obtener_db)):
    return usuarios.registrar(datos, db)


@router.post('/reto/')
def reto(datos: SolicitudReto, db: Session = Depends(obtener_db)):
    return autenticacion.reto(db, 'usuario', datos.id_cliente)


@router.post('/login/', response_model=RespuestaCifrada)
def login(datos: PeticionLoginCifrada, db: Session = Depends(obtener_db)):
    return autenticacion.iniciar(db, 'usuario', datos)
