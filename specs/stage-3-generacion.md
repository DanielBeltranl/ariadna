# Stage 3: JSON y generación

Escribe 4 JSON en `docs/proyectos/<slug>/` siguiendo su contrato y luego ejecuta los scripts. Los ejemplos completos están en `<SKILL_DIR>/examples/`.

| JSON | Contrato | Script | Salida |
| :--- | :--- | :--- | :--- |
| `propuesta.json` | `specs/script-propuesta.md` | `build_propuesta.py` | `Propuesta <Nombre>.docx` |
| `casos.json` | `specs/script-casos-uso.md` | `build_casos_uso.py` | `Casos de Uso <Nombre>.xlsx` |
| `historias.json` | `specs/script-historias.md` | `build_historias.py` | `Historias de Usuario <Nombre>.xlsx` |
| `diagrama.json` | `specs/script-diagrama.md` | `build_diagrama.py` | `Diagrama de Secuencia <Nombre>.drawio` |

`<Nombre>` es el nombre de la iniciativa (parte central de la nomenclatura). Solo los casos VIABLES generan casos, historias y diagrama; si no hay ninguno viable, genera solo la propuesta.

Ejecuta cada script así (uno por JSON):
```text
python "<SKILL_DIR>/scripts/build_casos_uso.py" --json "docs/proyectos/<slug>/casos.json" --output "docs/proyectos/<slug>/Casos de Uso <Nombre>.xlsx"
```
Ejecuta `build_propuesta.py` al final: imprime la tarjeta CoE que se muestra en el Stage 4.

Si un script falla, muestra su mensaje de error, corrige el JSON solo si el error es de formato, y vuelve a ejecutarlo una vez. Si persiste, detén el pipeline.
