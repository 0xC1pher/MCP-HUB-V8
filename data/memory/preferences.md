# User Preferences & Persistent Memory (v9)

## Preferencias de Desarrollo
- **Idioma**: Español (técnico/profesional).
- **Estilo de Código**: Django Best Practices, KISS, DRY.
- **Frontend**: Tailwind CSS + HTMX + Crispy Forms.
- **Arquitectura**: Multi-tenant por FK (TenantModelMixin).

## Decisiones de Arquitectura Consolidadas
1. **No esquemas**: Se mantiene isolation por `clinica_id`.
2. **IA Local/MCP**: Priorizar el uso de herramientas MCP para contexto antes que alucinación creativa.
3. **Validación Recursiva**: El agente debe auto-corregirse antes de entregar resultados si detecta discrepancias con el grounding.

## Historial de Contexto Relevante
- [2026-02-03]: Implementación de Arquitectura v9 con Bucle Anti-Alucinación.
- [2026-02-03]: Renombrado de `contex.md` a `context.md` para estandarización.
