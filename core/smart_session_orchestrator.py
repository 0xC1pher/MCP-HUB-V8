"""
Smart Session Orchestrator - Intelligent Auto-Session Management
=================================================================

Este módulo provee gestión inteligente y automática de sesiones.
Detecta el contexto del proyecto/tarea y crea/reutiliza sesiones
sin modificar la lógica ni flujos existentes.

Características:
- Detección automática de proyecto por directorio de trabajo
- Clasificación inteligente de tipo de sesión (feature, bugfix, etc.)
- Reutilización de sesiones existentes cuando aplica
- Indexación automática de código si es necesario
- Persistencia completa usando las tools existentes
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SmartSessionOrchestrator:
    """
    Orquestador inteligente de sesiones que automatiza la gestión
    usando las tools internas existentes.
    
    NO modifica la lógica ni flujos existentes, solo los orquesta.
    """
    
    # Patrones para detectar tipo de sesión
    SESSION_TYPE_PATTERNS = {
        "bugfix": [
            r"fix\b", r"bug\b", r"error\b", r"issue\b", r"crash\b",
            r"broken\b", r"arregla", r"corrige", r"solucion"
        ],
        "feature": [
            r"add\b", r"new\b", r"create\b", r"implement\b", r"feature\b",
            r"agrega", r"nuevo", r"crear", r"implementa", r"funcionalidad"
        ],
        "refactor": [
            r"refactor", r"clean", r"reorganize", r"optimize",
            r"limpia", r"reorganiza", r"optimiza", r"mejora"
        ],
        "review": [
            r"review\b", r"check\b", r"verify\b", r"audit\b",
            r"revisa", r"verifica", r"audita"
        ]
    }
    
    # Tiempo máximo para considerar una sesión como "reciente"
    SESSION_RECENT_THRESHOLD_HOURS = 24
    
    def __init__(self, mcp_server=None, storage_dir: str = "data/smart_sessions"):
        """
        Inicializar el orquestador.
        
        Args:
            mcp_server: Instancia del servidor MCP v6 (opcional, se obtiene por singleton)
            storage_dir: Directorio para almacenar estado del orquestador
        """
        self.mcp_server = mcp_server
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Estado interno
        self._state_file = self.storage_dir / "orchestrator_state.json"
        self._state = self._load_state()
        
        # Cache de proyectos indexados
        self._indexed_projects: Dict[str, datetime] = {}
        
        logger.info("SmartSessionOrchestrator initialized")
    
    def _load_state(self) -> Dict[str, Any]:
        """Cargar estado persistente del orquestador."""
        if self._state_file.exists():
            try:
                with open(self._state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load state: {e}")
        
        return {
            "project_sessions": {},  # project_hash -> session_id
            "last_active_session": None,
            "indexed_projects": {},  # project_path -> last_index_time
            "statistics": {
                "sessions_created": 0,
                "sessions_reused": 0,
                "auto_indexes": 0
            }
        }
    
    def _save_state(self):
        """Guardar estado persistente."""
        try:
            with open(self._state_file, 'w', encoding='utf-8') as f:
                json.dump(self._state, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save state: {e}")
    
    def _get_mcp_server(self):
        """Obtener instancia del servidor MCP."""
        if self.mcp_server:
            return self.mcp_server
        
        # Intentar obtener por singleton
        try:
            from v6 import MCPServerV6
            self.mcp_server = MCPServerV6()
            return self.mcp_server
        except Exception as e:
            logger.error(f"Could not get MCP server: {e}")
            return None
    
    def _generate_project_hash(self, project_path: str) -> str:
        """Generar hash único para un proyecto."""
        normalized = os.path.normpath(project_path).lower()
        return hashlib.md5(normalized.encode()).hexdigest()[:12]
    
    def _detect_session_type(self, context: str) -> str:
        """
        Detectar tipo de sesión basado en contexto.
        
        Args:
            context: Texto del contexto (query, descripción, etc.)
            
        Returns:
            Tipo de sesión: feature, bugfix, refactor, review, general
        """
        context_lower = context.lower()
        
        # Buscar patrones
        type_scores = {stype: 0 for stype in self.SESSION_TYPE_PATTERNS}
        
        for session_type, patterns in self.SESSION_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, context_lower):
                    type_scores[session_type] += 1
        
        # Retornar el tipo con más coincidencias
        max_score = max(type_scores.values())
        if max_score > 0:
            for stype, score in type_scores.items():
                if score == max_score:
                    return stype
        
        return "general"
    
    def _generate_session_id(self, project_path: str, session_type: str) -> str:
        """
        Generar ID único y descriptivo para sesión.
        
        Args:
            project_path: Ruta del proyecto
            session_type: Tipo de sesión
            
        Returns:
            ID de sesión formateado
        """
        # Obtener nombre del proyecto
        project_name = Path(project_path).name
        
        # Limpiar nombre
        clean_name = re.sub(r'[^a-zA-Z0-9]', '-', project_name.lower())
        clean_name = re.sub(r'-+', '-', clean_name).strip('-')
        
        # Timestamp corto
        timestamp = datetime.now().strftime("%m%d-%H%M")
        
        return f"{clean_name}-{session_type}-{timestamp}"
    
    def _find_existing_session(self, project_path: str) -> Optional[str]:
        """
        Buscar sesión existente para un proyecto.
        
        Args:
            project_path: Ruta del proyecto
            
        Returns:
            ID de sesión existente o None
        """
        project_hash = self._generate_project_hash(project_path)
        
        # Verificar si hay sesión registrada para este proyecto
        if project_hash in self._state.get("project_sessions", {}):
            session_info = self._state["project_sessions"][project_hash]
            session_id = session_info.get("session_id")
            last_active = session_info.get("last_active")
            
            # Verificar si la sesión sigue siendo "reciente"
            if last_active:
                try:
                    last_active_dt = datetime.fromisoformat(last_active)
                    threshold = timedelta(hours=self.SESSION_RECENT_THRESHOLD_HOURS)
                    
                    if datetime.now() - last_active_dt < threshold:
                        # Verificar que la sesión aún existe en el servidor
                        server = self._get_mcp_server()
                        if server and hasattr(server, 'session_manager'):
                            sessions = server.session_manager.list_sessions()
                            if any(s.get('session_id') == session_id for s in sessions):
                                return session_id
                except Exception as e:
                    logger.warning(f"Error checking session recency: {e}")
        
        return None
    
    def _should_reindex(self, project_path: str) -> bool:
        """
        Determinar si un proyecto necesita re-indexación.
        
        Args:
            project_path: Ruta del proyecto
            
        Returns:
            True si necesita re-indexación
        """
        indexed = self._state.get("indexed_projects", {})
        
        if project_path not in indexed:
            return True
        
        last_indexed = indexed[project_path]
        try:
            last_indexed_dt = datetime.fromisoformat(last_indexed)
            # Re-indexar si pasaron más de 24 horas
            if datetime.now() - last_indexed_dt > timedelta(hours=24):
                return True
        except Exception:
            return True
        
        return False
    
    async def smart_initialize(
        self,
        project_path: Optional[str] = None,
        context: str = "",
        force_new_session: bool = False
    ) -> Dict[str, Any]:
        """
        Inicialización inteligente de sesión.
        
        Este método:
        1. Detecta o usa el proyecto especificado
        2. Determina si reutilizar sesión existente o crear nueva
        3. Detecta el tipo de sesión automáticamente
        4. Indexa código si es necesario
        5. Retorna información de la sesión activa
        
        Args:
            project_path: Ruta del proyecto (opcional, usa CWD si no se especifica)
            context: Contexto para detectar tipo de sesión
            force_new_session: Forzar creación de nueva sesión
            
        Returns:
            Dict con información de la sesión:
            {
                "session_id": str,
                "session_type": str,
                "project_path": str,
                "is_new": bool,
                "was_indexed": bool,
                "message": str
            }
        """
        result = {
            "session_id": None,
            "session_type": "general",
            "project_path": None,
            "is_new": False,
            "was_indexed": False,
            "message": ""
        }
        
        server = self._get_mcp_server()
        if not server:
            result["message"] = "Error: No MCP server available"
            return result
        
        # Determinar ruta del proyecto
        if not project_path:
            project_path = os.getcwd()
        
        project_path = os.path.normpath(project_path)
        result["project_path"] = project_path
        
        # Verificar si existe el directorio
        if not os.path.isdir(project_path):
            result["message"] = f"Error: Project path does not exist: {project_path}"
            return result
        
        # Buscar sesión existente (si no se fuerza nueva)
        existing_session = None
        if not force_new_session:
            existing_session = self._find_existing_session(project_path)
        
        if existing_session:
            # Reutilizar sesión existente
            result["session_id"] = existing_session
            result["is_new"] = False
            self._state["statistics"]["sessions_reused"] += 1
            
            # Obtener info de la sesión
            if hasattr(server, 'session_manager'):
                summary = server.session_manager.get_session_summary(existing_session)
                if summary:
                    result["session_type"] = summary.get("type", "general")
            
            result["message"] = f"Reusing existing session: {existing_session}"
            logger.info(f"Reusing session: {existing_session}")
        else:
            # Crear nueva sesión
            session_type = self._detect_session_type(context)
            session_id = self._generate_session_id(project_path, session_type)
            
            # Crear sesión usando la tool interna
            try:
                import asyncio
                if hasattr(server, '_create_session'):
                    create_result = await server._create_session({
                        'session_id': session_id,
                        'session_type': session_type,
                        'strategy': 'trimming'
                    })
                    
                    result["session_id"] = session_id
                    result["session_type"] = session_type
                    result["is_new"] = True
                    
                    # Registrar en estado
                    project_hash = self._generate_project_hash(project_path)
                    self._state["project_sessions"][project_hash] = {
                        "session_id": session_id,
                        "project_path": project_path,
                        "session_type": session_type,
                        "created_at": datetime.now().isoformat(),
                        "last_active": datetime.now().isoformat()
                    }
                    self._state["last_active_session"] = session_id
                    self._state["statistics"]["sessions_created"] += 1
                    
                    result["message"] = f"Created new {session_type} session: {session_id}"
                    logger.info(f"Created new session: {session_id} (type: {session_type})")
                else:
                    result["message"] = "Error: Server does not support session creation"
                    
            except Exception as e:
                result["message"] = f"Error creating session: {e}"
                logger.error(f"Session creation error: {e}")
        
        # Auto-indexar si es necesario
        if result["session_id"] and self._should_reindex(project_path):
            try:
                if hasattr(server, '_index_code'):
                    index_result = await server._index_code({
                        'directory': project_path,
                        'recursive': True
                    })
                    
                    result["was_indexed"] = True
                    self._state["indexed_projects"][project_path] = datetime.now().isoformat()
                    self._state["statistics"]["auto_indexes"] += 1
                    
                    logger.info(f"Auto-indexed project: {project_path}")
                    
            except Exception as e:
                logger.warning(f"Auto-indexing failed: {e}")
        
        # Actualizar last_active
        if result["session_id"]:
            project_hash = self._generate_project_hash(project_path)
            if project_hash in self._state.get("project_sessions", {}):
                self._state["project_sessions"][project_hash]["last_active"] = datetime.now().isoformat()
            self._state["last_active_session"] = result["session_id"]
        
        # Guardar estado
        self._save_state()
        
        return result
    
    def smart_initialize_sync(
        self,
        project_path: Optional[str] = None,
        context: str = "",
        force_new_session: bool = False
    ) -> Dict[str, Any]:
        """
        Versión síncrona de smart_initialize.
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.smart_initialize(project_path, context, force_new_session)
        )
    
    def get_current_session(self) -> Optional[str]:
        """Obtener ID de la sesión activa actual."""
        return self._state.get("last_active_session")
    
    def get_project_session(self, project_path: str) -> Optional[str]:
        """Obtener sesión asociada a un proyecto."""
        project_hash = self._generate_project_hash(project_path)
        session_info = self._state.get("project_sessions", {}).get(project_hash)
        return session_info.get("session_id") if session_info else None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas del orquestador."""
        return {
            "statistics": self._state.get("statistics", {}),
            "active_projects": len(self._state.get("project_sessions", {})),
            "indexed_projects": len(self._state.get("indexed_projects", {})),
            "current_session": self._state.get("last_active_session")
        }
    
    async def smart_query(
        self,
        query: str,
        project_path: Optional[str] = None,
        auto_session: bool = True
    ) -> Dict[str, Any]:
        """
        Query inteligente que auto-gestiona la sesión.
        
        Args:
            query: Query a ejecutar
            project_path: Ruta del proyecto (opcional)
            auto_session: Auto-crear/reutilizar sesión si no hay activa
            
        Returns:
            Resultado del query con información de sesión
        """
        session_id = self.get_current_session()
        session_info = None
        
        # Auto-inicializar sesión si es necesario
        if auto_session and not session_id:
            session_info = await self.smart_initialize(project_path, query)
            session_id = session_info.get("session_id")
        
        if not session_id:
            return {
                "error": "No active session",
                "suggestion": "Call smart_initialize() first"
            }
        
        server = self._get_mcp_server()
        if not server:
            return {"error": "No MCP server available"}
        
        # Ejecutar query con la sesión
        try:
            result = server._get_context({
                'query': query,
                'session_id': session_id,
                'top_k': 5,
                'min_score': 0.5
            })
            
            # Actualizar last_active
            if project_path:
                project_hash = self._generate_project_hash(project_path)
                if project_hash in self._state.get("project_sessions", {}):
                    self._state["project_sessions"][project_hash]["last_active"] = datetime.now().isoformat()
                    self._save_state()
            
            return {
                "session_id": session_id,
                "session_info": session_info,
                "result": result
            }
            
        except Exception as e:
            return {"error": str(e), "session_id": session_id}
    
    def clear_project_association(self, project_path: str) -> bool:
        """
        Limpiar asociación proyecto-sesión.
        
        Args:
            project_path: Ruta del proyecto
            
        Returns:
            True si se limpió correctamente
        """
        project_hash = self._generate_project_hash(project_path)
        
        if project_hash in self._state.get("project_sessions", {}):
            del self._state["project_sessions"][project_hash]
            self._save_state()
            return True
        
        return False
    
    def get_all_project_sessions(self) -> List[Dict[str, Any]]:
        """Obtener todas las asociaciones proyecto-sesión."""
        sessions = []
        for hash_id, info in self._state.get("project_sessions", {}).items():
            sessions.append({
                "hash": hash_id,
                **info
            })
        return sessions


# ============================================
# Factory function
# ============================================

_orchestrator_instance = None

def get_smart_orchestrator() -> SmartSessionOrchestrator:
    """Obtener instancia singleton del orquestador."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = SmartSessionOrchestrator()
    return _orchestrator_instance


# ============================================
# Convenience functions
# ============================================

def auto_session(project_path: Optional[str] = None, context: str = "") -> Dict[str, Any]:
    """
    Función de conveniencia para auto-inicializar sesión.
    
    Uso:
        from smart_session_orchestrator import auto_session
        
        result = auto_session("/path/to/project", "fixing login bug")
        print(f"Session: {result['session_id']}")
    """
    orchestrator = get_smart_orchestrator()
    return orchestrator.smart_initialize_sync(project_path, context)


def get_or_create_session(project_path: str, session_type: str = "general") -> str:
    """
    Obtener sesión existente o crear nueva para un proyecto.
    
    Args:
        project_path: Ruta del proyecto
        session_type: Tipo de sesión si se crea nueva
        
    Returns:
        ID de la sesión
    """
    orchestrator = get_smart_orchestrator()
    
    # Intentar obtener existente
    existing = orchestrator.get_project_session(project_path)
    if existing:
        return existing
    
    # Crear nueva
    result = orchestrator.smart_initialize_sync(project_path, session_type, force_new_session=True)
    return result.get("session_id", "")
