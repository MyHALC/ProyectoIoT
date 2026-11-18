from mongoengine import (
    Document,
    IntField,
    DateTimeField,
    DictField
)

from db.mongodb.connection import (
    MONGO_ALIAS,
    MONGO_COLECCION
)


class RegistroIoT(Document):

    id_priv_dispositivo = IntField(
        required=True,
        min_value=1
    )

    fecha_generacion = DateTimeField(
        required=True
    )

    fecha_recepcion = DateTimeField(
        required=True
    )

    payload = DictField(
        required=True
    )

    meta = {
        "collection": MONGO_COLECCION,
        "db_alias": MONGO_ALIAS,
        "strict": True,
        "auto_create_index": False
    }