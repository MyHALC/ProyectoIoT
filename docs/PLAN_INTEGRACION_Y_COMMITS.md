# Plan de integración y commits del framework IoT

Este documento organiza las aportaciones de los equipos y establece cómo integrarlas sin incorporar cambios a `main`. La rama de trabajo para esta etapa es `Experimental`.

## 1. Estado de las ramas revisadas

| Rama | Aportación identificada | Tratamiento recomendado |
|---|---|---|
| `EquipoJuan_Wilmer` | Campo `es_master` en administrador, esquema y SQL | Ya fusionada en `Experimental` mediante el PR #2. |
| `EquipoJohana_Karen` | Interfaz web, plantillas, CSS/JS, correo, Docker y ajustes de API | Integrar por etapas |
| `EquipoJordi_Andrea` | Sesiones Redis, identidad, confianza, cifrado, llaves y cliente IoT en `aportaciones/` | Mantener aislada hasta acordar interfaces y pruebas. |
| `EquipoRaul` | Verificación de peticiones, HMAC, anti-replay y Redis en `aportaciones/` | Integrar después de definir el contrato criptográfico y de sesiones. |
| `EquipoAriam` |  |  |
| `Experimental` | Contiene el cambio de `es_master` y el merge del PR #2 | Rama de integración de pruebas |
| `feature/middleware-cifrado` | AES-GCM, esquemas y dependencia `cryptography` | PR #1 abierto. |

## 2. Convención de commits

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

## 3. Pull Requests y revisiones

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

## 4. Flujo Git local

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




