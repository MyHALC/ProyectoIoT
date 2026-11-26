if __package__ in (None, ''):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
from cryptography.exceptions import InvalidTag
from db.sql import obtener_sessionmaker
from db.mysql.repositorio import RepositorioIdentidades
from seguridad.confianza import Confianza
from seguridad.almacen_llaves import AlmacenLlaves
from seguridad.protocolo import Protocolo
from herramientas.comun import Consola


def main():
    parser = argparse.ArgumentParser(description='Administrar la confianza vigente de una identidad.')
    parser.add_argument('accion', nargs='?', choices=('vincular', 'rotar', 'revocar'))
    accion = parser.parse_args().accion or input('Acción (vincular/rotar/revocar): ').strip()
    if accion not in ('vincular', 'rotar', 'revocar'):
        parser.error('Acción inválida.')
    try:
        with obtener_sessionmaker()() as db:
            admin = Consola.administrador(db)
            tipo = input('Tipo (usuario/administrador/dispositivo): ').strip()
            if tipo not in Protocolo.tipos:
                raise ValueError('Tipo de identidad inválido.')
            repo = RepositorioIdentidades(db)
            for e in repo.listar(tipo):
                print(e.id_pub, e.info.nombre, 'activa' if e.fila.activo else 'pendiente')
            e = repo.por_id(tipo, int(input('Identificador público: ')))
            if e is None:
                raise ValueError('La identidad no existe.')
            if accion in ('rotar', 'revocar') and input(f'Escribe {accion.upper()} para continuar: ').strip() != accion.upper():
                return 0
            confianza = Confianza(db)
            if accion == 'revocar':
                confianza.revocar(e, admin)
            else:
                llave = None
                if accion == 'vincular' and e.fila.activo and e.llave:
                    llave = Confianza.llave(e)
                    esperado = {'id_cliente': e.id_pub, 'llave': Protocolo.base64(llave)}
                    if all(AlmacenLlaves(tipo).cargar(a) == esperado for a in e.alias()):
                        print('La identidad ya está vinculada.')
                        return 0
                confianza.establecer(e, admin, llave=llave)
            print('Operación completada.')
        return 0
    except (ValueError, InvalidTag) as error:
        print(str(error) or 'No se pudo abrir una llave almacenada.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
