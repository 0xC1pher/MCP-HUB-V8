import os
import json
import logging
from typing import List, Dict, Optional
from core.storage.vector_engine import VectorEngine
from core.shared.token_manager import TokenBudgetManager

logger = logging.getLogger(__name__)

class SkillsManager:
    """
    Gestiona paquetes de conocimiento reutilizables (Skills).
    Carga dinámicamente instrucciones avanzadas y contexto basado en la relevancia de la query.
    """
    def __init__(self, config: Optional[Dict] = None, vector_engine=None, token_manager=None):
        self.config = config or {
            "directory": "data/skills",
            "auto_load": True,
            "max_skills_per_query": 3
        }
        self.skills_dir = self.config.get("directory", "data/skills")
        self.max_skills = self.config.get("max_skills_per_query", 3)
        self.vector_engine = vector_engine or VectorEngine(config or {})
        self.token_manager = token_manager or TokenBudgetManager()
        
        if not os.path.exists(self.skills_dir):
            os.makedirs(self.skills_dir, exist_ok=True)
            
        self.skills_cache = {}
        self._refresh_cache()

    def _refresh_cache(self):
        """Escanea el directorio de skills y precarga metadatos."""
        if not os.path.exists(self.skills_dir):
            return

        for skill_folder in os.listdir(self.skills_dir):
            folder_path = os.path.join(self.skills_dir, skill_folder)
            if os.path.isdir(folder_path):
                skill_md = os.path.join(folder_path, "SKILL.md")
                if os.path.exists(skill_md):
                    try:
                        with open(skill_md, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        metadata_path = os.path.join(folder_path, "metadata.json")
                        metadata = {}
                        if os.path.exists(metadata_path):
                            with open(metadata_path, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                        
                        self.skills_cache[skill_folder] = {
                            "id": skill_folder,
                            "content": content,
                            "metadata": metadata,
                            "path": folder_path
                        }
                    except Exception as e:
                        logger.error(f"Error cargando skill {skill_folder}: {str(e)}")

    def get_relevant_skills(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        """
        Usa búsqueda semántica para encontrar las skills más relevantes para la query actual.
        Aplica los principios de JEPA al enfocarse en la representación semántica del contenido.
        """
        if not self.skills_cache:
            return []

        k = top_k or self.max_skills
        skill_ids = list(self.skills_cache.keys())
        skill_texts = [f"{s['id']} {s['content'][:500]}" for s in self.skills_cache.values()]
        
        try:
            # Simulamos el grounding semántico usando el VectorEngine existente
            # En v9 real, aquí se implementará el predictor JEPA
            scores = []
            query_vector = self.vector_engine.embed_query(query)
            
            for skill_id in skill_ids:
                # Si la skill tiene descripción en metadata, la usamos para el score
                search_text = self.skills_cache[skill_id]["metadata"].get("description", skill_id)
                skill_vector = self.vector_engine.embed_query(search_text)
                similarity = self.vector_engine.cosine_similarity(query_vector, skill_vector)
                scores.append((similarity, skill_id))
            
            # Ordenar por similitud y tomar top_k
            scores.sort(key=lambda x: x[0], reverse=True)
            relevant_ids = [s[1] for s in scores[:k] if s[0] > 0.6] # Umbral de confianza
            
            return [self.skills_cache[sid] for sid in relevant_ids]
            
        except Exception as e:
            logger.error(f"Error en búsqueda semántica de skills: {str(e)}")
            # Fallback a búsqueda por texto simple si falla el vector engine
            relevant = [s for s in self.skills_cache.values() if s["id"].lower() in query.lower()]
            return relevant[:k]

    def create_skill(self, skill_id: str, content: str, description: str = "") -> str:
        """Crea un nuevo paquete de skill."""
        folder_path = os.path.join(self.skills_dir, skill_id)
        os.makedirs(folder_path, exist_ok=True)
        
        with open(os.path.join(folder_path, "SKILL.md"), 'w', encoding='utf-8') as f:
            f.write(content)
            
        metadata = {"description": description, "id": skill_id}
        with open(os.path.join(folder_path, "metadata.json"), 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4)
            
        self._refresh_cache()
        return f"Skill '{skill_id}' creada exitosamente."
