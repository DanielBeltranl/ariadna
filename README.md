# evaluacion-proyectos

Skill de Claude Code que convierte la transcripción de una reunión de levantamiento técnico en:

- Propuesta técnica en formato SONDA (`.docx`) con valorización CoE.
- Casos de uso y historias de usuario (`.xlsx`).
- Diagrama de secuencia general editable (`.drawio`).

El resultado es una estructura inicial: debe ser revisada y validada antes de darse por finalizada.

## Instalación (una vez, en PowerShell)

```powershell
git clone <url-del-repo> "$HOME\.claude\skills\evaluacion-proyectos"
pip install -r "$HOME\.claude\skills\evaluacion-proyectos\requirements.txt"
```

Requisitos: Python 3.10+ en el `PATH`; si falta, el agente ofrece instalarlo con `winget` (con tu confirmación). Opcional: conector "claude.ai Microsoft 365" autenticado (`/mcp`) para buscar la reunión en Teams.

Actualizar: `git -C "$HOME\.claude\skills\evaluacion-proyectos" pull`.

## Uso

En Claude Code, dentro del proyecto donde quieras los documentos:

```text
/evaluacion-proyectos
/evaluacion-proyectos Levantamiento enlaces caídos
/evaluacion-proyectos C:\reuniones\levantamiento.vtt
```

El agente pregunta si busca la reunión en Teams o si le entregas la transcripción (archivo, carpeta o "la más reciente en Descargas"), confirma la reunión, te deja elegir los casos de uso viables y genera todo en `docs/proyectos/<slug>/`.

> En el tenant de Sonda la descarga de transcripciones desde Teams está bloqueada por política: la búsqueda de la reunión funciona, pero la transcripción se entrega como archivo.

## Desarrollo

```powershell
python -m unittest discover -s tests
```

- `SKILL.md`: punto de entrada y reglas del agente.
- `specs/`: instrucciones por stage y contratos JSON de cada script.
- `scripts/`: generadores deterministas; `examples/`: JSON de ejemplo.
- `scripts/sonda/`: copia sin cambios del generador y plantilla de la skill `sonda-user-manual`.
