from pathlib import Path
import re
from sqlalchemy import inspect


class EsquemaIoT2:
    archivo = Path(__file__).with_name('esquema_iot2.sql')

    def __init__(self, engine):
        self.engine = engine
        fuente = self.archivo.read_text(encoding='utf-8')
        self.sentencias = re.findall(r'^(?:CREATE TABLE|ALTER TABLE)\b.*?;', fuente, re.M | re.S)
        self.columnas = {}
        self.pk = {}
        self.fk = {}
        self.unicos = {}
        for sentencia in self.sentencias:
            tabla = re.search(r'TABLE(?: IF NOT EXISTS)? `([^`]+)`', sentencia)[1]
            if sentencia.startswith('CREATE'):
                self.columnas[tabla] = re.findall(r'^\s+`([^`]+)`\s+', sentencia, re.M)
                self.pk[tabla] = tuple(re.findall(r'`([^`]+)`', re.search(r'PRIMARY KEY \(([^)]+)\)', sentencia)[1]))
                self.unicos[tabla] = {tuple(re.findall(r'`([^`]+)`', x)) for x in re.findall(r'UNIQUE KEY `[^`]+` \(([^)]+)\)', sentencia)}
            else:
                self.fk[tabla] = set(re.findall(r'FOREIGN KEY \(`([^`]+)`\) REFERENCES `([^`]+)` \(`([^`]+)`\) ON DELETE (CASCADE)', sentencia))
        if len(self.columnas) != 10:
            raise RuntimeError('El DDL de referencia debe tener diez tablas.')

    def verificar(self):
        inspector = inspect(self.engine)
        if set(inspector.get_table_names()) != set(self.columnas):
            raise RuntimeError('El esquema no coincide con iot2.sql. Ejecuta el despliegue sobre una base iot2 vacía.')
        for tabla, columnas in self.columnas.items():
            if [c['name'] for c in inspector.get_columns(tabla)] != columnas:
                raise RuntimeError(f'Las columnas de {tabla} no coinciden con iot2.sql.')
            if tuple(inspector.get_pk_constraint(tabla)['constrained_columns']) != self.pk[tabla]:
                raise RuntimeError(f'La clave primaria de {tabla} no coincide con iot2.sql.')
            fks = {(r['constrained_columns'][0], r['referred_table'], r['referred_columns'][0],
                    r.get('options', {}).get('ondelete')) for r in inspector.get_foreign_keys(tabla)}
            if fks != self.fk.get(tabla, set()):
                raise RuntimeError(f'Las relaciones de {tabla} no coinciden con iot2.sql.')
            unicos = {tuple(i['column_names']) for i in inspector.get_indexes(tabla) if i.get('unique')}
            if unicos != self.unicos[tabla]:
                raise RuntimeError(f'Los índices únicos de {tabla} no coinciden con iot2.sql.')

    def preparar(self):
        if not inspect(self.engine).get_table_names():
            with self.engine.begin() as conn:
                for sentencia in self.sentencias:
                    conn.exec_driver_sql(sentencia)
        self.verificar()
