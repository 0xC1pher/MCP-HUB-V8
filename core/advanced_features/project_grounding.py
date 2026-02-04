import os
import logging
from typing import List, Dict, Optional
from core.storage.vector_engine import VectorEngine
from core.shared.token_manager import TokenBudgetManager

logger = logging.getLogger(__name__)

class ProjectGrounding:
    """
    Sistema de Grounding de Requerimientos y Visión de Proyecto.
    Asegura que las respuestas estén ancladas en los documentos de contexto del proyecto.
    Implementa técnicas anti-alucinación basadas en evidencia factual.
    """
    def __init__(self, config: Optional[Dict] = None, vector_engine=None, token_manager=None):
        self.config = config or {
            "directory": "data/project_context",
            "auto_index": True,
            "grounding_mode": "predictive"
        }
        self.context_dir = self.config.get("directory", "data/project_context")
        self.vector_engine = vector_engine or VectorEngine(config or {})
        self.token_manager = token_manager or TokenBudgetManager()
        
        if not os.path.exists(self.context_dir):
            os.makedirs(self.context_dir, exist_ok=True)
            
        self.context_cache = []
        self._load_all_context()

    def _load_all_context(self):
        """Carga y procesa todos los archivos de requerimientos y visión."""
        if not os.path.exists(self.context_dir):
            return

        self.context_cache = []
        for root, _, files in os.walk(self.context_dir):
            for file in files:
                if file.endswith(('.md', '.txt', '.json')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Chunking simple por ahora (en v9 avanzado usará el DynamicChunker)
                        self.context_cache.append({
                            "source": file,
                            "content": content,
                            "path": file_path
                        })
                    except Exception as e:
                        logger.error(f"Error cargando archivo de contexto {file}: {str(e)}")

    def get_grounding_evidence(self, query: str, top_k: int = 3) -> str:
        """
        Recupera evidencia relevante de los archivos de contexto para anclar la respuesta LLM.
        """
        if not self.context_cache:
            return "No se encontró evidencia factual en data/project_context/."

        try:
            query_vector = self.vector_engine.embed_query(query)
            scored_chunks = []
            
            for doc in self.context_cache:
                # Comparamos semánticamente la query con el contenido
                # En v9 avanzado esto se hace por chunks vectorizados en MP4
                doc_vector = self.vector_engine.embed_query(doc["content"][:2000]) # Grounding inicial
                similarity = self.vector_engine.cosine_similarity(query_vector, doc_vector)
                scored_chunks.append((similarity, doc))
            
            scored_chunks.sort(key=lambda x: x[0], reverse=True)
            top_docs = scored_chunks[:top_k]
            
            evidence = []
            for score, doc in top_docs:
                if score > 0.5: # Umbral de relevancia
                    evidence.append(f"--- Evidencia de {doc['source']} (Score: {score:.2f}) ---\n{doc['content']}")
            
            if not evidence:
                return "No se encontró evidencia relevante específica para esta consulta."
                
            return "\n\n".join(evidence)
            
        except Exception as e:
            logger.error(f"Error en grounding de proyecto: {str(e)}")
            return "Error al recuperar evidencia de grounding."

    def validate_against_vision(self, proposal: str) -> Dict:
        """
        Valida una propuesta o lógica contra la visión general del proyecto.
        Útil para asegurar que no se introducen lógicas externas no deseadas.
        """
        vision_docs = [d for d in self.context_cache if "vision" in d["source"].lower() or "roadmap" in d["source"].lower()]
        from core.advanced_features.factual_audit_jepa import FactualAuditJEPA
        self.auditor = FactualAuditJEPA(vector_engine=self.vector_engine)
        
    def validate_against_vision(self, proposal: str, query: str = "general alignment") -> Dict:
        """
        Valida una propuesta o lógica contra la visión general del proyecto.
        Usa los principios de JEPA para detectar desviaciones semánticas.
        """
        return self.auditor.audit_proposal(query, proposal)
