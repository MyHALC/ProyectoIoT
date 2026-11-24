from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

# Mismos parámetros Argon2id que usa el proyecto IoT del equipo.
_hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1, salt_len=16, hash_len=32)


def hashear(contrasena):
    return _hasher.hash(contrasena)


def verificar(contrasena, guardado):
    try:
        return _hasher.verify(guardado, contrasena)
    except (VerificationError, InvalidHashError):
        return False
