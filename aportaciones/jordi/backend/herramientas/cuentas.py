if __package__ in (None, ''):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
from fastapi import HTTPException
from pydantic import ValidationError
from controllers.administradores_controller import AdministradoresController
from controllers.usuarios_controller import UsuariosController
from db.sql import obtener_sessionmaker
from herramientas.comun import Consola


def main():
    parser = argparse.ArgumentParser(description='Alta local de cuentas autorizada por un administrador.')
    parser.add_argument('tipo', nargs='?', choices=('usuario', 'administrador'))
    tipo = parser.parse_args().tipo or input('Tipo (usuario/administrador): ').strip()
    if tipo not in ('usuario', 'administrador'):
        parser.error('Tipo inválido.')
    try:
        with obtener_sessionmaker()() as db:
            admin = Consola.administrador(db)
            datos = Consola.datos_persona()
            controlador = AdministradoresController() if tipo == 'administrador' else UsuariosController()
            cuenta = controlador.registrar(datos, db, admin)
            print('Cuenta creada y vinculada. Identificador público:', cuenta['id_pub'])
        return 0
    except ValidationError:
        print('Revisa los datos ingresados.')
    except (ValueError, HTTPException) as error:
        print(error.detail if isinstance(error, HTTPException) else str(error))
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
