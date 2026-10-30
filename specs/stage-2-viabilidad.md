# Stage 2: Puerta de viabilidad

1. Muestra los casos de uso detectados y espera la respuesta:
   ```text
   Se han identificado los siguientes Casos de Uso:

   [1] UC-01: <Título>
       -> Acotación técnica: <dependencia en una línea>
   [2] UC-02: <Título>
       -> Acotación técnica: <dependencia en una línea>

   ¿Cuáles de estos casos de uso son viables para ejecutar en esta fase?
   (Ingresa los números separados por coma, ej: 1, 2 o escribe 'todos')
   ```
2. Acepta solo números listados o `todos`. Ante una respuesta inválida, repite la lista.
3. Seleccionados = **VIABLES**. El resto = **DESCARTADOS (FUERA DE ALCANCE)**, cada uno con su justificación técnica.
4. Si no hay ningún viable, confirma con el usuario antes de seguir: solo se generará la propuesta (sin casos, historias ni diagrama).
