# Arquitectura del backend

## Capas

- **routes/**: define endpoints, métodos HTTP, dependencias y modelos de respuesta.
- **schemas/**: valida los datos de entrada y estructura las respuestas con Pydantic.
- **controllers/**: concentra reglas de negocio y traduce errores de persistencia a respuestas HTTP.
- **db/**: encapsula conexiones y modelos de almacenamiento.

## Persistencia

| Tecnología | Uso en el servidor |
|---|---|
| MySQL/MariaDB | Cuentas, administradores, dispositivos, correos y contraseñas |
| MongoDB | Registros de telemetría IoT |
| Redis | Sesiones con expiración |

## Sesiones

El repositorio Redis genera identificadores aleatorios, almacena su hash como clave y configura un TTL de 30 minutos. La cookie de sesión se configura como HttpOnly y SameSite=Lax; Secure depende de `COOKIE_SECURE`.

## Rutas registradas

- `/api/usuarios`
- `/api/administradores`
- `/api/dispositivos`
- `/api/registros-iot`
- `/api/sesiones`

## Consideraciones antes de producción

1. Definir migraciones reproducibles para el esquema relacional.
2. Validar disponibilidad, autenticación y autorización de cada endpoint.
3. Restringir CORS a los orígenes productivos.
4. Configurar TLS y cookies Secure.
5. Añadir pruebas unitarias e integración con servicios aislados.
6. Definir health checks y estrategia de despliegue.
