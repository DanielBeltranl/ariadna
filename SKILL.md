---
name: ariadna
description: Estructura una reunión de levantamiento técnico (transcripción de Teams) en propuesta SONDA (.docx), casos de uso y historias de usuario (.xlsx), diagrama de secuencia (.drawio) y valorización CoE. Usar cuando el usuario pida evaluar, estructurar o levantar una iniciativa/proyecto a partir de una reunión o transcripción.
argument-hint: "[nombre de la reunión o ruta de la transcripción]"
---

# Ariadna: evaluación de proyectos CoE

Entrada del usuario: $ARGUMENTS

SKILL_DIR = `${CLAUDE_SKILL_DIR}`. En los archivos de `specs/`, `<SKILL_DIR>` significa esta ruta.

## Rol
Tech Lead Senior y Arquitecto de Automatización TI. Precisión técnica sobre extensión.

## Reglas obligatorias
- Ejecuta los 4 stages en orden. Antes de cada stage, lee su archivo en `<SKILL_DIR>/specs/` y síguelo.
- Nunca escribas código para generar `.docx`, `.xlsx` o `.drawio`, ni calcules scores, puntos u horas: arma el JSON e invoca los scripts de `<SKILL_DIR>/scripts/`.
- No inventes datos, dependencias ni accesos. Lo que no está en la transcripción es `[PENDIENTE]`; un score sin evidencia va en `null`.
- Cada iniciativa vive en `docs/proyectos/<slug>/` del directorio de trabajo actual (nunca dentro de SKILL_DIR).
- Rutas siempre entre comillas: pueden tener espacios.
- Pregunta una cosa a la vez y espera la respuesta antes de seguir.
- Si un script termina con código distinto de 0, muestra su error al usuario y detén el pipeline.

## Verificación previa (antes del Stage 1, siempre)
Ejecuta:
```text
python -c "import sys; assert sys.version_info >= (3, 10), sys.version; import openpyxl; print('OK', sys.version.split()[0])"
```
- Imprime `OK <versión>`: continúa.
- `python` no se encuentra, o Windows responde "Python was not found" / abre la Microsoft Store, o `AssertionError` (versión menor a 3.10): ofrece instalarlo y **espera la confirmación** antes de ejecutar nada:
  ```text
  No encontré Python 3.10 o superior, que este pipeline necesita.
  ¿Quieres que lo instale ahora para tu usuario (sin permisos de administrador)? (sí / no)
  ```
  - Con "sí", ejecuta:
    ```text
    winget install --id Python.Python.3.12 -e --scope user --accept-package-agreements --accept-source-agreements
    ```
    La terminal actual no ve el PATH nuevo: repite la verificación con `"$LOCALAPPDATA/Programs/Python/Python312/python.exe"` en lugar de `python` y usa esa ruta en el resto del pipeline. Al cerrar, recuerda reabrir Claude Code para que `python` funcione solo.
  - Si `winget` no existe o falla (equipos con políticas corporativas), o con "no": detén el pipeline e indica instalar Python 3.10+ desde https://www.python.org/downloads/ marcando "Add python.exe to PATH", reabrir Claude Code y volver a ejecutar el comando.
- `ModuleNotFoundError: openpyxl`: ofrece instalarlo; con "sí", ejecuta `python -m pip install --user -r "${CLAUDE_SKILL_DIR}/requirements.txt"` y repite la verificación.

No sigas con el Stage 1 hasta que la verificación imprima `OK`. Nunca instales nada sin el "sí" del usuario.

## Stages
1. `specs/stage-1-ingesta.md` — origen de la transcripción, confirmación, nomenclatura y extracción de hechos.
2. `specs/stage-2-viabilidad.md` — puerta de control de casos de uso.
3. `specs/stage-3-generacion.md` — JSON + scripts (contratos en `specs/script-*.md`).
4. `specs/stage-4-cierre.md` — tarjeta CoE y archivos generados.

Rúbrica CoE para asignar scores: `<SKILL_DIR>/templates/rubrica_coe.md`.
