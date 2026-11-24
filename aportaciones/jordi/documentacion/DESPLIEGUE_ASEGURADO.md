# Cómo entender despliegue.py

La clase `Despliegue` prepara la primera cuenta del sistema y controla si puede revisarse su instalación.

## La decisión principal

Lee primero `_revisar_instalacion`. Hace estas comprobaciones, en este orden:

1. Busca al administrador máster en MariaDB.
2. Comprueba la llave maestra.
3. Si no existe el máster, crea la instalación inicial.
4. Si la instalación tiene valor `1`, muestra el bloqueo y termina.
5. Si tiene valor `0`, la consola pide autorización para conservar o reemplazar al máster.

| Campo instalacion_asegurada | Significado |
| --- | --- |
| `1` | El máster está identificado y la instalación está asegurada. |
| `0` | El máster está identificado y el administrador de MariaDB habilitó su revisión. |
| `NULL` | La cuenta es otro administrador; no controla el despliegue. |

## Qué hace cada método

**`ejecutar`: abre y cierra el trabajo.** Obtiene la conexión, comprueba las tablas y llama al flujo principal. El bloqueo de MariaDB impide ejecutar dos despliegues simultáneos; `finally` lo libera al terminar, incluso si aparece un error.

**`administrador_master`: busca la cuenta correcta.** Consulta los administradores cuyo indicador no es NULL. Si hay varios, un valor inválido o datos incompletos, detiene el proceso. Si la base no tiene administradores, devuelve `None`, que significa que falta crear la instalación.

**`validar_llave_maestra`: comprueba la llave.** Primero cuenta las llaves cifradas existentes. Después utiliza la maestra para abrirlas. Así verifica que corresponde a los datos guardados, además de tener el formato de 32 bytes. Si falta o no sirve para una instalación existente, genera un error y conserva los datos. Una base vacía todavía no tiene secretos con los cuales contrastarla; el alta inicial comprueba su funcionamiento.

**`_crear_master`: prepara una instalación nueva.** Pide los datos, genera la llave maestra si falta y la guarda en `.env`. Calcula el hash de la contraseña, crea la cuenta, marca el indicador en `1` y vincula su llave compartida.

**`reinstalar`: pregunta y comprueba la autorización.** Exige indicador `0` y credenciales válidas del máster. Pregunta si se conservan sus datos; Enter equivale a sí. Si se conservan, marca `1` y termina. Si se reemplazan, solicita los nuevos datos y exige escribir `REEMPLAZAR`.

**`_copiar_llaves_master`: guarda copias en memoria.** Lee únicamente los archivos de identidad del máster anterior para poder recuperarlos si falla el reemplazo.

**`_reemplazar_master`: aplica el cambio autorizado.** Retira los alias y datos de acceso anteriores, crea y vincula al nuevo máster y transfiere a su cuenta la relación de los dispositivos. Si falla, `rollback` recupera la operación SQL y se restauran los archivos anteriores. Tras el éxito, invalida las sesiones del máster sustituido.

## Palabras que aparecen en el código

| Palabra | Para qué se utiliza |
| --- | --- |
| `db` | Sesión con la que se consulta o modifica MariaDB. |
| `self` | Permite llamar a otro método del mismo objeto Despliegue. |
| `select` | Construye una consulta de datos. |
| `return` | Termina el método y, cuando corresponde, devuelve un resultado. |
| `raise ValueError` | Detiene una operación cuyos datos o estado no son válidos. |
| `commit` | Confirma los cambios en la base de datos. |
| `rollback` | Revierte los cambios SQL pendientes si falla una operación. |
| `try/except` | Ejecuta una operación y permite recuperar el estado si aparece un error. |
| `finally` | Ejecuta la limpieza tanto si hubo éxito como si hubo error. |
| `_` al principio de un método | Indica que es una ayuda interna de la clase, por convención de Python. |

La reinstalación reemplaza solo al máster. Conserva las otras identidades, la llave maestra del servidor, las lecturas y la auditoría. El proceso sigue usando POO, MariaDB y los servicios nativos de Windows. Las pruebas se realizan fuera del repositorio con datos temporales.
