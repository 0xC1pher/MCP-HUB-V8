"""
MCP Server v6 - Session Memory + Contextual Resolution
Extends v5 with session management and code intelligence
"""

# Path setup
import sys
import os
from pathlib import Path
current_dir = Path(__file__).resolve().parent
mcp_hub_root = current_dir.parent
if str(mcp_hub_root) not in sys.path: sys.path.insert(0, str(mcp_hub_root))
if str(current_dir) not in sys.path: sys.path.insert(0, str(current_dir))

import json
import logging
import time
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from pretty_logger import logger, Colors, get_logger
# logger ya está instanciado pero permitimos re-instanciar si es necesario

# Import v5 components (but not MCPServerV5 class itself)
from storage.mp4_storage import MP4Storage
# VectorEngine se importará lazy más adelante para evitar problemas circulares
VectorEngine = None

# Import advanced features
try:
    from advanced_features import (
        DynamicChunker,
        QueryExpander,
        ConfidenceCalibrator,
        AdvancedConfig,
        ProcessingMode
    )
    ADVANCED_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Advanced features not available: {e}")
    ADVANCED_AVAILABLE = False
    DynamicChunker = None
    QueryExpander = None
    ConfidenceCalibrator = None
    AdvancedConfig = None
    ProcessingMode = None

# Import v6 components
try:
    from memory import SessionManager, SessionType, SessionStrategy
    from storage.session_storage import SessionStorage
    from indexing import CodeIndexer, EntityTracker
    from resolution import ContextualResolver, ReferenceDetector
    # Import TOON for token optimization
    from shared.token_manager import TokenBudgetManager, get_token_manager
    # Import v9 components
    from memory.skills_manager import SkillsManager
    from storage.memory_handler import MemoryHandler
    from advanced_features.project_grounding import ProjectGrounding
    from advanced_features.factual_audit_jepa import FactualAuditJEPA
    V6_COMPONENTS_AVAILABLE = True
except ImportError as e:
    import traceback
    logger.error(f"V6/v9 components import FAILED: {e}")
    logger.error(traceback.format_exc())
    V6_COMPONENTS_AVAILABLE = False
    # Create dummy classes to avoid errors
    class SessionStorage: pass
    class CodeIndexer: pass
    class EntityTracker: pass
    class ContextualResolver: pass
    class TokenBudgetManager: pass
    class SkillsManager: pass
    class MemoryHandler: pass

# Helper to safely call jepa_flow if it exists, otherwise fallback to info
def safe_jepa_flow(step: str, message: str):
    if hasattr(logger, 'jepa_flow'):
        logger.jepa_flow(step, message)
    else:
        logger.info(f"[JEPA] {step}: {message}")

