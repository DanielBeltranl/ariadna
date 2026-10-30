# Script: build_casos_uso.py

Genera el Excel de casos de uso con el formato de `Casos de uso ejemplo.xlsx`. Ejemplo completo: `examples/casos.json`.

```text
python "<SKILL_DIR>/scripts/build_casos_uso.py" --json "<casos.json>" --output "<Casos de Uso X.xlsx>"
```

## Contrato `casos.json`
`{"iniciativa": "...", "casos": [ ... ]}`, cada caso con:

| Campo | Contenido |
| :--- | :--- |
| `modulo` | Agrupa casos en hojas (una hoja por módulo); ausente → "General" |
| `id` | `UC-01`, `UC-02`… (mismos IDs del Stage 2) |
| `titulo`, `actor`, `precondiciones`, `resultado` | Texto |
| `pasos` | Lista de textos, sin numerar (el script numera) |

## Formato generado
- Columnas: ID | Caso de Uso | Actor | Precondiciones | Flujo de Pasos | Resultado Esperado.
- Cabecera azul `535FC1` con texto blanco, filas alternadas blanco / `F6F8F9`, texto ajustado.
- Pasos en una celda: `1. …` + línea en blanco + `2. …`.
- Errores (código 1): lista vacía, caso sin campo obligatorio, archivo abierto en Excel.
