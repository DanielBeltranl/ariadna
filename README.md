# Ariadna

> Como el hilo que Ariadna le dio a Teseo para salir del laberinto: de una reunión enredada, saca el hilo de la iniciativa.

Convierte la transcripción de una reunión de levantamiento técnico en la documentación inicial de una iniciativa de automatización, lista para revisar por el CoE:

| Archivo | Contenido |
| :--- | :--- |
| `Propuesta <Nombre>.docx` | Propuesta técnica en formato SONDA: contexto, objetivos, alcance, fuera de alcance, observaciones y valorización CoE |
| `Casos de Uso <Nombre>.xlsx` | Casos de uso, una hoja por módulo |
| `Historias de Usuario <Nombre>.xlsx` | Historias de usuario con criterios de aceptación, una hoja por módulo |
| `Diagrama de Secuencia <Nombre>.drawio` | Diagrama de secuencia general, editable en draw.io |
| `tarjeta-coe.txt` | Score CoE, prioridad y métricas (también se muestra en el chat) |

> El resultado es una **estructura inicial**: debe ser revisada y validada antes de darse por finalizada.

Es una *skill* de Claude Code: se usa escribiendo `/ariadna` en el chat.

---

## Instalación rápida

Requiere [Claude Code](https://claude.com/claude-code) y Git. En PowerShell:

```powershell
git clone <url-del-repo> "$HOME\.claude\skills\ariadna"
```

Abre una sesión nueva de Claude Code y escribe `/ariadna`. Listo.

**Python:** el pipeline necesita Python 3.10+ y `openpyxl`. No hace falta instalarlos antes: al primer uso el agente los verifica y, si faltan, **ofrece instalarlos** (Python con `winget` para tu usuario, sin permisos de administrador; `openpyxl` con `pip`). Nunca instala nada sin tu confirmación.

Si `winget` está bloqueado en tu equipo, instala Python manualmente desde [python.org](https://www.python.org/downloads/) marcando **"Add python.exe to PATH"**, reabre Claude Code y ejecuta:

```powershell
python -m pip install --user -r "$HOME\.claude\skills\ariadna\requirements.txt"
```

### Actualizar

```powershell
git -C "$HOME\.claude\skills\ariadna" pull
```

### Desinstalar

Borra la carpeta `$HOME\.claude\skills\ariadna`.

---

## Uso

> **Antes de la reunión:** usa la [Guía de Reunión de Levantamiento](docs/guia-reunion/Guia%20de%20Reunion%20de%20Levantamiento.pdf). 10 preguntas para una reunión de 20 a 40 minutos, ordenadas para que la transcripción traiga lo que el pipeline necesita.

1. Abre Claude Code **en la carpeta donde quieres los documentos** (por ejemplo, la carpeta del proyecto o una de trabajo).
2. Escribe:
   ```text
   /ariadna
   ```
   También acepta el nombre de la reunión o la ruta de la transcripción: `/ariadna Checklist sistema SAG`. O simplemente pídelo en lenguaje natural: *"evalúa la reunión del sistema SAG"*.
3. Responde lo que el agente pregunta. Los documentos quedan en `docs\proyectos\<código>\`.

### Qué te va a preguntar

| Paso | Pregunta | Qué responder |
| :--- | :--- | :--- |
| 0 | (Solo si falta) ¿Instalo Python / openpyxl? | `sí` o `no` |
| 1 | ¿De dónde tomo la transcripción? | `1` (buscar en Teams) o `2` (archivo) |
| 1 | Confirma la reunión o el archivo encontrado | `sí` o `no` |
| 1 | Código y nombre formal de la iniciativa | `19-N1-COM-CL \| Gestión Alerta Enlaces caídos \| MON` |
| 2 | ¿Qué casos de uso son viables en esta fase? | Números separados por coma (`1, 3`) o `todos` |

Al final muestra la tarjeta de valorización CoE y la lista de archivos generados.

### Cómo entregar la transcripción

Descárgala desde Teams (pestaña **Transcripción** de la reunión → Descargar, en `.docx` o `.vtt`). Luego, en el paso 1, elige la opción `2` y entrega cualquiera de estas:

- La ruta del archivo: `C:\Users\yo\Downloads\Reunion SAG.docx`
- Una carpeta: el agente toma la transcripción más reciente que haya ahí.
- `la más reciente en Descargas`

Cuando el agente encuentra el archivo por su cuenta, te muestra duración, participantes y tema para que confirmes que es el correcto.

> **Sobre la opción Teams:** el agente puede encontrar la reunión en tu calendario (requiere el conector "claude.ai Microsoft 365", activable con `/mcp`), pero en el tenant de Sonda **la descarga automática de transcripciones está bloqueada por política**. La opción sirve para identificar la reunión y su nomenclatura; la transcripción se entrega como archivo.

---

## Cómo se calcula la valorización CoE

Fórmula oficial del CoE, calculada siempre por el script (nunca por el modelo):

```text
(Impacto×0.30) + (Eficiencia×0.20) + (Riesgo×0.15) + (Escalabilidad×0.10) + (Alineamiento×0.10) − (Complejidad×0.15)
Prioridad: ≥3.5 Alta | 2.5–3.4 Media | <2.5 Baja
```

- Los scores 1–5 se asignan con la rúbrica de [`templates/rubrica_coe.md`](templates/rubrica_coe.md), citando evidencia de la reunión.
- La **eficiencia** se calcula desde las horas hombre ahorradas: volumen mensual × minutos × % automatización.
- Si la reunión no da evidencia para una dimensión, se muestra *"No hay suficientes datos para establecer una calificación certera"* y el score final queda `[PENDIENTE]`. Nunca se inventan valores.
- "Decisión tomada" y "Responsable definido" quedan en blanco: los completa el comité.

---

## Problemas frecuentes

| Síntoma | Solución |
| :--- | :--- |
| `/ariadna` no aparece | Verifica que exista `$HOME\.claude\skills\ariadna\SKILL.md` y abre una sesión nueva de Claude Code |
| "No se pudo guardar … ¿está abierto en Excel o Word?" | Cierra el archivo en Excel/Word y vuelve a pedir la generación |
| La tabla de contenido del `.docx` sale vacía | En Word: clic derecho sobre la tabla → **Actualizar campos** |
| `python` abre la Microsoft Store | Python no está instalado: acepta la instalación asistida o instálalo desde python.org |
| Después de instalar Python, `python` sigue sin funcionar | Reabre Claude Code para que tome el nuevo PATH |

---

## Para desarrolladores

```powershell
python -m unittest discover -s tests
```

| Ruta | Contenido |
| :--- | :--- |
| `SKILL.md` | Punto de entrada de la skill: reglas del agente y verificación de Python |
| `specs/stage-*.md` | Instrucciones de cada etapa (ingesta, viabilidad, generación, cierre) |
| `specs/script-*.md` | Contrato JSON de cada generador |
| `scripts/` | Generadores deterministas (`build_*.py`), cálculo CoE (`coe.py`) y lector de transcripciones |
| `scripts/sonda/` | Copia sin cambios del generador y plantilla de la skill `sonda-user-manual` |
| `examples/*.json` | JSON de ejemplo de cada generador (también usados por los tests) |
| `templates/rubrica_coe.md` | Rúbrica oficial del CoE |

Principio de diseño: el modelo solo extrae información y arma JSON; todos los archivos y cálculos los producen scripts, así el formato es siempre el mismo y se gastan menos tokens.

Cada generador se puede ejecutar a mano:

```powershell
python scripts\build_casos_uso.py --json examples\casos.json --output "Casos de Uso Ejemplo.xlsx"
```
