# Plan de integración y commits del framework IoT

Este documento organiza las aportaciones de los equipos y establece cómo integrarlas sin incorporar cambios a `main`. La rama de trabajo para esta etapa es `Experimental`.

## 1. Estado de las ramas revisadas

| Rama | Aportación identificada | Tratamiento recomendado |
|---|---|---|
| `EquipoJuan_Wilmer` | Campo `es_master` en administrador, esquema y SQL | Ya fusionada en `Experimental` mediante el PR #2. No repetir el merge. |
| `EquipoJohana_Karen` | Interfaz web, plantillas, CSS/JS, correo, Docker y ajustes de API | Integrar por etapas; revisar que no duplique la aplicación FastAPI existente. |
| `EquipoJordi_Andrea` | Sesiones Redis, identidad, confianza, cifrado, llaves y cliente IoT en `aportaciones/` | Mantener aislada hasta acordar interfaces y pruebas. |
| `EquipoRaul` | Verificación de peticiones, HMAC, anti-replay y Redis en `aportaciones/` | Integrar después de definir el contrato criptográfico y de sesiones. |
| `EquipoAriam` | Elimina contenido del README | No fusionar esa eliminación; recuperar únicamente cambios útiles si los hubiera. |
| `Experimental` | Contiene el cambio de `es_master` y el merge del PR #2 | Rama de integración de pruebas; no sustituye a `main`. |
| `feature/middleware-cifrado` | AES-GCM, esquemas y dependencia `cryptography` | PR #1 abierto; revisar antes de aprobar. |

## 2. Orden propuesto de integración en Experimental

1. Estabilizar el backend base y documentar variables de entorno.
2. Verificar el campo `es_master` y su migración en MySQL/MariaDB.
3. Unificar la interfaz de sesiones Redis.
4. Integrar el cifrado AES-GCM y definir el formato de los paquetes.
5. Integrar la verificación HMAC y la protección anti-replay.
6. Conectar el frontend a los endpoints definitivos de FastAPI.
7. Validar despliegue, contenedores y documentación.

Cada etapa debe trabajarse en una rama independiente basada en `Experimental`, probarse y fusionarse primero en esa rama. No abrir ni fusionar estos cambios contra `main` durante esta etapa.

## 3. Convención de commits en español

Formato recomendado:

```text
tipo(area): acción concreta

Explicar qué se modificó, por qué y qué comportamiento cambia.
```

Tipos:
- `feat`: funcionalidad nueva.
- `fix`: corrección.
- `refactor`: reorganización sin cambiar el comportamiento.
- `test`: pruebas.
- `docs`: documentación.
- `build`: dependencias o construcción.
- `chore`: mantenimiento.

### Commits sugeridos por módulo

| Mensaje | Contenido esperado |
|---|---|
| `feat(admin): agregar indicador de administrador maestro` | Campo `es_master` en modelo y esquema. |
| `db(admin): crear migración para el campo es_master` | Migración segura para bases existentes. |
| `test(admin): validar permisos de administradores maestros` | Pruebas de administrador normal, maestro y accesos no autorizados. |
| `feat(sesiones): unificar almacenamiento de sesiones en Redis` | Interfaz única para crear, consultar, expirar y cerrar sesiones. |
| `test(sesiones): cubrir expiración y cierre de sesión` | Pruebas de sesión inexistente, vencida y revocada. |
| `feat(seguridad): incorporar cifrado autenticado AES-GCM` | Cifrado y descifrado con validación de llaves. |
| `test(seguridad): validar paquetes cifrados y rechazo de IV inválido` | Pruebas positivas y negativas del paquete cifrado. |
| `feat(seguridad): verificar firmas HMAC de peticiones` | Firma de campos canónicos y comparación segura. |
| `feat(seguridad): impedir repetición de mensajes` | Nonce de un solo uso y expiración. |
| `feat(frontend): agregar panel de administración` | Vistas y componentes web. |
| `feat(frontend): conectar vistas con la API` | Cliente HTTP, rutas y manejo de errores. |
| `test(integracion): validar flujo completo de autenticación` | Pruebas entre frontend, API, SQL y Redis. |

No atribuir commits a personas que no realizaron esos cambios. Conservar la autoría original de los colaboradores.

