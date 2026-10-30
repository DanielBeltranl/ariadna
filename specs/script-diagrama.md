# Script: build_diagrama.py

Genera un único diagrama de secuencia general de la iniciativa (solo casos viables), editable en draw.io (web, escritorio o extensión de VS Code). Ejemplo completo: `examples/diagrama.json`.

```text
python "<SKILL_DIR>/scripts/build_diagrama.py" --json "<diagrama.json>" --output "<Diagrama de Secuencia X.drawio>"
```

## Contrato `diagrama.json`
| Campo | Contenido |
| :--- | :--- |
| `titulo` | Nombre de la iniciativa (nombre de la página del diagrama) |
| `participantes` | Lista de nombres únicos, en orden de izquierda a derecha |
| `mensajes` | Lista ordenada de `{de, a, texto, respuesta?}`; `de`/`a` deben estar en `participantes` |

- `respuesta: true` dibuja línea punteada (retorno); por defecto flecha sólida.
- `de == a` dibuja un auto-mensaje (lazo a la derecha de la línea de vida).

## Formato generado
- XML `mxfile` sin comprimir; una línea de vida (`umlLifeline`) por participante en columnas fijas.
- Mensajes de arriba hacia abajo en el orden del JSON, separados 50 px.
- Errores (código 1): participantes vacíos o repetidos, mensaje con participante desconocido.
