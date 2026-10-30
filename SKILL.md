---
name: evaluacion-proyectos
description: Estructura una reunión de levantamiento técnico (transcripción de Teams) en propuesta SONDA (.docx), casos de uso y historias de usuario (.xlsx), diagrama de secuencia (.drawio) y valorización CoE. Usar cuando el usuario pida evaluar, estructurar o levantar una iniciativa/proyecto a partir de una reunión o transcripción.
argument-hint: "[nombre de la reunión o ruta de la transcripción]"
---

# Evaluación de proyectos CoE

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

## Stages
1. `specs/stage-1-ingesta.md` — origen de la transcripción, confirmación, nomenclatura y extracción de hechos.
2. `specs/stage-2-viabilidad.md` — puerta de control de casos de uso.
3. `specs/stage-3-generacion.md` — JSON + scripts (contratos en `specs/script-*.md`).
4. `specs/stage-4-cierre.md` — tarjeta CoE y archivos generados.

Rúbrica CoE para asignar scores: `<SKILL_DIR>/templates/rubrica_coe.md`.
