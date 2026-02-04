# Roadmap Técnico: MCP Hub v9 (Joint Context Intelligence)

## Resumen de la Evolución v9
La versión 9 (Enero-Febrero 2026) transforma el MCP Hub de un recuperador de información (RAG) a un gestor de inteligencia contextual basado en **grounding factual** y **persistencia de largo plazo**.

## Arquitectura de Capas de Contexto (Priorización JEPA)

El sistema de grounding debe filtrar las respuestas basándose en estas capas, de mayor a menor autoridad:

1. **Capa 0: Manifiesto de Visión (`Vision.md`)**
   - Reglas inmutables del sistema.
   - Definición de límites (Contexto vs Negocio).

2. **Capa 1: Requerimientos de Proyecto (`project_context/*.md`)**
   - Especificaciones técnicas actuales.
   - Arquitectura y decisiones de diseño (v8 Tech Docs).

3. **Capa 2: Persistencia de Usuario (`memories/`)**
   - Decisiones tomadas en la sesión actual o previas.
   - Estilo de codificación y preferencias específicas.

4. **Capa 3: Skills y Conocimiento Semántico (`skills/`)**
   - Herramientas y paquetes de conocimiento reutilizables.
   - Documentación de APIs y librerías especializadas.

5. **Capa 4: Análisis de Código Dinámico (Vector Engine)**
   - El estado actual del sistema de archivos.

## Anti-Hallucination Protocol (AHP)
Para cada consulta crítica, el servidor v9 realizará:
1. **Context Grounding Check**: Invocar `ground_project_context` para buscar discrepancias con la visión o requerimientos.
2. **Confidence Calibration**: Evaluar si hay suficiente evidencia en las capas 0-2 antes de proponer cambios estructurales.
3. **Reasoning Trace**: En modo verbose, mostrar qué capa de contexto validó la decisión.

## Tareas Pendientes (Implementación Incremental)
- [x] Middlewares de persistencia (`MemoryHandler`).
- [x] Gestor de Skills semánticas (`SkillsManager`).
- [x] Herramientas de Grounding Factual (`ProjectGrounding`).
- [ ] Integración de calibración de confianza basada en embeddings (JEPA Stage 2).
- [ ] Optimización de Skills mediante compresión v8 MP4.

---
*Referencia para el agente: Si el usuario pide un cambio que contradice los requerimientos en `project_context/`, el agente DEBE advertir usando la evidencia del grounding.*