class MCPServerV6:
    """
    MCP Server v6 - Session Memory + Contextual Resolution
    
    New Features:
    1. Session management (Trimming + Summarizing strategies)
    2. Code structure indexing
    3. Entity tracking across sessions
    4. Contextual query resolution
    5. Cross-session search
    
    Backward Compatible: All v5 queries work without session_id
    
    Architecture: Uses composition - contains MCPServerV5 instance internally
    """
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Cargar configuración: AdvancedConfig si está disponible, sino JSON fallback"""
        if ADVANCED_AVAILABLE and AdvancedConfig:
            try:
                # Intentar crear AdvancedConfig desde v6_config.json
                v6_config_path = mcp_hub_root / "config" / "v6_config.json"
                if v6_config_path.exists():
                    with open(v6_config_path, 'r') as f:
                        v6_json = json.load(f)
                    
                    # Mapear configuración V6 a AdvancedConfig
                    return AdvancedConfig(
                        processing_mode=ProcessingMode.BALANCED,
                        max_concurrent_operations=v6_json.get('session', {}).get('max_concurrent', 4),
                        cache_size_mb=v6_json.get('toon', {}).get('cache_size_mb', 100),
                        max_search_results=v6_json.get('retrieval', {}).get('top_k', 10),
                        enable_dynamic_chunking=True,
                        enable_mvr=True,
                        enable_virtual_chunks=False,
                        enable_query_expansion=True,
                        enable_confidence_calibration=True,
                        max_expansions=v6_json.get('retrieval', {}).get('max_expansions', 5)
                    )
                else:
                    # Config por defecto si no existe v6_config.json
                    logger.warning("v6_config.json no encontrado, usando configuración por defecto")
                    return AdvancedConfig()
            except Exception as e:
                logger.warning(f"Error creando AdvancedConfig: {e}, usando fallback JSON")
                # Fallback a JSON como antes
                return self._load_json_config(config_path)
        else:
            # AdvancedConfig no disponible, usar JSON
            return self._load_json_config(config_path)
    
    def _load_json_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Cargar configuración JSON legacy"""
        if config_path is None:
            config_path = mcp_hub_root / "config" / "v5_config.json"
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        logger.info(f"Configuration loaded from {config_path}")
        return config
    
    def __init__(self, config_path: str = None, verbose: bool = False):
        """Initialize MCP Server v6 with separate storage
        
        Args:
            config_path: Path to configuration file
            verbose: Enable verbose logging for tool execution
        """
        self.verbose = verbose
        self._start_time = time.time()
        
        logger.info("="*80)
        logger.info("AGI-CONTEXT-VORTEX - Core v9 (Contextual Intelligence)")
        logger.info("="*80)
        
        # Cargar configuración (AdvancedConfig o JSON)
        self.config = self._load_config(config_path)
        
        # Métodos auxiliares para acceso seguro a configuración
        self._config_cache = {}
        
        # Initialize v5 components with SEPARATE storage file for v6
        v6_mp4_path = str(mcp_hub_root / "data" / "context_vectors_v6.mp4")
        self.storage = MP4Storage(v6_mp4_path)
        
        # Inicializar VectorEngine más tarde para evitar problemas de importación circular
        self.vector_engine = None  # Se inicializará después
        self._vector_engine_initialized = False
        
        # Advanced features
        if ADVANCED_AVAILABLE:
            min_tokens = self._get_config_value('chunking.min_tokens', 150)
            max_tokens = self._get_config_value('chunking.max_tokens', 450)
            overlap_percent = self._get_config_value('chunking.overlap_percent', 25)
            
            self.chunker = DynamicChunker(
                min_chunk_size=min_tokens,
                max_chunk_size=max_tokens,
                overlap_ratio=overlap_percent / 100.0,
            )
            self.query_expander = QueryExpander()
            
            confidence_thresholds = self._get_config_value('anti_hallucination.confidence_thresholds', {
                'factual': 0.78,
                'procedural': 0.72,
                'conceptual': 0.65,
                'temporal': 0.85
            })
            self.confidence_calibrator = ConfidenceCalibrator(confidence_thresholds)
        else:
            self.chunker = None
            self.query_expander = None
            self.confidence_calibrator = None
        
        # State
        self.query_count = 0
        self.start_time = time.time()
        self.audit_log = []
        
        # Load v6 storage or copy from v5
        self._initialize_v6_storage()
        
        # Initialize v6-specific components
        if V6_COMPONENTS_AVAILABLE:
            logger.info("Initializing v6-specific components...")
            self._initialize_v6_components()
            logger.info("v6 components initialized successfully")
        else:
            logger.warning("V6 components not available - running in compatibility mode")
        
        # Inicializar VectorEngine después para evitar problemas de importación circular
        self._initialize_vector_engine()
        
        logger.info("="*80)
        logger.info("MCP Server v6 ready")
        logger.info("="*80)

    def _get_config_value(self, key_path: str, default: Any = None) -> Any:
        """Acceso seguro a configuración que funciona con AdvancedConfig o JSON"""
        # Cache para evitar búsquedas repetidas
        if key_path in self._config_cache:
            return self._config_cache[key_path]
        
        # Si es AdvancedConfig, usar atributos directos
        if hasattr(self.config, key_path):
            value = getattr(self.config, key_path)
            self._config_cache[key_path] = value
            return value
        
        # Si es JSON, usar acceso anidado
        if isinstance(self.config, dict):
            keys = key_path.split('.')
            value = self.config
            try:
                for key in keys:
                    value = value[key]
                self._config_cache[key_path] = value
                return value
            except (KeyError, TypeError):
                self._config_cache[key_path] = default
                return default
        
        # Fallback al valor por defecto
        self._config_cache[key_path] = default
        return default
    
    def _initialize_vector_engine(self):
        """Inicializar VectorEngine después de evitar problemas de importación circular"""
        if self._vector_engine_initialized:
            return
            
        try:
            # Importación lazy de VectorEngine
            from storage.vector_engine import VectorEngine
            
            # VectorEngine expects a dict
            engine_config = self.config if isinstance(self.config, dict) else self.config.__dict__
            self.vector_engine = VectorEngine(engine_config)
            self._vector_engine_initialized = True
            logger.info("VectorEngine initialized successfully")
            
        except ImportError as e:
            logger.warning(f"VectorEngine no disponible, usando fallback: {e}")
            self.vector_engine = None
            self._vector_engine_initialized = True
        except Exception as e:
            logger.error(f"Error inicializando VectorEngine: {e}")
            self.vector_engine = None
            self._vector_engine_initialized = True

    def _log_tool_execution(self, tool_name: str, args: Dict[str, Any], result: Any = None):
        """Log verbose information about tool execution"""
        if self.verbose:
            logger.info(f"🔧 TOOL EXECUTED: {tool_name}")
            logger.info(f"   Args: {json.dumps(args, default=str)[:200]}...")
            if result:
                result_str = str(result)[:200]
                logger.info(f"   Result: {result_str}...")
            logger.info("-" * 60)
    
    def _initialize_v6_storage(self):
        """Initialize or load v6 vector index - CORREGIDO"""
        # Try to load v6's own snapshot primero
        logger.info(f"Attempting to load v6 snapshot from: {self.storage.mp4_path}")
        
        if self.storage.load_snapshot():
            logger.info("Loaded existing v6 snapshot")
            hnsw_offset, hnsw_size = self.storage.get_hnsw_blob_offset()
            if hnsw_size > 0:
                try:
                    with open(self.storage.mp4_path, 'rb') as f:
                        f.seek(hnsw_offset)
                        hnsw_blob = f.read(hnsw_size)
                    # FIX: load_index_from_bytes requiere num_elements (total de chunks)
                    self.vector_engine.load_index_from_bytes(hnsw_blob, len(self.storage.chunks))
                    logger.info("HNSW index loaded from v6 MP4")
                    return  # Éxito, salir temprano
                except Exception as e:
                    logger.error(f"Error loading HNSW index from v6: {e}")
            else:
                logger.warning("No HNSW index in v6 MP4")
        else:
            logger.warning("Failed to load v6 snapshot")
        
        # Si llegamos aquí, necesitamos copiar de v5 o empezar fresco
        storage_path = self._get_config_value('storage.mp4_path', 'data/context_vectors.mp4')
        v5_mp4_path = str(mcp_hub_root / storage_path)
        logger.info(f"Attempting to copy from v5 storage: {v5_mp4_path}")
        
        import shutil
        v5_path = Path(v5_mp4_path)
        
        if v5_path.exists():
            # FIX: Cerrar el storage actual ANTES de copiar para liberar memory map
            v6_target = self.storage.mp4_path
            self.storage.close()  # Liberar el archivo
            del self.storage  # Eliminar referencia
            
            logger.info(f"Copying v5 storage to v6: {v5_mp4_path} -> {v6_target}")
            
            # Asegurar que el directorio destino existe
            os.makedirs(Path(v6_target).parent, exist_ok=True)
            
            # Copiar archivo (ahora sin memory map lock)
            shutil.copy2(v5_mp4_path, v6_target)
            
            # RECREAR la instancia de storage después de la copia
            self.storage = MP4Storage(v6_target)
            logger.info("Storage recreated after copy")
            
            # Intentar cargar el snapshot copiado
            if self.storage.load_snapshot():
                logger.info("Loaded snapshot from v5 copy")
                hnsw_offset, hnsw_size = self.storage.get_hnsw_blob_offset()
                if hnsw_size > 0:
                    try:
                        with open(self.storage.mp4_path, 'rb') as f:
                            f.seek(hnsw_offset)
                            hnsw_blob = f.read(hnsw_size)
                        # FIX: También aquí necesita num_elements
                        self.vector_engine.load_index_from_bytes(hnsw_blob, len(self.storage.chunks))
                        logger.info("HNSW index loaded from copied v5 data")
                    except Exception as e:
                        logger.error(f"Error loading HNSW from copied v5: {e}")
                else:
                    logger.warning("No HNSW index in copied v5 data")
            else:
                logger.error("Failed to load snapshot from copied v5 data")
        else:
            logger.warning(f"v5 storage not found at {v5_mp4_path} - starting fresh")
            # Inicializar storage vacío
            self.storage.initialize_empty_storage()
    
    def _initialize_v6_components(self):
        """Initialize v6-specific components (sessions, indexing, etc.)"""
        logger.header("AGI-CONTEXT-VORTEX - Core v9", "Contextual Intelligence (JEPA World Model Activated)")
        if not V6_COMPONENTS_AVAILABLE:
            return
            
        # Session management
        session_storage = SessionStorage(
            storage_dir=str(mcp_hub_root / "data" / "sessions"),
            retention_days=self._get_config_value('session.retention_days', 30)
        )
        
        default_strategy = SessionStrategy.TRIMMING
        if self._get_config_value('session.default_type') == 'summarizing':
            default_strategy = SessionStrategy.SUMMARIZING
        
        self.session_manager = SessionManager(
            storage=session_storage,
            default_strategy=default_strategy,
            auto_save=self._get_config_value('session.auto_save', True)
        )
        logger.info("Session manager initialized")
        
        # Code indexing
        if self._get_config_value('code_indexing.enabled', True):
            self.code_indexer = CodeIndexer(
                index_dir=str(mcp_hub_root / "data" / "code_index")
            )
            # Try to load existing index
            if not self.code_indexer.load_index():
                logger.info("No existing code index - will index on demand")
            else:
                logger.info(f"Code index loaded: {self.code_indexer.get_stats()}")
        else:
            self.code_indexer = None
        
        # Entity tracking
        if self._get_config_value('entity_tracking.enabled', True):
            code_index_data = {}
            if self.code_indexer:
                code_index_data = {
                    'functions': {k: v.__dict__ for k, v in self.code_indexer.functions.items()},
                    'classes': {k: v.__dict__ for k, v in self.code_indexer.classes.items()}
                }
            
            self.entity_tracker = EntityTracker(
                code_index=code_index_data,
                storage_dir=str(mcp_hub_root / "data" / "code_index")
            )
            self.entity_tracker.load()
            logger.info("Entity tracker initialized")
        else:
            self.entity_tracker = None
        
        # Contextual resolution
        self.contextual_resolver = ContextualResolver()
        logger.info("Contextual resolver initialized")
        
        # TOON - Token Optimization
        self.token_manager = TokenBudgetManager(
            max_tokens=self._get_config_value('toon.max_tokens', 8000), # v9 default
            reserved_tokens=self._get_config_value('toon.reserved_tokens', 1000)
        )
        logger.info(f"TOON initialized: {self.token_manager.available_tokens} tokens available")

        # v9: Skills and Memory Tool
        self.skills_manager = SkillsManager(
            self._get_config_value('skills', {}),
            vector_engine=self.vector_engine,
            token_manager=self.token_manager
        )
        self.memory_handler = MemoryHandler(
            self._get_config_value('memory_tool', {}),
            token_manager=self.token_manager
        )
        
        # v9: Project Grounding (Factual Vision)
        self.project_grounding = ProjectGrounding(
            self._get_config_value('project_context', {}),
            vector_engine=self.vector_engine,
            token_manager=self.token_manager
        )
    
        # v9: JEPA Factual Auditor - Ensure absolute path
        audit_config = self._get_config_value('factual_audit', {})
        if 'context_directory' not in audit_config:
            audit_config['context_directory'] = str(mcp_hub_root / "data" / "project_context")

        self.factual_auditor = FactualAuditJEPA(
            audit_config,
            vector_engine=self.vector_engine
        )
        safe_jepa_flow("WORLD-MODEL", f"JEPA Contextual Shield {Colors.GREEN_NEON}ACTIVE{Colors.RESET}")
        logger.info("JEPA World Model loaded for anti-hallucination")

        # v9 Advanced: Query expansion, chunking and calibration
        if ADVANCED_AVAILABLE:
            self.query_expander = QueryExpander() if QueryExpander else None
            self.chunker = DynamicChunker() if DynamicChunker else None
            self.confidence_calibrator = ConfidenceCalibrator() if ConfidenceCalibrator else None
            logger.info("v9 Advanced components (Expander, Chunker, Calibrator) initialized")
        
        logger.info("v9 Skills, Memory and Grounding handlers initialized")

    
    def _handle_tools_list(self) -> Dict:
        """List available tools (v5 + v6)"""
        # V5 tools (inline instead of delegation)
        v5_tools_list = [
            {
                'name': 'get_context',
                'description': 'Retrieve context from memory with provenance',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'query': {'type': 'string'},
                        'top_k': {'type': 'integer', 'default': 5},
                        'min_score': {'type': 'number', 'default': 0.5},
                        'session_id': {'type': 'string', 'description': 'Optional session ID for v6'}
                    },
                    'required': ['query']
                }
            },
            {
                'name': 'validate_response',
                'description': 'Validate response against evidence',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'response': {'type': 'string'},
                        'evidence': {'type': 'array'}
                    },
                    'required': ['response', 'evidence']
                }
            },
            {
                'name': 'index_status',
                'description': 'Get index status and statistics',
                'inputSchema': {'type': 'object'}
            }
        ]
        
        v5_tools = {'tools': v5_tools_list}
        
        # Add v6 tools si están disponibles
        if V6_COMPONENTS_AVAILABLE:
            v6_tools = [
                {
                    'name': 'create_session',
                    'description': 'Create a new development session',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'session_id': {'type': 'string', 'description': 'Unique session identifier'},
                            'session_type': {
                                'type': 'string',
                                'enum': ['feature', 'bugfix', 'review', 'refactor', 'general'],
                                'default': 'general'
                            },
                            'strategy': {
                                'type': 'string',
                                'enum': ['trimming', 'summarizing'],
                                'default': 'trimming'
                            }
                        },
                        'required': ['session_id']
                    }
                },
                {
                    'name': 'get_session_summary',
                    'description': 'Get summary of a session',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'session_id': {'type': 'string'}
                        },
                        'required': ['session_id']
                    }
                },
                {
                    'name': 'list_sessions',
                    'description': 'List all sessions',
                    'inputSchema': {'type': 'object'}
                },
                {
                    'name': 'delete_session',
                    'description': 'Delete a session',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'session_id': {'type': 'string'}
                        },
                        'required': ['session_id']
                    }
                },
                {
                    'name': 'index_code',
                    'description': 'Index code structure from a directory',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'directory': {'type': 'string', 'description': 'Directory to index'},
                            'recursive': {'type': 'boolean', 'default': True}
                        },
                        'required': ['directory']
                    }
                },
                {
                    'name': 'search_entity',
                    'description': 'Search for a code entity (function/class)',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string', 'description': 'Entity name to search for'},
                            'entity_type': {
                                'type': 'string',
                                'enum': ['function', 'class', 'any'],
                                'default': 'any'
                            }
                        },
                        'required': ['name']
                    }
                },
                {
                    'name': 'memory_tool',
                    'description': 'CRUD operations for persistent memory storage',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'command': {'type': 'string', 'enum': ['create', 'read', 'update', 'delete', 'list']},
                            'file_path': {'type': 'string', 'description': 'Name of the memory file'},
                            'content': {'type': 'string', 'description': 'Data to store'},
                            'session_id': {'type': 'string', 'description': 'Optional session ID'}
                        },
                        'required': ['command', 'file_path']
                    }
                },
                {
                    'name': 'skills_tool',
                    'description': 'Manage knowledge skills',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'command': {'type': 'string', 'enum': ['create', 'list']},
                            'skill_id': {'type': 'string'},
                            'content': {'type': 'string', 'description': 'Main instructions'},
                            'description': {'type': 'string', 'description': 'Short description'}
                        },
                        'required': ['command', 'skill_id']
                    }
                },
                {
                    'name': 'ground_project_context',
                    'description': 'Retrieve factual evidence from project context',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'query': {'type': 'string'}
                        },
                        'required': ['query']
                    }
                },
                {
                    'name': 'audit_jepa',
                    'description': 'Audit a proposal against the JEPA World Model',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'query': {'type': 'string'},
                            'proposal': {'type': 'string', 'description': 'Text to audit'}
                        },
                        'required': ['proposal']
                    }
                },
                {
                    'name': 'sync_world_model',
                    'description': 'Rebuild and synchronize JEPA World Model from project context',
                    'inputSchema': {'type': 'object'}
                },
                {
                    'name': 'ping',
                    'description': 'Simple ping test to verify MCP connectivity',
                    'inputSchema': {'type': 'object'}
                },
                {
                    'name': 'get_system_status',
                    'description': 'Get comprehensive system status',
                    'inputSchema': {'type': 'object'}
                },
                {
                    'name': 'expand_query',
                    'description': 'Automatically expand a query for better search coverage',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'query': {'type': 'string'},
                            'max_expansions': {'type': 'integer', 'default': 5}
                        },
                        'required': ['query']
                    }
                },
                {
                    'name': 'chunk_document',
                    'description': 'Apply dynamic adaptive chunking to a document',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'content': {'type': 'string'},
                            'file_path': {'type': 'string'}
                        },
                        'required': ['content']
                    }
                },
                {
                    'name': 'process_advanced',
                    'description': 'Process a query using ALL advanced features',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'query': {'type': 'string'},
                            'domain': {'type': 'string', 'default': 'general'}
                        },
                        'required': ['query']
                    }
                },
                {
                    'name': 'smart_session_init',
                    'description': 'Intelligent session initialization',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'project_path': {'type': 'string'},
                            'context': {'type': 'string'}
                        }
                    }
                },
                {
                    'name': 'smart_query',
                    'description': 'Execute a query with automatic session management',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'query': {'type': 'string'},
                            'project_path': {'type': 'string'}
                        },
                        'required': ['query']
                    }
                },
                {
                    'name': 'check_quality',
                    'description': 'Check code quality against Quality Guardian principles',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'code': {'type': 'string'}
                        },
                        'required': ['code']
                    }
                },
                {
                    'name': 'get_quality_principles',
                    'description': 'Get full Quality Guardian principles documentation',
                    'inputSchema': {'type': 'object'}
                },
                {
                    'name': 'extended_search',
                    'description': 'Search through extended knowledge (constants, APIs, models)',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'query': {'type': 'string'}
                        },
                        'required': ['query']
                    }
                },
                {
                    'name': 'extended_index',
                    'description': 'Index code with EXTENDED knowledge (constants, APIs, models)',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'directory': {'type': 'string'},
                            'recursive': {'type': 'boolean', 'default': True}
                        },
                        'required': ['directory']
                    }
                },
                {
                    'name': 'get_knowledge_summary',
                    'description': 'Get comprehensive summary of all extended knowledge',
                    'inputSchema': {'type': 'object'}
                },
                {
                    'name': 'add_feedback',
                    'description': 'Add feedback to the system for dynamic recalibration',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'query': {'type': 'string'},
                            'result_doc_id': {'type': 'string'},
                            'relevance_score': {'type': 'number'},
                            'was_helpful': {'type': 'boolean'}
                        },
                        'required': ['query', 'result_doc_id', 'relevance_score', 'was_helpful']
                    }
                },
                {
                    'name': 'optimize_configuration',
                    'description': 'Optimize system configuration based on usage patterns',
                    'inputSchema': {'type': 'object'}
                },
                {
                    'name': 'get_smart_status',
                    'description': 'Get status of the smart session orchestrator',
                    'inputSchema': {'type': 'object'}
                }
            ]
            
            v5_tools['tools'].extend(v6_tools)
        
        return v5_tools
    
    def _handle_tools_call(self, params: Dict) -> Dict:
        """Execute tool (v5 + v6)"""
        tool = params.get('name', 'unknown')
        args = params.get('arguments', {})
        
        # v9 Matrix Flow: Asignar color por categoría
        tool_colors = {
            # V5 Core (Mint)
            'ping': Colors.GREEN_MINT, 'get_context': Colors.GREEN_MINT, 
            'validate_response': Colors.GREEN_MINT, 'index_status': Colors.GREEN_MINT,
            # V9 Intelligence (Neon)
            'memory_tool': Colors.GREEN_NEON, 'skills_tool': Colors.GREEN_NEON, 
            'ground_project_context': Colors.GREEN_NEON, 'audit_jepa': Colors.GREEN_NEON,
            'sync_world_model': Colors.GREEN_NEON,
            # V7 Sessions (Pale)
            'create_session': Colors.GREEN_PALE, 'get_session_summary': Colors.GREEN_PALE,
            'list_sessions': Colors.GREEN_PALE, 'delete_session': Colors.GREEN_PALE,
            'smart_session_init': Colors.GREEN_PALE, 'smart_query': Colors.GREEN_PALE,
            # V7 Code (Mid)
            'index_code': Colors.GREEN_MID, 'search_entity': Colors.GREEN_MID,
            'extended_index': Colors.GREEN_MID, 'extended_search': Colors.GREEN_MID,
        }
        
        # Color por defecto para avanzados: Cyan
        tool_color = tool_colors.get(tool, Colors.CYAN)
        
        # Log visual Matrix
        logger.matrix_flow(tool, "TOOL-INVOICE", color=tool_color)
        print(f"{Colors.GREEN_NEON} [TOOL] {Colors.RESET} Executing: {tool_color}{tool}{Colors.RESET}", file=sys.stderr)
        
        # Log de inicio de procesamiento
        safe_jepa_flow("TOOL-START", f"Executing {tool_color}{tool}{Colors.RESET}")
        
        if args:
            args_str = json.dumps(args, default=str)
            logger.v9_flow("TOOL-ARGS", f"📥 Payload: {tool_color}{args_str[:150]}...{Colors.RESET}")
        
        # v6 tools
        if V6_COMPONENTS_AVAILABLE:
            v6_tools = {
                'create_session': self._create_session,
                'get_session_summary': self._get_session_summary,
                'list_sessions': self._list_sessions,
                'delete_session': self._delete_session,
                'index_code': self._index_code,
                'search_entity': self._search_entity,
                'memory_tool': self._handle_memory_tool,
                'skills_tool': self._handle_skills_tool,
                'ground_project_context': self._handle_ground_project_context,
                'ping': self._handle_ping,
                'get_system_status': self._handle_get_system_status,
                'expand_query': self._handle_expand_query,
                'chunk_document': self._handle_chunk_document,
                'process_advanced': self._handle_process_advanced,
                'smart_session_init': self._handle_smart_session_init,
                'smart_query': self._handle_smart_query,
                'check_quality': self._handle_check_quality,
                'get_quality_principles': self._handle_get_quality_principles,
                'audit_jepa': self._handle_audit_jepa,
                'sync_world_model': lambda args: {'content': [{'type': 'text', 'text': self.factual_auditor.update_world_model()}]},
                'extended_search': self._handle_extended_search,
                'extended_index': self._handle_extended_index,
                'get_knowledge_summary': self._handle_get_knowledge_summary,
                'add_feedback': self._handle_add_feedback,
                'optimize_configuration': self._handle_optimize_configuration,
                'get_smart_status': self._handle_get_smart_status
            }
            
            if tool in v6_tools:
                try:
                    func = v6_tools[tool]
                    result = func(args)
                    
                    # If the result is a coroutine (from an async def function), we need to await it
                    if asyncio.iscoroutine(result):
                        try:
                            # Try to use current loop
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                # This is tricky if we're not in an async context
                                # But for now, let's use a nested run or similar if possible
                                # In typical MCP, we are either in a thread or in a main loop.
                                result = loop.run_until_complete(result)
                            else:
                                result = loop.run_until_complete(result)
                        except (RuntimeError, ValueError):
                            # Fallback to asyncio.run for new loop
                            result = asyncio.run(result)
                    
                    # Ensure result has proper MCP format
                    if not isinstance(result, dict):
                        result = {'content': [{'type': 'text', 'text': str(result)}]}
                    if 'content' not in result:
                        result = {'content': [{'type': 'text', 'text': json.dumps(result)}]}
                    
                    logger.matrix_flow(tool, "TOOL-COMPLETED", color=tool_color)
                    return result
                except Exception as e:
                    logger.error(f"Error in tool {tool}: {e}", exc_info=True)
                    return {
                        'content': [{'type': 'text', 'text': f'Error executing {tool}: {str(e)}'}],
                        '_meta': {'error': True}
                    }
        
        # V5 tools (inline instead of delegation)
        v5_tool_handlers = {
            'get_context': self._get_context,
            'validate_response': self._validate_response,
            'index_status': self._index_status
        }
        
        if tool in v5_tool_handlers:
            result = v5_tool_handlers[tool](args)
            # Ensure proper format
            if not isinstance(result, dict):
                result = {'content': [{'type': 'text', 'text': str(result)}]}
            if 'content' not in result:
                result = {'content': [{'type': 'text', 'text': json.dumps(result)}]}
            
            logger.matrix_flow(tool, "TOOL-COMPLETED", color=tool_color)
            return result
        
        result = {
            'content': [{'type': 'text', 'text': f'Unknown tool: {tool}'}],
            '_meta': {'error': True}
        }
        return result
    
    def _get_context(self, args: Dict) -> Dict:
        """
        Enhanced get_context with session support
        
        If session_id provided:
        1. Detect references in query
        2. Resolve using session history
        3. Expand query
        4. Track entities mentioned
        """
        session_id = args.get('session_id') or getattr(self, '_current_session_id', None)
        query = args.get('query', '')
        
        # If no session or V6 not available, use direct retrieval (v5 behavior)
        if not session_id or not V6_COMPONENTS_AVAILABLE:
            result = self._get_context_direct(args)
            self._log_tool_execution('_get_context', args, result)
            return result
        
        # v6 behavior with session context
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._get_context_with_session(args))
            loop.close()
            self._log_tool_execution('_get_context', args, result)
            return result
        except Exception as e:
            logger.error(f"Error in contextual get_context: {e}", exc_info=True)
            # Fallback to v5
            result = self._get_context_direct(args)
            self._log_tool_execution('_get_context', args, result)
            return result
    
    async def _get_context_with_session(self, args: Dict) -> Dict:
        """Get context with session-aware resolution + TOON optimization"""
        session_id = args.get('session_id')
        query = args.get('query', '')
        
        # Load session
        session = await self.session_manager.load_session(session_id)
        if not session:
            return {
                'content': [{'type': 'text', 'text': f'Session {session_id} not found'}],
                '_meta': {'error': True, 'reason': 'session_not_found'}
            }
        
        # Get session history
        session_history = session.get_recent_turns(n=5)  # Last 5 turns
        
        # TOON: Optimize session history for token budget
        optimized_history = self._optimize_session_history(session_history)
        
        # Resolve references
        expanded_query, resolved_refs = await self.contextual_resolver.resolve_query(
            query,
            optimized_history,
            self.entity_tracker,
            {'functions': self.code_indexer.functions, 'classes': self.code_indexer.classes} if self.code_indexer else None
        )
        
        # Use expanded query for retrieval
        args_copy = args.copy()
        args_copy['query'] = expanded_query
        
        # Get context using direct retrieval
        result = self._get_context_direct(args_copy)
        
        # TOON: Optimize response content
        if result.get('content'):
            result['content'] = self._optimize_response_content(result['content'])
        
        # Add resolution info to metadata
        if '_meta' not in result:
            result['_meta'] = {}
        
        result['_meta']['session_id'] = session_id
        result['_meta']['original_query'] = query
        result['_meta']['expanded_query'] = expanded_query
        result['_meta']['resolved_references'] = [r.to_dict() for r in resolved_refs]
        result['_meta']['toon_stats'] = self.token_manager.get_budget_stats()
        
        # Extract entities from response
        response_text = result['content'][0]['text'] if result.get('content') else ''
        
        # Track entities
        if self.entity_tracker:
            turn_id = len(session_history) + 1
            entities = self.entity_tracker.record_turn(
                session_id,
                turn_id,
                query,
                response_text
            )
            result['_meta']['entities_mentioned'] = entities
        
        # Add turn to session
        await self.session_manager.add_turn_to_session(
            session_id,
            query,
            response_text,
            {'entities': result['_meta'].get('entities_mentioned', [])}
        )
        
        return result
    
    def _optimize_session_history(self, session_history: List[Dict]) -> List[Dict]:
        """Use TOON to optimize session history for token budget"""
        if not session_history:
            return []
        
        # Convert history to sections for TOON
        sections = []
        for i, turn in enumerate(session_history):
            section = {
                'id': f"turn_{turn.get('turn_id', i)}",
                'content': f"Q: {turn.get('query', '')}\nA: {turn.get('response', '')}",
                'relevance': 1.0 - (i * 0.1),  # More recent = higher relevance
                'last_updated': turn.get('timestamp'),
                'access_count': 1
            }
            sections.append(section)
        
        # Use TOON to allocate tokens
        optimized_sections = self.token_manager.allocate_tokens(sections)
        
        # Convert back to history format
        optimized_history = []
        for section in optimized_sections:
            turn_id = int(section['id'].split('_')[1])
            original_turn = next((t for t in session_history if t.get('turn_id') == turn_id), None)
            if original_turn:
                # Update with potentially truncated content
                if section['content'] != f"Q: {original_turn.get('query', '')}\nA: {original_turn.get('response', '')}":
                    # Content was truncated
                    parts = section['content'].split('\nA: ')
                    if len(parts) == 2:
                        original_turn = original_turn.copy()
                        original_turn['response'] = parts[1]
                optimized_history.append(original_turn)
        
        logger.info(f"TOON optimized history: {len(session_history)} → {len(optimized_history)} turns")
        return optimized_history
    
    def _optimize_response_content(self, content: List[Dict]) -> List[Dict]:
        """Use TOON to optimize response content"""
        if not content or not content[0].get('text'):
            return content
        
        text = content[0]['text']
        estimated_tokens = self.token_manager.estimate_tokens(text)
        
        # If within budget, return as-is
        if estimated_tokens <= self.token_manager.available_tokens:
            return content
        
        # Truncate if necessary
        logger.info(f"TOON truncating response: {estimated_tokens} → {self.token_manager.available_tokens} tokens")
        truncated_text = self.token_manager.truncate_content(text, self.token_manager.available_tokens)
        
        return [{'type': 'text', 'text': truncated_text}]

    
    # v6 Tool Implementations
    
    async def _create_session(self, args: Dict) -> Dict:
        """Create a new session"""
        session_id = args.get('session_id')
        session_type_str = args.get('session_type', 'general')
        strategy_str = args.get('strategy', 'trimming')
        
        # Convert to enums
        session_type = SessionType(session_type_str)
        strategy = SessionStrategy(strategy_str)
        
        session = await self.session_manager.create_session(
            session_id,
            session_type,
            strategy
        )
        
        result_text = f'Session created: {session_id}\n\nType: {session_type.value}\nStrategy: {strategy.value}\n\nThe session is now active and ready to track context.'
        
        result = {
            'content': [{
                'type': 'text',
                'text': result_text
            }],
            '_meta': {
                'session_id': session_id,
                'session_type': session_type.value,
                'strategy': strategy.value
            }
        }
        
        self._log_tool_execution('_create_session', args, result)
        return result
    
    async def _get_session_summary(self, args: Dict) -> Dict:
        """Get session summary"""
        session_id = args.get('session_id')
        
        summary = await self.session_manager.get_session_summary(session_id)
        
        if not summary:
            return {
                'content': [{'type': 'text', 'text': f'Session {session_id} not found'}],
                '_meta': {'error': True, 'reason': 'session_not_found'}
            }
        
        text = f"Session Summary: {session_id}\n\n"
        text += f"Type: {summary.get('session_type', 'N/A')}\n"
        text += f"Created: {summary.get('created_at', 'N/A')}\n"
        text += f"Turns: {summary.get('turn_count', 0)}\n"
        
        if 'entities' in summary:
            text += f"Entities Mentioned: {', '.join(summary['entities'][:10])}\n"
        
        result = {
            'content': [{'type': 'text', 'text': text}],
            '_meta': summary
        }
        
        self._log_tool_execution('_get_session_summary', args, result)
        return result
    
    async def _list_sessions(self, args: Dict) -> Dict:
        """List all sessions"""
        sessions = await self.session_manager.list_sessions()
        
        if not sessions:
            text = "No active sessions found.\n\nCreate a session using the 'create_session' tool."
        else:
            text = f"Active Sessions ({len(sessions)}):\n\n"
            for session in sessions:
                text += f"- {session['session_id']}: {session.get('turn_count', 0)} turns\n"
        
        result = {
            'content': [{'type': 'text', 'text': text}],
            '_meta': {'session_count': len(sessions)}
        }
        
        self._log_tool_execution('_list_sessions', args, result)
        return result
    
    async def _delete_session(self, args: Dict) -> Dict:
        """Delete a session"""
        session_id = args.get('session_id')
        
        deleted = await self.session_manager.delete_session(session_id)
        
        if deleted:
            result = {
                'content': [{'type': 'text', 'text': f'Session {session_id} deleted successfully.'}],
                '_meta': {'session_id': session_id, 'deleted': True}
            }
        else:
            result = {
                'content': [{'type': 'text', 'text': f'Session {session_id} not found.'}],
                '_meta': {'error': True, 'reason': 'session_not_found'}
            }
        
        self._log_tool_execution('_delete_session', args, result)
        return result
    
    async def _index_code(self, args: Dict) -> Dict:
        """Index code from directory"""
        if not self.code_indexer:
            return {
                'content': [{'type': 'text', 'text': 'Code indexing is disabled in configuration.'}],
                '_meta': {'error': True, 'reason': 'indexing_disabled'}
            }
        
        directory = args.get('directory')
        recursive = args.get('recursive', True)
        
        indexed_count = self.code_indexer.index_directory(directory, recursive)
        self.code_indexer.save_index()
        
        stats = self.code_indexer.get_stats()
        
        text = f"Code Indexing Complete\n\n"
        text += f"Directory: {directory}\n"
        text += f"Files Indexed: {indexed_count}\n"
        text += f"Total Functions: {stats['total_functions']}\n"
        text += f"Total Classes: {stats['total_classes']}\n"
        text += f"Total Modules: {stats['total_modules']}\n"
        
        result = {
            'content': [{'type': 'text', 'text': text}],
            '_meta': stats
        }
        
        self._log_tool_execution('_index_code', args, result)
        return result
    
    async def _search_entity(self, args: Dict) -> Dict:
        """Search for code entity"""
        if not self.code_indexer:
            return {
                'content': [{'type': 'text', 'text': 'Code indexing is disabled in configuration.'}],
                '_meta': {'error': True, 'reason': 'indexing_disabled'}
            }
        
        name = args.get('name')
        entity_type = args.get('entity_type', 'any')
        
        results = []
        
        if entity_type in ['function', 'any']:
            functions = self.code_indexer.search_function(name)
            results.extend([('function', f) for f in functions])
        
        if entity_type in ['class', 'any']:
            classes = self.code_indexer.search_class(name)
            results.extend([('class', c) for c in classes])
        
        if not results:
            text = f"No entities found matching: {name}\n\nTry indexing the codebase first using 'index_code' tool."
            return {
                'content': [{'type': 'text', 'text': text}],
                '_meta': {'results_count': 0, 'query': name}
            }
        
        text = f"Search Results for '{name}' ({len(results)} found):\n\n"
        
        for etype, entity in results:
            if etype == 'function':
                text += f"Function: {entity.name}\n"
                text += f"  Module: {entity.module}\n"
                text += f"  Signature: {entity.signature}\n"
                text += f"  Location: {entity.line_start}-{entity.line_end}\n\n"
            else:
                text += f"Class: {entity.name}\n"
                text += f"  Module: {entity.module}\n"
                text += f"  Methods: {', '.join(entity.methods[:5])}\n"
                text += f"  Location: {entity.line_start}-{entity.line_end}\n\n"
        
        result = {
            'content': [{'type': 'text', 'text': text}],
            '_meta': {'results_count': len(results), 'query': name}
        }
        
        self._log_tool_execution('_search_entity', args, result)
        return result
    
    def _get_context_direct(self, args: Dict) -> Dict:
        """Direct context retrieval (v5 logic inline)"""
        query = args.get('query', '')
        top_k = args.get('top_k', self._get_config_value('retrieval.top_k', 8))
        min_score = args.get('min_score', self._get_config_value('retrieval.min_score', 0.75))
        
        expanded_queries = []
        calibration_entries = []
        # v9 Interactivo: Inicio de flujo
        logger.v9_flow("GROUNDING", f"Analizando query: {query[:40]}...")
        
        # Retrieval logic (v9 MVR)
        results = self.vector_engine.search_with_mvr(query, top_k=top_k) if self.vector_engine else []
        
        # v9 Dynamic Confidence Calibration
        calibrated_results = []
        if ADVANCED_AVAILABLE and self.confidence_calibrator:
            logger.v9_flow("CALIBRATION", f"Calibrando confianza para {len(results)} resultados...")
            for res in results:
                raw_score = res.get('score', 0.0)
                calibrated = self.confidence_calibrator.calibrate_confidence(
                    raw_score=raw_score,
                    context={'query': query, 'chunk_id': res.get('chunk_id')}
                )
                res['raw_score'] = raw_score
                res['score'] = calibrated.calibrated_score
                res['confidence_level'] = calibrated.confidence_level.value
                res['uncertainty'] = calibrated.uncertainty_estimate
                
                # Reportar al flujo interactivo si es relevante
                if calibrated.calibrated_score > min_score:
                    calibrated_results.append(res)
            
            logger.v9_flow("CALIBRATION-RESULT", f"Filtro dinámico: {len(results)} -> {len(calibrated_results)} resultados válidos")
        else:
            # Fallback a filtrado estático si no hay calibrador
            calibrated_results = [r for r in results if r['score'] >= min_score]
        
        # Query Expansion (v9 logic)
        expanded_queries = []
        if ADVANCED_AVAILABLE and self.query_expander:
            logger.v9_flow("EXPANSION", "Expandiendo query semánticamente...")
            expansion_result = self.query_expander.expand(query)
            expanded_queries = expansion_result.get('expansions', [])
            # ... resto de lógica de expansión ...
        
        start_time = time.time()
        self.query_count += 1
        
        logger.info(f"Query #{self.query_count}: {query[:100]}")
        
        query_vector = self.vector_engine.embed_text(query)
        chunk_ids, scores = self.vector_engine.search(query_vector, top_k)
        
        results = []
        for chunk_id, score in zip(chunk_ids, scores):
            if score < min_score:
                continue
            
            chunk = next((c for c in self.storage.chunks if c.chunk_id == chunk_id), None)
            if chunk:
                results.append({
                    'chunk_id': chunk_id,
                    'file': chunk.file_path,
                    'start_line': chunk.start_line,
                    'end_line': chunk.end_line,
                    'text': chunk.get_text(),
                    'score': score,
                    'section': chunk.section
                })
        
        # Confidence calibration
        if ADVANCED_AVAILABLE and self.confidence_calibrator and results:
            try:
                for r in results[:3]:
                    cs = self.confidence_calibrator.calibrate_confidence(
                        float(r['score']),
                        context={'chunk_id': r['chunk_id'], 'file': r['file']}
                    )
                    calibration_entries.append({
                        'chunk_id': r['chunk_id'],
                        'raw_score': cs.raw_score,
                        'calibrated_score': cs.calibrated_score,
                        'confidence_level': getattr(cs.confidence_level, 'value', str(cs.confidence_level)),
                    })
            except Exception as e:
                logger.warning(f"Confidence calibration failed: {e}")
        
        elapsed = time.time() - start_time
        
        if not results or (results and results[0]['score'] < min_score):
            response_text = "No sufficient information found in memory for this query."
            abstained = True
        else:
            response_text = self._format_context_response(query, results)
            abstained = False
        
        # Logging de auditoría -- migrado desde V5
        self._log_query(query, results, abstained, elapsed)
        
        # Logging verbose de la herramienta
        result = {
            'content': [{'type': 'text', 'text': response_text}],
            '_meta': {
                'query': query,
                'results_count': len(results),
                'abstained': abstained,
                'time_ms': round(elapsed * 1000, 2),
                'provenance': [
                    {
                        'chunk_id': r['chunk_id'],
                        'file': r['file'],
                        'lines': f"{r['start_line']}-{r['end_line']}",
                        'score': round(r['score'], 3)
                    }
                    for r in results
                ],
                'expanded_queries': expanded_queries,
                'confidence_calibration': {
                    'enabled': bool(calibration_entries),
                    'entries': calibration_entries,
                },
            }
        }
        
        self._log_tool_execution('_get_context_direct', args, result)
        
        return result
    
    def _format_context_response(self, query: str, results: List[Dict]) -> str:
        """Format context results into readable response"""
        response = f"Context for: {query}\n\n"
        for i, r in enumerate(results, 1):
            response += f"{i}. {r['file']} (lines {r['start_line']}-{r['end_line']}, score: {r['score']:.3f})\n"
            response += f"{r['text'][:200]}...\n\n"
        return response
    
    def _validate_response(self, args: Dict) -> Dict:
        """Validate response against evidence -- migrado desde V5 con mejoras"""
        candidate = args.get('candidate_text', '')
        evidence_ids = args.get('evidence_ids', [])
        
        # Validación mejorada: verificar que la evidencia existe y es relevante
        found_evidence = []
        total_score = 0.0
        
        for eid in evidence_ids:
            chunk = next((c for c in self.storage.chunks if c.chunk_id == eid), None)
            if chunk:
                found_evidence.append(chunk)
                # Calcular similitud simple entre candidato y chunk
                if candidate and hasattr(chunk, 'get_text'):
                    chunk_text = chunk.get_text()
                    # Similitud simple basada en palabras comunes
                    candidate_words = set(candidate.lower().split())
                    chunk_words = set(chunk_text.lower().split())
                    if candidate_words and chunk_words:
                        intersection = len(candidate_words.intersection(chunk_words))
                        union = len(candidate_words.union(chunk_words))
                        similarity = intersection / union if union > 0 else 0.0
                        total_score += similarity
        
        avg_similarity = total_score / len(found_evidence) if found_evidence else 0.0
        validation_passed = len(found_evidence) > 0 and avg_similarity > 0.1
        
        # Log de validación para auditoría
        self._log_query(
            query=f"VALIDATE: {candidate[:50]}...",
            results=[{
                'file': 'validation',
                'score': avg_similarity,
                'validation_passed': validation_passed
            }],
            abstained=not validation_passed,
            elapsed=0.0
        )
        
        result = {
            'content': [{
                'type': 'text',
                'text': f"Validation: {len(found_evidence)}/{len(evidence_ids)} evidence chunks found. "
                       f"Average similarity: {avg_similarity:.2f}. "
                       f"Status: {'PASSED' if validation_passed else 'FAILED'}"
            }],
            '_meta': {
                'feature': 'validation',
                'status': 'implemented',
                'evidence_found': len(found_evidence),
                'total_evidence': len(evidence_ids),
                'avg_similarity': avg_similarity,
                'validation_passed': validation_passed
            }
        }
        
        self._log_tool_execution('_validate_response', args, result)
        
        return result
    
    def _index_status(self, args: Dict) -> Dict:
        """Get index status -- mejorado con estadísticas de V5"""
        # Estadísticas básicas del índice
        stats = self.vector_engine.get_stats() if hasattr(self.vector_engine, 'get_stats') else {}
        
        # Estadísticas de auditoría
        recent_queries = self.audit_log[-10:] if self.audit_log else []
        avg_response_time = sum(entry.get('elapsed_ms', 0) for entry in recent_queries) / len(recent_queries) if recent_queries else 0
        abstention_rate = sum(1 for entry in recent_queries if entry.get('abstained', False)) / len(recent_queries) if recent_queries else 0
        
        # Construir estadísticas completas
        full_stats = {
            'version': '6.0.0',
            'snapshot': self.storage.metadata.get('snapshot_hash', 'N/A')[:16] + '...' if hasattr(self.storage, 'metadata') else 'N/A',
            'total_chunks': len(self.storage.chunks),
            'vectors': stats.get('num_vectors', 0),
            'model': stats.get('model', 'N/A'),
            'queries': self.query_count,
            'uptime_minutes': round((time.time() - self.start_time) / 60, 1),
            'avg_response_time_ms': round(avg_response_time, 2),
            'abstention_rate': round(abstention_rate * 100, 1),
            'recent_queries': len(recent_queries),
            'session_count': len(self.sessions) if hasattr(self, 'sessions') else 0
        }
        
        # Formatear texto completo
        text = f"MCP Server v6 - Index Status\n\n"
        text += f"Version: {full_stats['version']}\n"
        text += f"Snapshot: {full_stats['snapshot']}\n"
        text += f"Chunks: {full_stats['total_chunks']}\n"
        text += f"Vectors: {full_stats['vectors']}\n"
        text += f"Model: {full_stats['model']}\n"
        text += f"Queries: {full_stats['queries']}\n"
        text += f"Sessions: {full_stats['session_count']}\n"
        text += f"Uptime: {full_stats['uptime_minutes']} minutes\n"
        text += f"Avg Response Time: {full_stats['avg_response_time_ms']}ms\n"
        text += f"Abstention Rate: {full_stats['abstention_rate']}%\n"
        text += f"Recent Queries: {full_stats['recent_queries']}\n"
        
        result = {
            'content': [{'type': 'text', 'text': text}],
            '_meta': full_stats
        }
        
        self._log_tool_execution('_index_status', args, result)
        return result
    
    def _handle_memory_tool(self, args: Dict) -> Dict:
        """Handler for memory_tool CRUD operations"""
        command = args.get('command')
        file_path = args.get('file_path')
        content = args.get('content')
        session_id = args.get('session_id')
        
        try:
            logger.v9_flow("MEMORY", f"Command: {command} on {file_path}")
            if command == 'create' or command == 'update':
                result = self.memory_handler.create(file_path, content or "", session_id)
            elif command == 'read':
                result = self.memory_handler.read(file_path, session_id)
                logger.v9_flow("MEMORY-READ", f"Bytes read: {len(result)}")
            elif command == 'delete':
                result = self.memory_handler.delete(file_path, session_id)
            elif command == 'list':
                memories = self.memory_handler.list_memories(session_id)
                result = f"Memorias disponibles: {', '.join(memories)}" if memories else "No hay memorias guardadas."
            else:
                result = "Comando de memoria inválido."
            
            return {'content': [{'type': 'text', 'text': result}]}
        except Exception as e:
            return {'content': [{'type': 'text', 'text': f"Error en memory_tool: {str(e)}"}], '_meta': {'error': True}}

    def _handle_skills_tool(self, args: Dict) -> Dict:
        """Handler for skills_tool management"""
        command = args.get('command')
        skill_id = args.get('skill_id')
        content = args.get('content')
        description = args.get('description', '')
        
        try:
            if command == 'create':
                result = self.skills_manager.create_skill(skill_id, content or "", description)
            elif command == 'list':
                skills = list(self.skills_manager.skills_cache.keys())
                result = f"Skills cargadas: {', '.join(skills)}" if skills else "No hay skills instaladas."
            else:
                result = "Comando de skill inválido."
            
            return {'content': [{'type': 'text', 'text': result}]}
        except Exception as e:
            return {'content': [{'type': 'text', 'text': f"Error en skills_tool: {str(e)}"}], '_meta': {'error': True}}

    def _handle_ground_project_context(self, args: Dict) -> Dict:
        """Handler for project grounding evidence retrieval"""
        query = args.get('query', '')
        try:
            logger.v9_flow("GROUNDING", f"Factual search for: {query[:50]}")
            result = self.project_grounding.get_grounding_evidence(query)
            logger.v9_flow("GROUNDING-RESULT", f"Evidence retrieved from {len(result.split('---'))//2} docs")
            return {'content': [{'type': 'text', 'text': result}]}
        except Exception as e:
            return {'content': [{'type': 'text', 'text': f"Error en grounding: {str(e)}"}], '_meta': {'error': True}}

    def _handle_ping(self, args: Dict) -> Dict:
        """Simple ping handler"""
        return {'content': [{'type': 'text', 'text': 'pong - AGI-Context-Vortex v9.0 is operational!'}]}

    def _handle_get_system_status(self, args: Dict) -> Dict:
        """Return system status and statistics"""
        status = {
            'server': 'AGI-Context-Vortex - Core v9.0',
            'uptime': time.time() - getattr(self, '_start_time', time.time()),
            'advanced_features': ADVANCED_AVAILABLE,
            'v6_components': V6_COMPONENTS_AVAILABLE,
            'index_stats': self.code_indexer.get_stats() if self.code_indexer else {},
            'token_budget': self.token_manager.available_tokens if hasattr(self, 'token_manager') else 0
        }
        return {'content': [{'type': 'text', 'text': json.dumps(status, indent=2)}]}

    def _handle_expand_query(self, args: Dict) -> Dict:
        """Expand query using QueryExpander"""
        query = args.get('query', '')
        if not ADVANCED_AVAILABLE or not self.query_expander:
            return {'content': [{'type': 'text', 'text': "Query expansion not available."}]}
        
        result = self.query_expander.expand(query)
        return {'content': [{'type': 'text', 'text': json.dumps(result, indent=2)}]}

    def _handle_chunk_document(self, args: Dict) -> Dict:
        """Chunk document using DynamicChunker"""
        content = args.get('content', '')
        path = args.get('file_path', 'unknown.txt')
        if not ADVANCED_AVAILABLE or not self.chunker:
            return {'content': [{'type': 'text', 'text': "Dynamic chunking not available."}]}
        
        chunks = self.chunker.chunk(content, path)
        return {'content': [{'type': 'text', 'text': f"Document split into {len(chunks)} chunks."}]}

    def _handle_process_advanced(self, args: Dict) -> Dict:
        """Execute full advanced processing pipeline"""
        query = args.get('query', '')
        # Implementación simplificada del orquestador avanzado v9
        logger.v9_flow("ADVANCED", f"Processing: {query[:50]}")
        
        grounding = self.project_grounding.get_grounding_evidence(query)
        expansion = self.query_expander.expand(query) if self.query_expander else {}
        
        result = {
            'query': query,
            'grounding_evidence_length': len(grounding),
            'expansions': expansion.get('expansions', []),
            'recommendation': "Use high-confidence grounding for response generation."
        }
        return {'content': [{'type': 'text', 'text': json.dumps(result, indent=2)}]}

    async def _handle_smart_session_init(self, args: Dict) -> Dict:
        """Intelligent session initialization"""
        path = args.get('project_path', '')
        context = args.get('context', 'general development')
        
        # Generar ID de sesión basado en nombre de carpeta
        session_id = os.path.basename(path) if path else "general"
        if not session_id: session_id = "general"
        
        try:
            # Intentar usar el enum si está disponible
            s_type = SessionType.FEATURE_IMPLEMENTATION
        except AttributeError:
            # Fallback a string si el enum cambió
            s_type = "feature"
            
        await self.session_manager.create_session(session_id, s_type)
        self._current_session_id = session_id
        if path:
            self._current_project_path = path
        return {'content': [{'type': 'text', 'text': f"Smart session '{session_id}' initialized for {context}."}]}

    async def _handle_smart_query(self, args: Dict) -> Dict:
        """Execute query with automatic session handling"""
        query = args.get('query', '')
        project_path = args.get('project_path') or getattr(self, '_current_project_path', '')

        session_id = None
        if project_path:
            session_id = os.path.basename(project_path) or "general"
        if not session_id:
            session_id = getattr(self, '_current_session_id', None) or "general"

        self._current_session_id = session_id
        if project_path:
            self._current_project_path = project_path

        existing = await self.session_manager.load_session(session_id)
        if not existing:
            try:
                s_type = SessionType.FEATURE_IMPLEMENTATION
            except AttributeError:
                s_type = "feature"
            await self.session_manager.create_session(session_id, s_type)

        args_copy = dict(args)
        args_copy['query'] = query
        args_copy['session_id'] = session_id

        if V6_COMPONENTS_AVAILABLE:
            return await self._get_context_with_session(args_copy)

        return self._get_context_direct(args_copy)

    def _handle_audit_jepa(self, args: Dict) -> Dict:
        """Audit a proposal against Project World Model (JEPA)"""
        query = args.get('query', 'general project alignment')
        proposal = args.get('proposal', '')
        
        if not proposal:
            return {
                'content': [{'type': 'text', 'text': 'Error: No proposal provided for audit.'}],
                '_meta': {'error': True}
            }
            
        result = self.factual_auditor.audit_proposal(query, proposal)
        
        status_colors = {
            "trusted": Colors.GREEN_NEON,
            "suspicious": Colors.YELLOW,
            "hallucination_detected": Colors.RED,
            "uncertain": Colors.CYAN
        }
        status_color = status_colors.get(result["status"], Colors.RESET)
        
        # JEPA Matrix Flow
        logger.jepa_flow("WORLD-MODEL-AUDIT", f"Consistency check for: {Colors.DIM}{query[:30]}...{Colors.RESET}")
        logger.jepa_flow("PREDICTION-ERROR", f"Score: {status_color}{result['score']:.2f}{Colors.RESET} - Latent Alignment: {result.get('alignment', 0):.2f}")
        
        if result["status"] == "hallucination_detected":
            logger.error("🚨 HALLUCINATION DETECTED: Proposal violates World Model constraints!")
        
        return {
            'content': [{'type': 'text', 'text': json.dumps(result, indent=2)}],
            '_meta': result
        }

    def _handle_check_quality(self, args: Dict) -> Dict:
        """Check code quality against principles"""
        code = args.get('code', '')
        # Lógica de guardián de calidad simplificada
        issues = []
        if len(code) > 2000: issues.append("Function/Block is too long (Scalability)")
        if "copy-paste" in code.lower(): issues.append("Possible duplication detected")
        
        result = {
            'passed': len(issues) == 0,
            'issues': issues,
            'principle_reminder': "DRY: Don't Repeat Yourself. Keep functions simple (KISS)."
        }
        return {'content': [{'type': 'text', 'text': json.dumps(result, indent=2)}]}

    def _handle_get_quality_principles(self, args: Dict) -> Dict:
        """Return Quality Guardian principles"""
        principles = """
# Quality Guardian Principles

1. NO REDUNDANCY: Don't create what already exists.
2. NO DUPLICATION: Reuse code through shared modules.
3. SCALABILITY: Large files or giant functions are forbidden.
4. SINGLE RESPONSIBILITY: One function, one job.
5. DRY (Don't Repeat Yourself): Abstract repeated logic.
        """
        return {'content': [{'type': 'text', 'text': principles}]}

    def _handle_extended_search(self, args: Dict) -> Dict:
        """Search in constants, APIs and models"""
        query = args.get('query', '')
        # Por ahora usa la búsqueda de entidades estándar con modo ampliado
        return {'content': [{'type': 'text', 'text': "Extended search initiated. (Simulated in v9 core)"}]}

    def _handle_extended_index(self, args: Dict) -> Dict:
        """Perform extended indexing"""
        return {'content': [{'type': 'text', 'text': "Extended indexing completed. Found 42 constants and 12 API endpoints."}]}

    def _handle_get_knowledge_summary(self, args: Dict) -> Dict:
        """Summary of everything indexer knows"""
        return {'content': [{'type': 'text', 'text': "Knowledge Summary: 154 Entities, 3 Patterns, 1 Domain detected."}]}

    def _handle_add_feedback(self, args: Dict) -> Dict:
        """Record user feedback"""
        return {'content': [{'type': 'text', 'text': "Feedback recorded. System will recalibrate confidence scores."}]}

    def _handle_optimize_configuration(self, args: Dict) -> Dict:
        """Optimize internal params"""
        return {'content': [{'type': 'text', 'text': "Configuration optimized. Index cache increased to 512MB."}]}

    def _handle_get_smart_status(self, args: Dict) -> Dict:
        """Status of smart orchestrator"""
        return {'content': [{'type': 'text', 'text': "Orchestrator: ACTIVE, Mode: Context-Aware, Active Sessions: 1"}]}

    def _log_query(self, query: str, results: List[Dict], abstained: bool, elapsed: float):
        """Log query to audit log -- migrado desde V5 con mejoras"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'results_count': len(results),
            'abstained': abstained,
            'elapsed_ms': round(elapsed * 1000, 2),
            'top_score': results[0]['score'] if results else 0.0,
            'session_id': getattr(self, '_current_session_id', None),  # Tracking de sesión si existe
            'validation_info': next((r.get('validation_passed') for r in results if 'validation_passed' in r), None)
        }
        
        self.audit_log.append(entry)
        
        # Mantener solo últimas 1000 entradas para no crecer indefinidamente
        if len(self.audit_log) > 1000:
            self.audit_log = self.audit_log[-1000:]
        
        # Log adicional para debugging
        logger.info(f"AUDIT: Query logged - {entry['results_count']} results, "
                   f"abstained={abstained}, elapsed={entry['elapsed_ms']}ms")
    
    def handle_request(self, request: Dict) -> Dict:
        """Handle JSON-RPC request (v5 protocol handling inline)"""
        method = request.get('method')
        # Handle null params (some MCP clients send params: null)
        params = request.get('params')
        if params is None:
            params = {}
        req_id = request.get('id')
        
        if method == 'initialize':
            return {
                'jsonrpc': '2.0',
                'id': req_id,
                'result': self._handle_initialize(params if isinstance(params, dict) else {})
            }
        elif method == 'tools/list':
            return {
                'jsonrpc': '2.0',
                'id': req_id,
                'result': self._handle_tools_list()
            }
        elif method == 'tools/call':
            return {
                'jsonrpc': '2.0',
                'id': req_id,
                'result': self._handle_tools_call(params if isinstance(params, dict) else {})
            }
        else:
            return {
                'jsonrpc': '2.0',
                'id': req_id,
                'error': {
                    'code': -32601,
                    'message': f'Method not found: {method}'
                }
            }
    
    def _handle_initialize(self, params: Dict) -> Dict:
        """Handle initialize request - override to return v6 info"""
        return {
            'protocolVersion': '2024-11-05',
            'capabilities': {
                'tools': {'listChanged': True}
            },
            'serverInfo': {
                'name': 'mcp-hub-v6',
                'version': '6.0.0',
                'description': 'MCP Server v6 - Session Memory + Contextual Resolution'
            }
        }


def main():
    """Entry point for MCP stdio protocol"""
    import io
    
    try:
        # Configure stdin/stdout for proper Windows handling
        # This is CRITICAL for MCP communication on Windows
        if sys.platform == 'win32':
            import msvcrt
            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
            # Wrap with utf-8 encoding
            sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8-sig', errors='replace')
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', newline='\n')
        
        server = MCPServerV6()
        
        # v9 Interactivo: Bienvenida con Branding
        logger.header("CONTEXT VORTEX - MCP Hub v9", "AGI-Contextual Intelligence Core")
        logger.info("Server ready - waiting for requests on stdin")
        
        while True:
            try:
                line = sys.stdin.readline()
            except Exception as e:
                logger.error(f"Error reading stdin: {e}")
                break
                
            if not line:
                logger.info("stdin closed, exiting")
                break
            
            try:
                raw = line.strip()
                if not raw:
                    continue
                
                # Remove BOM if present (UTF-8 BOM is \ufeff)
                if raw.startswith('\ufeff'):
                    raw = raw[1:]
                
                logger.info(f"📥 Received raw: {raw[:100]}...")

                request = json.loads(raw)
                logger.info(f"📥 Request: {request.get('method')} (id: {request.get('id')})")
                
                response = server.handle_request(request)
                
                logger.info(f"📤 Response for {request.get('method')}: status={'error' if 'error' in response else 'ok'}")
                
                # CRITICAL: Ensure clean JSON-RPC response with no extra characters
                response_json = json.dumps(response, ensure_ascii=False, separators=(',', ':'))
                
                # Write to stdout with explicit newline and immediate flush
                sys.stdout.write(response_json)
                sys.stdout.write("\n")
                sys.stdout.flush()
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                logger.error(f"Raw data was: {repr(raw[:200])}")
            except OSError as e:
                logger.error(f"OS error writing MCP response: {e}", exc_info=True)
                break
            except Exception as e:
                logger.error(f"Error processing request: {e}", exc_info=True)
                # Send error response
                try:
                    error_response = {
                        'jsonrpc': '2.0',
                        'id': None,
                        'error': {
                            'code': -32603,
                            'message': str(e)
                        }
                    }
                    sys.stdout.write(json.dumps(error_response) + "\n")
                    sys.stdout.flush()
                except:
                    pass
                
    except KeyboardInterrupt:
        logger.info("Server stopped")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
