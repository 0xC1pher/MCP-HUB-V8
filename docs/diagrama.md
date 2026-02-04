# Diagrama de Flujo v9: Inteligencia Contextual y Anti-Alucinación

```mermaid
flowchart TD
    A[Consulta Usuario] --> B[Orquestador v9]
    
    subgraph S1 [Fuentes de Conocimiento]
        C[Project Grounding<br/>vision.md / context.md]
        D[Memory Tool<br/>Preferencias / Historial]
        E[Skills Manager<br/>Conocimiento Reutilizable]
    end
    
    B --> C
    B --> D
    B --> E
    
    C --> F[Generación Preliminar<br/>con RAG]
    D --> F
    E --> F
    
    F --> G{Validación Factual<br/>Self-Consistency Check}
    
    G -- "Alucinación detectada" --> H[Corrección Iterativa<br/>Re-generación con constraints]
    H --> G
    
    G -- "Validado ✓" --> I[QA Audit Report<br/>Confianza + Fuentes Citadas]
    
    I --> J[Respuesta Final<br/>con transparencia]
    
    J --> K[Persistencia en Memoria<br/>para aprendizaje continuo]
    K --> D
    
    %% Estilos
    classDef generation fill:#f6b26b,stroke:#333
    classDef validation fill:#e06666,stroke:#333,color:white
    classDef output fill:#6aa84f,stroke:#333,color:white
    classDef feedback fill:#ffd966,stroke:#333,stroke-dasharray: 5 5
    
    class F generation
    class G,H validation
    class I,J output
    class K feedback
```

### 🔑 Componentes Críticos del Flujo

| Componente | Propósito anti-alucinación | Aplicación en Yari Medic |
|------------|----------------------------|-------------------------|
| **RAG integrado** | La respuesta se genera *siempre* anclada a documentos reales (no "desde cero") | Evita inventar módulos que no existen en `INSTALLED_APPS`. |
| **Self-Consistency Check** | El modelo se auto-cuestiona: *"¿Esta afirmación está respaldada por las fuentes?"* | Detecta si se está sugiriendo un framework ajeno a la arquitectura Django base. |
| **Bucle de corrección** | Si hay alucinación → **re-genera con constraints**, no entrega así | **Crucial:** La validación alimenta la generación antes de que el usuario vea el error. |
| **QA con fuentes citadas** | La respuesta incluye: *"Según vision.md, línea 42..."* | Transparencia total y trazabilidad de decisiones técnicas. |
| **Persistencia → Memoria** | Errores corregidos se guardan para evitar repetir alucinaciones | Aprendizaje incremental sobre las preferencias técnicas del proyecto. |