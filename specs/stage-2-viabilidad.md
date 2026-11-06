# Stage 2: Puerta de viabilidad

0. **Análisis de automatizabilidad.** Evalúa cada caso de uso preliminar con `<SKILL_DIR>/templates/criterios_automatizabilidad.md`, escribe `docs/proyectos/<slug>/automatizabilidad.json` (contrato en `specs/script-automatizabilidad.md`) y ejecuta:
   ```text
   python "<SKILL_DIR>/scripts/build_automatizabilidad.py" --json "docs/proyectos/<slug>/automatizabilidad.json" --output "docs/proyectos/<slug>/Analisis de Automatizabilidad <Nombre>.docx"
   ```
   Usa el veredicto y el score que imprime el script, sin cambiarlos. Es una recomendación: la decisión del paso 1 es del usuario.
1. Muestra los casos de uso detectados con su veredicto y espera la respuesta:
   ```text
   Se han identificado los siguientes Casos de Uso:

   [1] UC-01: <Título>
       -> Acotación técnica: <dependencia en una línea>
       -> Automatizabilidad: <veredicto> (score <N>/100, <nivel>) — <motivo>
   [2] UC-02: <Título>
       -> Acotación técnica: <dependencia en una línea>
       -> Automatizabilidad: <veredicto> (score <N>/100, <nivel>) — <motivo>

   ¿Cuáles de estos casos de uso son viables para ejecutar en esta fase?
   (Ingresa los números separados por coma, ej: 1, 2 o escribe 'todos')
   ```
2. Acepta solo números listados o `todos`. Ante una respuesta inválida, repite la lista.
3. Seleccionados = **VIABLES**. El resto = **DESCARTADOS (FUERA DE ALCANCE)**, cada uno con su justificación técnica.
4. Si no hay ningún viable, confirma con el usuario antes de seguir: solo se generará la propuesta (sin casos, historias ni diagrama).
