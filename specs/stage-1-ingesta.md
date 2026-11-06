# Stage 1: Obtención de las fuentes e ingesta

Las fuentes son todo lo que el usuario entrega como evidencia: transcripciones, actas, especificaciones, planillas, presentaciones, diagramas, PDF, imágenes. Todas valen como evidencia.

## 1. Preguntar el origen (siempre, sin adivinar)
```text
¿De dónde tomo la información de la iniciativa?
[1] Buscar la reunión en Teams
[2] Te dejo los archivos aquí:
    - una o varias rutas de archivos (separadas por coma o una por línea), o
    - la ruta de una carpeta: leo todos sus archivos (incluidas subcarpetas), o
    - "la más reciente en Descargas"
```
Si `$ARGUMENTS` trae algo, úsalo como nombre de reunión (opción 1) o como ruta(s) (opción 2) según la respuesta.

## 2a. Opción Teams
1. Busca la reunión con `outlook_calendar_search` del conector Microsoft 365 (por nombre; si no hay nombre, pregúntalo).
2. Confirma: `Encontré «<asunto>», sostenida el <dd/mm/aaaa>. ¿Es la reunión que buscas? (sí / no)`. Con varias coincidencias, lista nombre + fecha numerados.
3. Con "sí": lee el evento (`read_resource`) y luego su `meetingTranscriptUrl`.
4. Si la transcripción falla (en Sonda, Microsoft Graph responde `GraphAccessToTranscriptsDisabled` o "User does not have access to lookup meeting"), informa en una línea que la descarga está bloqueada y pasa a la opción 2.
5. Conserva del evento: asunto (suele traer la nomenclatura CoE), participantes y descripción. Úsalos como complemento, nunca en lugar de las fuentes.
6. Sin conector autenticado: indica que ejecute `/mcp` → "claude.ai Microsoft 365", o que use la opción 2.
7. Después pregunta: `¿Hay más archivos que deba considerar? (rutas, carpeta o "no")`. Si los hay, sigue con 2b.

## 2b. Opción archivos
Pasa cada ruta o carpeta como un `--input` (las carpetas se leen completas y recursivas, sin archivos ocultos ni temporales `~$`). Para "la más reciente en Descargas" usa `--input "$HOME/Downloads" --latest`. Inspecciona con:
```text
python "<SKILL_DIR>/scripts/extract_sources.py" --input "<ruta 1>" --input "<ruta 2>"
```
Imprime JSON `{"fuentes": [...]}`, uno por archivo, con `archivo`, `modificado`, `estado`, `duracion_min`, `participantes`, `tema`. Muestra siempre la lista y confirma antes de seguir:
```text
Voy a usar estas fuentes:
1. <nombre> (modificado el <modificado>) — <duracion_min> min, participantes: <participantes>
2. <nombre> (modificado el <modificado>) — PDF/imagen, lo leo directo
3. <nombre> — no puedo leer este formato
¿Están todas las que necesitas? (sí / no)
```
Omite los datos que vengan vacíos. Con "no", pide las rutas a agregar o quitar y vuelve a ejecutar. Si hay archivos `no_soportado` (por ejemplo `.doc` o `.xls` antiguos), pide una versión `.docx`, `.xlsx`, `.pdf` o texto, u ofrece continuar sin ellos.

## 3. Nomenclatura y carpeta
1. Si el asunto de Teams ya trae la nomenclatura (`<código> | <nombre> | <tag>`), confírmala; si no, pide:
   ```text
   Ingrese el código y nombre formal de la iniciativa según estándar CoE:
   Ejemplo: 19-N1-COM-CL | Gestión Alerta Enlaces caídos | MON
   ```
2. Slug = código en minúsculas (`19-n1-com-cl`). Crea `docs/proyectos/<slug>/`.
3. Guarda el texto con los mismos `--input` confirmados: `python "<SKILL_DIR>/scripts/extract_sources.py" --input "<ruta 1>" --input "<ruta 2>" --output "docs/proyectos/<slug>/fuentes.md"`. Si la transcripción vino de Teams, agrégala al final de `fuentes.md` en una sección `## Teams: <asunto>`.

## 4. Extracción de hechos
Lee `fuentes.md` descartando muletillas y ruido. Para cada fuente con estado `leer_con_read` (PDF, imagen), lee el archivo original con la herramienta Read. Identifica solo hechos confirmados:
- Qué se hace hoy y qué función cumple en la operación (contexto).
- Torre, solicitante, sistemas involucrados.
- Volumen mensual, minutos por ejecución manual, % automatizable.
- Riesgo operativo, multas, cumplimiento.
- Conectividad, usuarios y accesos.

Cada hecho lleva su fuente entre corchetes con el nombre del archivo, por ejemplo `[fuente: Reunion SAG.docx]`. Si dos fuentes se contradicen, muestra ambas y pregunta cuál vale.

Lista los casos de uso preliminares (`UC-01`, `UC-02`…), cada uno con su módulo, una acotación técnica de una línea (ej. "Requiere apertura de puerto 1521") y las fuentes que lo respaldan.
