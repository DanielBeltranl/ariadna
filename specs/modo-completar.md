# Modo completar: retomar una iniciativa existente

Se usa cuando el usuario quiere completar, retomar o actualizar una iniciativa que ya tiene carpeta en SharePoint. Requiere el conector Microsoft 365; sin él, indica ejecutar `/mcp` → "claude.ai Microsoft 365" y detente.

## 1. Encontrar la iniciativa
1. Si `$ARGUMENTS` o la conversación no la nombran, pregunta: `¿Qué iniciativa quieres completar? (código, número o parte del nombre)`.
2. Ubica la carpeta padre `02. - Documentos Relacionados a Iniciativas` como en `stage-4-cierre.md` → «Publicar en SharePoint», paso 1, y lista sus subcarpetas con `read_resource`.
3. Compara lo que dio el usuario con cada nombre, sin distinguir mayúsculas ni tildes: el código completo (`45-N2-SEG-CL`), el correlativo (`45`, `el 45`) o palabras del nombre (`QRadar`, `ofensas`). El usuario rara vez da el código exacto.
4. Muestra hasta 5 candidatas numeradas y confirma, aunque haya una sola:
   ```text
   Encontré estas iniciativas:
   [1] 45-N2-SEG-CL Casos de uso ofensas QRadar
   ¿Cuál es? (número, o "ninguna")
   ```
   Con "ninguna" o sin coincidencias, pide otro dato. Si no existe, ofrece crearla con el flujo normal (Stage 1).
5. Toma el código del inicio del nombre de la carpeta. Slug = código en minúsculas. El nombre formal es el resto del nombre de la carpeta; confírmalo si no está claro.

## 2. Cargar lo que existe
Lista la carpeta elegida con `read_resource` y busca los JSON de Ariadna (`propuesta.json`, `automatizabilidad.json`, `casos.json`, `historias.json`, `diagrama.json`).

- **Con JSON de Ariadna**: lee cada JSON y `fuentes.md` con `read_resource` y guárdalos tal cual en `docs/proyectos/<slug>/` con la herramienta Write. Sigue con el paso 3.
- **Sin JSON de Ariadna** (carpeta anterior a Ariadna): informa en una línea que la iniciativa no tiene levantamiento de Ariadna y que se usarán sus documentos como fuentes. Lee cada archivo con `read_resource` (también dentro de subcarpetas) y guarda su texto en `docs/proyectos/<slug>/sharepoint/<nombre original>.md`. Las imágenes no se pueden leer así: lístalas como omitidas. Luego ejecuta el flujo normal desde `stage-1-ingesta.md`, sección 2b, con `--input "docs/proyectos/<slug>/sharepoint"`, y en la sección 3 usa el código y nombre ya confirmados (no los vuelvas a pedir). Al publicar (Stage 4), usa la misma carpeta sin volver a buscarla.

## 3. Listar pendientes
```text
python "<SKILL_DIR>/scripts/pendientes.py" --dir "docs/proyectos/<slug>"
```
Imprime `{"pendientes": [{"archivo", "campo", "pregunta"}]}`. Muestra el total por archivo. Si no hay pendientes, dilo y pregunta si hay algo puntual que actualizar; si no, termina.

## 4. Preguntar de a uno
Para cada pendiente, en orden: formula su `pregunta` y espera la respuesta antes de seguir. Si varios pendientes piden el mismo dato (por ejemplo `evaluacion_coe.volumen_mensual` y la observación «Volumen mensual: [PENDIENTE]»), pregúntalo una sola vez y actualiza todos.
- Con respuesta: actualiza el `campo` del `archivo` con evidencia `[fuente: respuesta de <usuario>, <dd/mm/aaaa>]`. En `automatizabilidad.json`, ajusta `estado` y `evidencia` del criterio y **borra su `pregunta`** (ya está respondida). Un score CoE se asigna con `templates/rubrica_coe.md` y su `_justificacion`; las métricas son números, nunca estimaciones.
- Con "no sé", "no" o "saltar": deja el pendiente como está y sigue.
- Con "basta" o "terminar": deja de preguntar y sigue al paso 5 con lo respondido.
- Si una respuesta contradice algo ya registrado, muestra ambas versiones y pregunta cuál vale.

Agrega al final de `fuentes.md` una sección `## Actualización <dd/mm/aaaa>` con cada pregunta y su respuesta.

## 5. Regenerar
1. En cada JSON modificado que genera `.docx` (`propuesta.json`, `automatizabilidad.json`), sube la versión menor (`1.0` → `1.1`; sin campo `version`, la actual es `1.0`) y pon `"cambio": "Actualización de pendientes"`.
2. Ejecuta los scripts de los JSON modificados, con los mismos comandos y nombres de archivo de `stage-2-viabilidad.md` y `stage-3-generacion.md`. Ejecuta `build_propuesta.py` al final siempre: la tarjeta CoE puede cambiar.
3. Si cambió el veredicto de algún caso, muéstralo (`UC-02: No automatizable aún → Automatizable`) y pregunta si cambia el alcance. Si cambia, actualiza `alcance`/`fuera_de_alcance` en `propuesta.json` y vuelve a ejecutar `build_propuesta.py`.

## 6. Cierre
Sigue `stage-4-cierre.md` desde el paso 1. Al publicar, la carpeta ya está elegida: confirma una sola vez `¿Reemplazo los archivos actualizados en «<carpeta>»? (sí / no)` y súbelos con `conflictBehavior` `replace`; los archivos nuevos se suben con `fail`.
