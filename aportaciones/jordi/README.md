# Aportación de Jordi: identidad, autenticación y despliegue

Selección de archivos del proyecto IoT para presentar la aportación de Jordi en la rama `EquipoJordi_Andrea`.

## Alcance

- Identidades y registro de usuarios, administradores y dispositivos.
- Contraseñas con hash Argon2id y sal.
- Llaves compartidas, almacenamiento protegido y alta autorizada de confianza.
- Autenticación mediante reto criptográfico y HMAC.
- Cliente Python que prepara y envía las peticiones de autenticación cifradas.
- Despliegue: validación y generación de la llave maestra, administrador máster y control de reinstalación.
- Adaptación del modelo de administrador con el indicador `instalacion_asegurada`.

## Cómo leer esta entrega

Se conservan las rutas relativas `backend/`, `frontend/cliente_iot/` y `documentacion/` del proyecto de origen. El código copiado permanece sin modificaciones. Los archivos compartidos conservan las llamadas y métodos que ya contenían; esta selección no atribuye autoría exclusiva de todas sus líneas. Los modelos y funciones originalmente proporcionados se distinguen de sus adaptaciones.

Esta carpeta es una entrega parcial para la revisión de aportaciones, no una aplicación ejecutable independiente. Se conserva intacta la base común de `src/`. Andrea incorporará posteriormente la versión completa e integrada. No se agregan aquí los módulos dedicados a sesiones, telemetría, auditoría, plantillas HTML, configuración, dependencias ni módulos originales completos.

## Orden sugerido de revisión

1. [Despliegue](backend/herramientas/despliegue.py) y [su explicación](documentacion/DESPLIEGUE_ASEGURADO.md).
2. [Repositorio de identidades](backend/db/mysql/repositorio.py) y [modelo de administrador adaptado](backend/db/mysql/models/administrador.py).
3. [Contraseñas y confianza](backend/seguridad/confianza.py) y [almacén de llaves](backend/seguridad/almacen_llaves.py).
4. [Controlador de autenticación](backend/controllers/autenticacion_controller.py) y [protocolo de reto y HMAC](backend/seguridad/protocolo.py).
5. [Cliente Python](frontend/cliente_iot/cliente.py) y [protocolo del cliente](frontend/cliente_iot/protocolo.py).

No se incluyen secretos, cuentas reales, bases con datos, entornos virtuales, respaldos ni resultados de pruebas.
