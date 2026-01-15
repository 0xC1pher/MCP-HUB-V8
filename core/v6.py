"""
MCP Server v6 - Session Memory + Contextual Resolution
Extends v5 with session management and code intelligence
"""

import json
import sys
import logging
import time
import asyncio
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Setup logging - CRITICAL: Must write to stderr/file ONLY, never stdout
# Stdout is reserved for JSON-RPC protocol communication
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "mcp_v6.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stderr)  # Explicitly use stderr, NOT stdout
    ]
)
logger = logging.getLogger(__name__)

# Path setup
current_dir = Path(__file__).resolve().parent
mcp_hub_root = current_dir.parent
sys.path.insert(0, str(mcp_hub_root))
sys.path.insert(0, str(current_dir))

# Import v5 components (but not MCPServerV5 class itself)
from storage.mp4_storage import MP4Storage
from storage.vector_engine import VectorEngine

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
    V6_COMPONENTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"V6 components not available: {e}")
    V6_COMPONENTS_AVAILABLE = False
    # Create dummy classes to avoid errors
    class SessionManager: pass
    class SessionStorage: pass
    class CodeIndexer: pass
    class EntityTracker: pass
    class ContextualResolver: pass
    class TokenBudgetManager: pass


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
        
        logger.info("="*80)
        logger.info("MCP Server v6 - Session Memory + Contextual Resolution")
        logger.info("="*80)
        
        # Cargar configuración (AdvancedConfig o JSON)
        self.config = self._load_config(config_path)
        
        # Métodos auxiliares para acceso seguro a configuración
        self._config_cache = {}
    
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
    
    def _log_tool_execution(self, tool_name: str, args: Dict[str, Any], result: Any = None):
        """Log verbose information about tool execution"""
        if self.verbose:
            logger.info(f"🔧 TOOL EXECUTED: {tool_name}")
            logger.info(f"   Args: {json.dumps(args, default=str)[:200]}...")
            if result:
                result_str = str(result)[:200]
                logger.info(f"   Result: {result_str}...")
            logger.info("-" * 60)
            logger.info("-" * 60)
        
        # Initialize v5 components with SEPARATE storage file for v6
        v6_mp4_path = str(mcp_hub_root / "data" / "context_vectors_v6.mp4")
        self.storage = MP4Storage(v6_mp4_path)
        self.vector_engine = VectorEngine(self.config)
        
        # Advanced features (copy from v5 logic)
        if ADVANCED_AVAILABLE:
            # Configuración de chunking - compatible con AdvancedConfig y JSON
            min_tokens = self._get_config_value('chunking.min_tokens', 150)
            max_tokens = self._get_config_value('chunking.max_tokens', 450)
            overlap_percent = self._get_config_value('chunking.overlap_percent', 25)
            
            self.chunker = DynamicChunker(
                min_chunk_size=min_tokens,
                max_chunk_size=max_tokens,
                overlap_ratio=overlap_percent / 100.0,
            )
            self.query_expander = QueryExpander()
            
            # Configuración de confianza - compatible con ambos formatos
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
        
        # Load v6-specific configuration
        logger.info("Loading v6-specific configuration...")
        v6_config_path = mcp_hub_root / "config" / "v6_config.json"
        if v6_config_path.exists():
            with open(v6_config_path, 'r') as f:
                v6_config = json.load(f)
                self.config.update(v6_config)
            logger.info(f"v6 configuration loaded from {v6_config_path}")
        
        # Initialize v6-specific components
        if V6_COMPONENTS_AVAILABLE:
            logger.info("Initializing v6-specific components...")
            self._initialize_v6_components()
            logger.info("v6 components initialized successfully")
        else:
            logger.warning("V6 components not available - running in compatibility mode")
        
        logger.info("="*80)
        logger.info("MCP Server v6 ready")
        logger.info("="*80)
    
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
        if not V6_COMPONENTS_AVAILABLE:
            return
            
        # Session management
        session_storage = SessionStorage(
            storage_dir=str(mcp_hub_root / "data" / "sessions"),
            retention_days=self.config.get('session', {}).get('retention_days', 30)
        )
        
        default_strategy = SessionStrategy.TRIMMING
        if self.config.get('session', {}).get('default_type') == 'summarizing':
            default_strategy = SessionStrategy.SUMMARIZING
        
        self.session_manager = SessionManager(
            storage=session_storage,
            default_strategy=default_strategy,
            auto_save=self.config.get('session', {}).get('auto_save', True)
        )
        logger.info("Session manager initialized")
        
        # Code indexing
        if self.config.get('code_indexing', {}).get('enabled', True):
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
        if self.config.get('entity_tracking', {}).get('enabled', True):
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
        toon_config = self.config.get('toon', {})
        self.token_manager = TokenBudgetManager(
            max_tokens=toon_config.get('max_tokens', 4000),
            reserved_tokens=toon_config.get('reserved_tokens', 500)
        )
        logger.info(f"TOON initialized: {self.token_manager.available_tokens} tokens available")

    
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
                }
            ]
            
            v5_tools['tools'].extend(v6_tools)
        
        return v5_tools
    
    def _handle_tools_call(self, params: Dict) -> Dict:
        """Execute tool (v5 + v6)"""
        tool = params.get('name')
        args = params.get('arguments', {})
        
        # v6 tools
        if V6_COMPONENTS_AVAILABLE:
            v6_tools = {
                'create_session': self._create_session,
                'get_session_summary': self._get_session_summary,
                'list_sessions': self._list_sessions,
                'delete_session': self._delete_session,
                'index_code': self._index_code,
                'search_entity': self._search_entity
            }
            
            if tool in v6_tools:
                try:
                    # Run async tools
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(v6_tools[tool](args))
                    loop.close()
                    # Ensure result has proper MCP format
                    if not isinstance(result, dict):
                        result = {'content': [{'type': 'text', 'text': str(result)}]}
                    if 'content' not in result:
                        result = {'content': [{'type': 'text', 'text': json.dumps(result)}]}
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
            return result
        
        result = {
            'content': [{'type': 'text', 'text': f'Unknown tool: {tool}'}],
            '_meta': {'error': True}
        }
    
    def _get_context(self, args: Dict) -> Dict:
        """
        Enhanced get_context with session support
        
        If session_id provided:
        1. Detect references in query
        2. Resolve using session history
        3. Expand query
        4. Track entities mentioned
        """
        session_id = args.get('session_id')
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
        
        start_time = time.time()
        self.query_count += 1
        
        logger.info(f"Query #{self.query_count}: {query[:100]}")
        
        # Query expansion
        if ADVANCED_AVAILABLE and self.query_expander and query:
            try:
                expansion = self.query_expander.expand_query(query, max_expansions=5)
                if hasattr(expansion, 'expanded_queries') and expansion.expanded_queries:
                    expanded_queries = list(expansion.expanded_queries)
            except Exception as e:
                logger.warning(f"Query expansion failed: {e}")
        
        # Vector search
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
