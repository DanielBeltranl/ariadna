# Stage 1: Obtención de la transcripción e ingesta

## 1. Preguntar el origen (siempre, sin adivinar)
```text
¿De dónde tomo la transcripción?
[1] Buscar la reunión en Teams
[2] Te dejo la transcripción aquí (archivo, carpeta o "la más reciente en Descargas")
```
Si `$ARGUMENTS` trae algo, úsalo como nombre de reunión (opción 1) o como ruta (opción 2) según la respuesta.

## 2a. Opción Teams
1. Busca la reunión con `outlook_calendar_search` del conector Microsoft 365 (por nombre; si no hay nombre, pregúntalo).
2. Confirma: `Encontré «<asunto>», sostenida el <dd/mm/aaaa>. ¿Es la reunión que buscas? (sí / no)`. Con varias coincidencias, lista nombre + fecha numerados.
3. Con "sí": lee el evento (`read_resource`) y luego su `meetingTranscriptUrl`.
4. Si la transcripción falla (en Sonda, Microsoft Graph responde `GraphAccessToTranscriptsDisabled` o "User does not have access to lookup meeting"), informa en una línea que la descarga está bloqueada y pasa a la opción 2.
5. Conserva del evento: asunto (suele traer la nomenclatura CoE), participantes y descripción. Úsalos como complemento, nunca en lugar de la transcripción.
6. Sin conector autenticado: indica que ejecute `/mcp` → "claude.ai Microsoft 365", o que use la opción 2.

## 2b. Opción archivo
Acepta un archivo (`.txt`, `.vtt`, `.docx`), una carpeta, o "la más reciente en Descargas" (`$HOME/Downloads`). Inspecciona con:
```text
python "<SKILL_DIR>/scripts/extract_transcript.py" --input "<archivo o carpeta>"
```
Imprime JSON con `archivo`, `modificado`, `duracion_min`, `participantes`, `tema`. Si el archivo NO lo dio el usuario directamente (carpeta o Descargas), confirma antes de usarlo:
```text
Encontré esta transcripción:
- Archivo: <nombre> (modificado el <modificado>)
- Duración aprox.: <duracion_min> min
- Participantes: <participantes>
- Tema (primeras intervenciones): "<tema>"
¿Es la reunión que necesitas? (sí / no)
```
Omite las líneas sin dato. Con "no", ofrece el siguiente más reciente o pide la ruta.

## 3. Nomenclatura y carpeta
1. Si el asunto de Teams ya trae la nomenclatura (`<código> | <nombre> | <tag>`), confírmala; si no, pide:
   ```text
   Ingrese el código y nombre formal de la iniciativa según estándar CoE:
   Ejemplo: 19-N1-COM-CL | Gestión Alerta Enlaces caídos | MON
   ```
2. Slug = código en minúsculas (`19-n1-com-cl`). Crea `docs/proyectos/<slug>/`.
3. Guarda el texto: `python "<SKILL_DIR>/scripts/extract_transcript.py" --input "<archivo>" --output "docs/proyectos/<slug>/transcripcion.txt"`.

## 4. Extracción de hechos
Lee `transcripcion.txt` descartando muletillas y ruido. Identifica solo hechos confirmados:
- Qué se hace hoy y qué función cumple en la operación (contexto).
- Torre, solicitante, sistemas involucrados.
- Volumen mensual, minutos por ejecución manual, % automatizable.
- Riesgo operativo, multas, cumplimiento.
- Conectividad, usuarios y accesos.

Lista los casos de uso preliminares (`UC-01`, `UC-02`…), cada uno con su módulo y una acotación técnica de una línea (ej. "Requiere apertura de puerto 1521").
