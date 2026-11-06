# Stage 4: Cierre y valorización

1. Lee `docs/proyectos/<slug>/tarjeta-coe.txt` (la escribe `build_propuesta.py`) y muéstrala **tal cual**, dentro de un bloque de código. No recalcules ni reformatees ningún número.
2. Lista los archivos generados:
   ```text
   Archivos generados en docs/proyectos/<slug>/:
   - Propuesta <Nombre>.docx
   - Analisis de Automatizabilidad <Nombre>.docx
   - Casos de Uso <Nombre>.xlsx
   - Historias de Usuario <Nombre>.xlsx
   - Diagrama de Secuencia <Nombre>.drawio
   - fuentes.md y los 5 JSON (para regenerar si se corrigen datos)
   ```
3. Enumera los datos que quedaron `[PENDIENTE]` o sin score (la tarjeta los muestra).
4. Recuerda: actualizar la tabla de contenido del .docx en Word (clic derecho → "Actualizar campos") y que "Decisión tomada" y "Responsable definido" los completa el comité.
5. Publica en SharePoint (sección siguiente).
6. Cierra con el aviso de gobernanza: **Estos cambios deben ser validados antes de darse por finalizados.**

## Publicar en SharePoint
Destino: la carpeta de la iniciativa dentro de `02. - Documentos Relacionados a Iniciativas` (sitio `Centro_de_Operaciones_Chile`, ruta `CL_COP/01_Areas/03_App/08_Automatizacion`). Usa el conector Microsoft 365; sin conector autenticado, indica ejecutar `/mcp` → "claude.ai Microsoft 365" y termina aquí (los archivos ya quedaron en local).

1. **Carpeta padre**: `sharepoint_folder_search` con `Documentos Relacionados a Iniciativas`; usa el resultado cuyo `webUrl` contiene `/sites/Centro_de_Operaciones_Chile/` y guarda su `driveId` e `id`.
2. **Carpeta de la iniciativa**: lista la carpeta padre con `read_resource` (si trae la nota de más páginas, sigue con `startPage`). Busca la subcarpeta cuyo nombre empieza con el código CoE del Stage 1, sin distinguir mayúsculas e ignorando espacios repetidos (ej. `17-N2-COM-CL  Creación Reglas de FW-Fortinet  AUT` para `17-N2-COM-CL`).
   - Si existe: `Encontré la carpeta «<nombre>» en SharePoint. ¿Subo ahí los archivos? (sí / no)`.
   - Si no existe: `No hay carpeta para <código> en SharePoint. ¿La creo como «<CÓDIGO> <Nombre>»? (sí / no)`. Con "sí", créala con `sharepoint_create_folder` (`driveId` y `parentItemId` de la carpeta padre) y usa su `id`.
   - Con "no", termina aquí sin subir nada.
3. **Subida**: sube cada archivo de `docs/proyectos/<slug>/` con `sharepoint_upload_file` (`driveId`, `parentItemId` de la carpeta de la iniciativa, `filename` = nombre local). Los `.json`, `.md` y `.txt` van como `content`; los `.docx`, `.xlsx` y `.drawio` van como `contentBase64`, obtenido con:
   ```text
   python -c "import base64,sys; print(base64.b64encode(open(sys.argv[1],'rb').read()).decode())" "<ruta del archivo>"
   ```
   Usa `conflictBehavior` `fail`. Si un archivo ya existe, pregunta `«<archivo>» ya existe en SharePoint. ¿Lo reemplazo? (sí / no)` y, con "sí", reintenta con `replace`. Un archivo mayor a 1 MB no se puede subir con el conector: avísalo y sigue con el resto.
4. Informa el `webUrl` de la carpeta y los archivos subidos, omitidos o fallidos.
