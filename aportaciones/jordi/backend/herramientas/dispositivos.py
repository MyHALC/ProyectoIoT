if __package__ in (None, ''):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydantic import ValidationError
from controllers.dispositivos_controller import DispositivosController
from db.sql import obtener_sessionmaker
from schemas.identidad import RegistroDispositivo
from herramientas.comun import Consola


def main():
    try:
        with obtener_sessionmaker()() as db:
            admin = Consola.administrador(db)
            datos = RegistroDispositivo(nombre=input('Nombre del dispositivo: '), tipo_disp=input('Tipo de dispositivo: '))
            equipo = DispositivosController().registrar(datos, db, admin)
            print('Dispositivo vinculado. Usa este identificador en el simulador:', equipo['id_pub'])
        return 0
    except ValidationError:
        print('Revisa los datos del dispositivo.')
    except ValueError as error:
        print(error)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