## 4. Pull Requests y revisiones

Cada PR dirigido a `Experimental` debe documentar:
- Problema que resuelve y alcance.
- Archivos y módulos modificados.
- Variables de entorno nuevas.
- Cambios de esquema o migraciones.
- Dependencias agregadas.
- Comandos de ejecución y pruebas realizadas.
- Ejemplos de petición y respuesta cuando aplique.
- Riesgos, limitaciones y pendientes.

Antes de fusionar:
1. Actualizar la rama con la última versión de `Experimental`.
2. Resolver conflictos sin descartar cambios de otros equipos.
3. Ejecutar pruebas y análisis de sintaxis.
4. Probar la integración con servicios de prueba.
5. Solicitar revisión de otro colaborador.
6. Fusionar el PR exclusivamente hacia `Experimental`.

## 5. Flujo Git local

Actualizar la rama de integración:

```bash
git switch Experimental
git pull origin Experimental
```

Crear una rama de trabajo:

```bash
git switch -c integracion/nombre-funcionalidad
```

Registrar cambios:

```bash
git add src/ tests/ docs/
git commit -m "feat(area): describir el cambio realizado"
git push -u origin integracion/nombre-funcionalidad
```

Actualizar una rama con la rama de integración:

```bash
git fetch origin
git switch integracion/nombre-funcionalidad
git merge origin/Experimental
```

Resolver conflictos archivo por archivo, ejecutar pruebas y subir la rama. No usar `git push --force` en ramas compartidas.

## 6. Riesgos técnicos que deben resolverse

### Cifrado AES-GCM
- No reutilizar un IV con la misma llave.
- La llave maestra debe ser secreta, de 32 bytes y cargarse desde una variable segura.
- No registrar llaves, contraseñas ni datos sensibles.
- Manejar de forma controlada los errores de autenticación del descifrado.

### Sesiones y HMAC
- Unificar nombres, estructura y TTL de las claves Redis.
- Consumir el nonce de forma atómica para evitar repeticiones concurrentes.
- Definir exactamente qué campos se firman y su serialización.
- Validar expiración, revocación y rol en el servidor; no confiar en datos del navegador.

### Bases de datos
- Usar migraciones versionadas y no depender únicamente de scripts SQL manuales.
- Probar instalaciones nuevas y bases existentes.
- Evitar sobrescribir tablas o datos de otros equipos.

### Frontend
- Mantener una sola API como fuente de verdad.
- Confirmar rutas, métodos, esquemas y códigos HTTP con FastAPI.
- Revisar CORS, cookies, CSRF, XSS y permisos.

## 7. Criterios para considerar una funcionalidad integrada

Una funcionalidad se considera integrada en `Experimental` cuando:
- Su PR fue revisado y fusionado a `Experimental`.
- Las pruebas automatizadas pasan.
- La configuración está documentada y no contiene secretos.
- El flujo funcional fue probado de extremo a extremo.
- La documentación refleja el comportamiento real.

## 8. Pull Requests relacionados

- [PR #1 — Middleware de cifrado AES-GCM](../pull/1) (abierto; requiere revisión).
- [PR #2 — Campo es_master](../pull/2) (fusionado en `Experimental`).
- [PR #3 — Administrador maestro](../pull/3) (borrador creado anteriormente; revisar destino antes de usar).
- [PR #4 — Interfaz web y panel](../pull/4) (borrador creado anteriormente; revisar destino antes de usar).
- [PR #5 — Identidad y sesiones](../pull/5) (borrador creado anteriormente; revisar destino antes de usar).
- [PR #6 — Verificación de peticiones](../pull/6) (borrador creado anteriormente; revisar destino antes de usar).

Los PR #3 a #6 se abrieron contra `main` como borradores. No deben fusionarse. Para continuar el trabajo de integración, crear PR nuevos con destino `Experimental` o cambiar el destino de los borradores a `Experimental` tras revisar sus diferencias.

## 9. Restricción de esta etapa

**No realizar commits, merges ni cambios de archivos en `main`.** Toda la documentación, integración y validación de esta fase debe permanecer en `Experimental`. La promoción a `main` requerirá una decisión explícita posterior y una revisión integral.
