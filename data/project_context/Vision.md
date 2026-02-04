# Visión de Proyecto: MCP Hub v9 (Antigravity Core)

## Propósito Fundamental
MCP Hub es un sistema de gestión avanzada de contexto y persistencia semántica. Su objetivo es actuar como la memoria externa y el motor de razonamiento contextual para modelos de lenguaje a gran escala, permitiendo sesiones de desarrollo coherentes, profundas y libres de alucinaciones.

## Principios Centrales (Reglas de Oro)

1. **Gestión de Contexto, NO de Negocio**: 
   - El sistema es agnóstico a las reglas de negocio, modelos de bases de datos de aplicaciones externas o lógica comercial.
   - Su dominio es la *estructura del conocimiento*, los *vínculos entre entidades de código* y la *persistencia de la intención del usuario*.

2. **Memoria Persistente y Evolutiva**:
   - Utiliza `memory_tool` para acumular datos específicos entre turnos.
   - Utiliza `skills_tool` para paquetes de conocimiento reutilizables que no deben perderse entre proyectos.

3. **Grounding Factual (Anti-Alucinaciones)**:
   - Toda respuesta crítica debe ser validada contra este directorio de contexto (`data/project_context/`).
   - Se prioriza la evidencia encontrada en requerimientos sobre la generación creativa del modelo.

4. **Preservación de Flujos**:
   - No eliminar lógica existente.
   - Expandir mediante la adición de capas (como la capa JEPA de predicción semántica) sin romper la base v6/v7 estable.

5. **Optimización Inteligente (TOON)**:
   - El contexto es un recurso finito. El sistema debe triturar, resumir y priorizar información para maximizar la utilidad del budget de tokens.

## Tecnologías y Metodología (Roadmap v9)
- **JEPA (Joint Embedding Predictive Architecture)**: Predicción de representaciones semánticas para manejar incertidumbre.
- **RAG Avanzado**: Grounding predictivo en archivos .md y de requerimientos.
- **Skills Modulares**: Inspirado en las Agent Skills de Claude para portabilidad de conocimiento.
- **Persistencia en .mp4**: Almacenamiento optimizado de vectores de contexto.

---
*Este documento es la referencia base para la herramienta `ground_project_context`.*
