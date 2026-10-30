# Script: build_historias.py

Genera el Excel de historias de usuario con el formato de `Historias de usuario ejemplo.xlsx`. Ejemplo completo: `examples/historias.json`.

```text
python "<SKILL_DIR>/scripts/build_historias.py" --json "<historias.json>" --output "<Historias de Usuario X.xlsx>"
```

## Contrato `historias.json`
`{"iniciativa": "...", "historias": [ ... ]}`, cada historia con:

| Campo | Contenido |
| :--- | :--- |
| `modulo` | Una hoja por módulo; ausente → "General" |
| `nombre` | Nombre corto de la historia |
| `rol`, `accion`, `beneficio` | Se arma "Como <rol>, quiero <accion> para <beneficio>." (sin punto final en los campos) |
| `criterios` | Lista de criterios de aceptación, sin numerar |

## Formato generado
- Columnas: N° | Nombre | Descripción | Criterios de Aceptación.
- Cabecera celeste `A4C2F4`, numeración `1.0`, `2.0`… por hoja.
- Criterios en una celda: `1. …` + línea en blanco + `2. …`.
- Solo historias de casos VIABLES.
- Errores (código 1): lista vacía, historia sin campo obligatorio, archivo abierto en Excel.
