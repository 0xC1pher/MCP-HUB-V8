import os
import json
import logging
from typing import Dict, Any, Optional
from core.shared.token_manager import TokenBudgetManager

logger = logging.getLogger(__name__)

class MemoryHandler:
    """
    Maneja el almacenamiento persistente CRUD para el sistema MCP.
    Inspirado en la 'Memory Tool' de Claude para acumular conocimiento entre turnos y sesiones.
    """
    def __init__(self, config: Optional[Dict] = None, token_manager=None):
        # Valores por defecto si no hay config
        self.config = config or {
            "directory": "data/memories",
            "per_session": True,
            "max_optimize_size": 1024
        }
        self.memory_dir = self.config.get("directory", "data/memories")
        self.per_session = self.config.get("per_session", True)
        self.token_manager = token_manager or TokenBudgetManager()
        
        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir, exist_ok=True)
            logger.info(f"Directorio de memorias creado en: {self.memory_dir}")

    def _get_storage_path(self, file_path: str, session_id: Optional[str] = None) -> str:
        """Calcula la ruta física del archivo de memoria."""
        base_dir = self.memory_dir
        if self.per_session and session_id:
            base_dir = os.path.join(self.memory_dir, session_id)
            os.makedirs(base_dir, exist_ok=True)
        
        # Asegurar que el path no se salga del directorio base (prevención de Path Traversal)
        safe_name = os.path.basename(file_path)
        return os.path.join(base_dir, safe_name)

    def create(self, file_path: str, content: str, session_id: Optional[str] = None) -> str:
        """Crea o sobre-escribe una memoria."""
        path = self._get_storage_path(file_path, session_id)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Memoria guardada exitosamente: {file_path}"
        except Exception as e:
            logger.error(f"Error al crear memoria {file_path}: {str(e)}")
            return f"Error al guardar memoria: {str(e)}"

    def read(self, file_path: str, session_id: Optional[str] = None) -> str:
        """Lee el contenido de una memoria."""
        path = self._get_storage_path(file_path, session_id)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error al leer memoria {file_path}: {str(e)}")
                return f"Error al leer memoria: {str(e)}"
        return "Error: Memoria no encontrada."

    def read_optimized(self, file_path: str, max_tokens: int, session_id: Optional[str] = None) -> str:
        """Lee una memoria optimizando el uso de tokens mediante TOON."""
        content = self.read(file_path, session_id)
        if "Error:" in content:
            return content
        return self.token_manager.truncate_text(content, max_tokens)

    def update(self, file_path: str, content: str, session_id: Optional[str] = None) -> str:
        """Actualiza una memoria (alias de create para estandarizar CRUD)."""
        if "Error: Memoria no encontrada" in self.read(file_path, session_id):
            return "Error: No se puede actualizar una memoria inexistente."
        return self.create(file_path, content, session_id)

    def delete(self, file_path: str, session_id: Optional[str] = None) -> str:
        """Elimina una memoria física."""
        path = self._get_storage_path(file_path, session_id)
        if os.path.exists(path):
            try:
                os.remove(path)
                return f"Memoria eliminada: {file_path}"
            except Exception as e:
                logger.error(f"Error al eliminar memoria {file_path}: {str(e)}")
                return f"Error al eliminar: {str(e)}"
        return "Error: Memoria no encontrada."

    def list_memories(self, session_id: Optional[str] = None) -> list:
        """Limpia y lista las memorias disponibles para el contexto actual."""
        base_dir = self.memory_dir
        if self.per_session and session_id:
            base_dir = os.path.join(self.memory_dir, session_id)
            
        if not os.path.exists(base_dir):
            return []
            
        return [f for f in os.listdir(base_dir) if os.path.isfile(os.path.join(base_dir, f))]
