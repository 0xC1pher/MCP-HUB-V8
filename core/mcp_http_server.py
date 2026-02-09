"""
MCP Server v10 Context Vortex - HTTP/SSE Transport
Integra TODAS las funcionalidades + Code Guardian Anti-Duplicación

TOOLS INCLUIDAS (20 total):
===========================
V5 Base (4):
- ping: Test de conectividad
- get_context: Recuperar contexto con provenance
- validate_response: Validar respuestas contra evidencia  
- index_status: Estado del índice vectorial

V7 Session Management (4):
- create_session: Crear sesión de desarrollo
- get_session_summary: Resumen de sesión
- list_sessions: Listar sesiones activas
- delete_session: Eliminar sesión

V7 Code Intelligence (2):
- index_code: Indexar directorio de código
- search_entity: Buscar funciones/clases

Advanced Features (6):
- process_advanced: Procesamiento con todas las features (MVR, chunking, expansion, calibration)
- expand_query: Expansión automática de queries (semántica, estadística, contextual)
- chunk_document: Chunking dinámico adaptativo
- get_system_status: Estado del sistema completo
- add_feedback: Agregar feedback para recalibración dinámica
- optimize_configuration: Optimizar configuración basada en uso

CODE GUARDIAN (4):
- check_code_creation: 🛡️ PREVIENE duplicación ANTES de crear código
- analyze_project_redundancy: 📊 ANALIZA redundancia en TODO el proyecto
- get_code_suggestions: 💡 SUGIERE código reutilizable existente
- learn_from_context: 🧠 APRENDE de archivos de contexto
"""
import sys
import os
import re
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any, Set

# Setup paths
current_dir = Path(__file__).resolve().parent
mcp_hub_root = current_dir.parent
sys.path.insert(0, str(mcp_hub_root))
sys.path.insert(0, str(current_dir))

from mcp.server.fastmcp import FastMCP

# Import Pretty Logger for beautiful logging
try:
    from pretty_logger import get_logger, Colors
    _tool_logger = get_logger("MCP-Tools")
    _color_logger = get_logger("MCP-Colors")
except ImportError:
    _tool_logger = None
    _color_logger = None
    Colors = None

# Import Visual Activity Monitor for real-time interface
try:
    from visual_monitor import get_visual_monitor, VisualActivityMonitor
    _visual_monitor = get_visual_monitor()
    if _visual_monitor:
        _visual_monitor.start_monitoring()
except ImportError:
    _visual_monitor = None

# Create server
mcp = FastMCP("AGI-Context-Vortex-v10-Code-Guardian")

# ============================================
# Singleton instances
# ============================================
_v6_server = None
_orchestrator = None
_code_guardian_tools = None

BASE_DIR = Path(
    os.environ.get("MCP_BASE_DIR", mcp_hub_root.parent)
).resolve()
EXCLUDED_DIRS: Set[str] = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}


def _should_skip_dir(dir_name: str) -> bool:
    return dir_name in EXCLUDED_DIRS


def _safe_read_text(file_path: Path) -> Optional[str]:
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None
    except Exception:
        return None


def _resolve_base_dir(override: Optional[str]) -> Optional[Path]:
    if override:
        candidate = Path(override)
        if not candidate.is_absolute():
            candidate = BASE_DIR / candidate
        candidate = candidate.resolve()
    else:
        candidate = BASE_DIR
    return candidate if candidate.exists() else None


def _resolve_css_path(base_dir: Path, override: Optional[str]) -> Optional[Path]:
    if override:
        candidate = Path(override)
        if not candidate.is_absolute():
            candidate = base_dir / candidate
        if candidate.exists():
            return candidate

    env_path = os.environ.get("MCP_CSS_PATH")
    if env_path:
        env_candidate = Path(env_path)
        if not env_candidate.is_absolute():
            env_candidate = base_dir / env_candidate
        if env_candidate.exists():
            return env_candidate

    default_path = base_dir / "static" / "css" / "app.css"
    if default_path.exists():
        return default_path

    css_dir = base_dir / "static" / "css"
    if css_dir.exists():
        candidates = sorted(css_dir.glob("*.css"))
        if candidates:
            return candidates[0]

    return None

def get_v6_server():
    """Get or create singleton instance of MCPServerV6"""
    global _v6_server
    if _v6_server is None:
        try:
            # Importar de forma segura para evitar problemas circulares
            # Precargar módulos de storage para evitar importación circular
            try:
                from storage import vector_engine
                print("Storage modules pre-loaded successfully", file=sys.stderr)
            except ImportError as e:
                print(f"Warning: Storage modules loading issue: {e}", file=sys.stderr)
            
            # Usar importlib para importar dinámicamente y evitar problemas de inicialización
            import importlib.util
            import sys
            
            # Verificar si el módulo ya está en sys.modules
            if 'v6' in sys.modules:
                v6_module = sys.modules['v6']
            else:
                # Cargar el módulo dinámicamente
                spec = importlib.util.spec_from_file_location(
                    "v6", 
                    os.path.join(os.path.dirname(__file__), "v6.py")
                )
                if spec and spec.loader:
                    v6_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(v6_module)
                    sys.modules['v6'] = v6_module
                else:
                    raise ImportError("No se pudo cargar el módulo v6")
            
            MCPServerV6 = getattr(v6_module, 'MCPServerV6')
            _v6_server = MCPServerV6()
        except Exception as e:
            print(f"Warning: Could not import MCPServerV6: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            _v6_server = None
    return _v6_server

def get_orchestrator():
    """Get or create singleton instance of Advanced Features Orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        try:
            from advanced_features import create_orchestrator
            _orchestrator = create_orchestrator("balanced")
        except Exception as e:
            print(f"Warning: Could not create orchestrator: {e}", file=sys.stderr)
            _orchestrator = None
    return _orchestrator

def get_code_guardian_tools():
    """Get or create singleton instance of Code Guardian tools"""
    global _code_guardian_tools
    if _code_guardian_tools is None:
        try:
            from advanced_features.code_guardian_mcp import create_code_guardian_mcp_tools
            _code_guardian_tools = create_code_guardian_mcp_tools()
            print(f"✅ Code Guardian tools initialized: {len(_code_guardian_tools)} tools")
        except Exception as e:
            print(f"Warning: Could not create Code Guardian tools: {e}", file=sys.stderr)
            _code_guardian_tools = None
    return _code_guardian_tools


def visual_tool_decorator(tool_func):
    """Decorador para agregar visualización dinámica a las herramientas"""
    import time
    import functools
    
    @functools.wraps(tool_func)
    async def wrapper(*args, **kwargs):
        tool_name = tool_func.__name__
        start_time = time.time()
        
        # Visual feedback al inicio
        if _visual_monitor:
            # Limpiar argumentos para visualización (evitar información sensible)
            safe_args = {k: str(v)[:50] + "..." if len(str(v)) > 50 else str(v) 
                         for k, v in kwargs.items() if v is not None}
            _visual_monitor.tool_started(tool_name, safe_args)
        
        try:
            # Ejecutar la herramienta
            result = await tool_func(*args, **kwargs)
            
            duration = time.time() - start_time
            
            # Visual feedback al completar
            if _visual_monitor:
                result_summary = "Success"
                if isinstance(result, str):
                    if len(result) > 100:
                        result_summary = f"Result: {len(result)} chars"
                    else:
                        result_summary = result[:50] + "..." if len(result) > 50 else result
                
                _visual_monitor.tool_completed(tool_name, result_summary, duration)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Visual feedback de error
            if _visual_monitor:
                _visual_monitor.tool_failed(tool_name, str(e))
            
            # Re-lanzar la excepción para que se maneje normalmente
            raise
    
    return wrapper


# ============================================
# V5 Tools (Core Retrieval)
# ============================================

@mcp.tool()
@visual_tool_decorator
async def ping() -> str:
    """Simple ping test to verify MCP connectivity."""
    return "pong - MCP v7 HTTP server is working!"


@mcp.tool()
@visual_tool_decorator
async def get_context(query: str, top_k: int = 5, min_score: float = 0.5, session_id: Optional[str] = None) -> str:
    """
    Retrieve context from memory with provenance.
    
    Args:
        query: The search query
        top_k: Number of results to return (default: 5)
        min_score: Minimum relevance score (default: 0.5)
        session_id: Optional session ID for v6 session-aware queries
    
    Returns:
        Context results with provenance information
    """
    try:
        import time
        start_time = time.time()
        
        # Visual feedback para tool execution
        if _visual_monitor:
            tool_args = {
                'query': query[:50] + "..." if len(query) > 50 else query,
                'top_k': top_k,
                'min_score': min_score
            }
            if session_id:
                tool_args['session_id'] = session_id
            _visual_monitor.tool_started("get_context", tool_args)
        
        if _tool_logger:
            _tool_logger.v9_flow("RETRIEVAL", f"Query: {query[:40]}...")
        
        server = get_v6_server()
        # v9: Unificar via _handle_tools_call para activar logs de flujo
        result = server._handle_tools_call({
            'name': 'get_context',
            'arguments': {
                'query': query,
                'top_k': top_k,
                'min_score': min_score,
                'session_id': session_id
            }
        })
        
        duration = time.time() - start_time
        
        # Extraer texto del resultado unificado
        if 'content' in result and result['content']:
            response_text = result['content'][0].get('text', 'No context found')
            
            # Visual feedback de finalización
            if _visual_monitor:
                _visual_monitor.tool_completed("get_context", f"Found {len(result['content'])} results", duration)
            
            return response_text
        
        # Visual feedback de resultados vacíos
        if _visual_monitor:
            _visual_monitor.tool_completed("get_context", "No results found", duration)
        
        return "No context found"
        
    except Exception as e:
        if _visual_monitor:
            _visual_monitor.tool_failed("get_context", str(e))
        if _tool_logger:
            _tool_logger.error(f"Query failed: {query[:30]}...", error=str(e))
        return f"Error: {str(e)}"


@mcp.tool()
@visual_tool_decorator
async def validate_response(response: str, evidence: list) -> str:
    """
    Validate a response against provided evidence.
    
    Args:
        response: The response text to validate
        evidence: List of evidence items to check against
    
    Returns:
        Validation result with confidence assessment
    """
    try:
        server = get_v6_server()
        result = server._handle_tools_call({
            'name': 'validate_response',
            'arguments': {
                'response': response,
                'evidence': evidence
            }
        })
        if 'content' in result and result['content']:
            return result['content'][0].get('text', 'Validation complete')
        return "Validation complete"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def index_status() -> str:
    """
    Get index status and statistics.
    
    Returns:
        Current status including chunk count, query count, uptime, and advanced features status
    """
    try:
        server = get_v6_server()
        result = server._handle_tools_call({'name': 'index_status', 'arguments': {}})
        text = ""
        if 'content' in result and result['content']:
            text = result['content'][0].get('text', '')
        
        # Add advanced features status
        orchestrator = get_orchestrator()
        if orchestrator:
            status = orchestrator.get_system_status()
            text += "\n\n=== Advanced Features ===\n"
            text += f"Mode: {status.get('config', {}).get('processing_mode', 'unknown')}\n"
            features = status.get('config', {}).get('enabled_features', [])
            text += f"Enabled: {', '.join(features)}\n"
        
        return text if text else "Status unavailable"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def escanear_urls_django(base_dir: Optional[str] = None) -> str:
    """
    Escanea urls.py y devuelve rutas en formato app_name:route_name.
    """
    resolved_base = _resolve_base_dir(base_dir)
    if not resolved_base:
        return f"BASE_DIR no existe: {base_dir or BASE_DIR}"

    valid_routes: Set[str] = set()

    for root, dirs, files in os.walk(resolved_base):
        dirs[:] = [d for d in dirs if not _should_skip_dir(d)]
        if "urls.py" not in files:
            continue

        file_path = Path(root) / "urls.py"
        content = _safe_read_text(file_path)
        if not content:
            continue

        app_name_match = re.search(r"\bapp_name\s*=\s*['\"]([^'\"]+)['\"]", content)
        app_name = app_name_match.group(1) if app_name_match else None
        if not app_name:
            continue

        names = re.findall(r"\bname\s*=\s*['\"]([^'\"]+)['\"]", content)
        for name in names:
            valid_routes.add(f"{app_name}:{name}")

    if not valid_routes:
        return "No se encontraron rutas con app_name y name en urls.py"

    return f"Rutas encontradas ({len(valid_routes)}):\n" + "\n".join(sorted(valid_routes))


@mcp.tool()
async def analizar_tokens_css(
    css_path: Optional[str] = None, base_dir: Optional[str] = None
) -> str:
    """
    Lee el CSS principal y extrae variables de diseño.
    """
    resolved_base = _resolve_base_dir(base_dir)
    if not resolved_base:
        return f"BASE_DIR no existe: {base_dir or BASE_DIR}"

    resolved_css_path = _resolve_css_path(resolved_base, css_path)
    if not resolved_css_path:
        return "No se encontró un archivo CSS válido en static/css"

    content = _safe_read_text(resolved_css_path)
    if not content:
        return f"No se pudo leer el archivo CSS: {resolved_css_path}"

    variables = re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", content)
    if not variables:
        return f"No se encontraron variables CSS en {resolved_css_path.name}"

    return "Variables de diseño del sistema:\n" + "\n".join(
        [f"{k}: {v.strip()}" for k, v in variables]
    )

# ============================================
# v9 Tools (Knowledge & Persistence)
# ============================================

@mcp.tool()
@visual_tool_decorator
async def memory_tool(command: str, file_path: str, content: Optional[str] = None, session_id: Optional[str] = None) -> str:
    """
    CRUD operations for persistent memory storage.
    
    Args:
        command: create, read, update, delete, or list
        file_path: Name of the memory file (e.g. 'user_preferences.txt')
        content: Data to store (for create/update)
        session_id: Optional session ID for isolation
    """
    try:
        if _tool_logger:
            _tool_logger.v9_flow("MEMORY", f"{command.upper()} on {file_path}")
            
        server = get_v6_server()
        # v9: Unificar via _handle_tools_call para activar logs de flujo
        result = server._handle_tools_call({
            'name': 'memory_tool',
            'arguments': {
                'command': command,
                'file_path': file_path,
                'content': content,
                'session_id': session_id
            }
        })
        
        if 'content' in result and result['content']:
            return result['content'][0].get('text', 'Success')
        return "Operación de memoria completada"
    except Exception as e:
        if _tool_logger:
            _tool_logger.error(f"Memory tool failed: {e}")
        return f"Error en memory_tool: {str(e)}"

@mcp.tool()
async def skills_tool(command: str, skill_id: str, content: Optional[str] = None, description: Optional[str] = None) -> str:
    """
    Manage Knowledge Skills (Claude-like skills).
    
    Args:
        command: create or list
        skill_id: Unique identifier for the skill
        content: Main instructions/knowledge for SKILL.md
        description: Short description for semantic search
    """
    try:
        server = get_v6_server()
        result = server._handle_tools_call({
            'name': 'skills_tool',
            'arguments': {
                'command': command,
                'skill_id': skill_id,
                'content': content,
                'description': description
            }
        })
        if 'content' in result and result['content']:
            return result['content'][0].get('text', 'Operación de skills completada')
        return "Operación de skills completada"
    except Exception as e:
        return f"Error en skills_tool: {str(e)}"

@mcp.tool()
async def ground_project_context(query: str) -> str:
    """
    Retrieve factual evidence from project requirements and vision documents.
    Use this to ensure compliance with project goals.
    """
    try:
        server = get_v6_server()
        result = server._handle_tools_call({
            'name': 'ground_project_context',
            'arguments': {'query': query}
        })
        if 'content' in result and result['content']:
            return result['content'][0].get('text', 'No evidence found')
        return "No evidence found"
    except Exception as e:
        return f"Error en grounding: {str(e)}"


# ============================================
# V7 Tools (Session Management)
# ============================================

@mcp.tool()
@visual_tool_decorator
async def create_session(session_id: str, session_type: str = "general", strategy: str = "trimming") -> str:
    """
    Create a new development session for context tracking.
    
    Args:
        session_id: Unique session identifier
        session_type: Type of session - feature, bugfix, review, refactor, or general
        strategy: Memory strategy - trimming (default) or summarizing
    
    Returns:
        Confirmation of session creation with details
    """
    try:
        if _tool_logger:
            _tool_logger.session("Creating", session_id, type=session_type, strategy=strategy)
        
        server = get_v6_server()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            server._create_session({
                'session_id': session_id,
                'session_type': session_type,
                'strategy': strategy
            })
        )
        loop.close()
        
        if _tool_logger:
            _tool_logger.success(f"Session created: {session_id}")
        
        if 'content' in result and result['content']:
            return result['content'][0].get('text', 'Session created')
        return "Session created"
    except Exception as e:
        if _tool_logger:
            _tool_logger.error(f"Session creation failed: {session_id}", error=str(e))
        return f"Error: {str(e)}"


@mcp.tool()
async def get_session_summary(session_id: str) -> str:
    """
    Get summary of a session including entities and interactions.
    
    Args:
        session_id: Session ID to get summary for
    
    Returns:
        Session summary with type, turn count, and entities mentioned
    """
    try:
        server = get_v6_server()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            server._get_session_summary({'session_id': session_id})
        )
        loop.close()
        if 'content' in result and result['content']:
            return result['content'][0].get('text', 'Session not found')
        return "Session not found"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def list_sessions() -> str:
    """
    List all active sessions.
    
    Returns:
        List of active sessions with their turn counts
    """
    try:
        server = get_v6_server()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            server._list_sessions({})
        )
        loop.close()
        if 'content' in result and result['content']:
            return result['content'][0].get('text', 'No sessions')
        return "No sessions"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def delete_session(session_id: str) -> str:
    """
    Delete a session.
    
    Args:
        session_id: Session ID to delete
    
    Returns:
        Confirmation of deletion
    """
    try:
        server = get_v6_server()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            server._delete_session({'session_id': session_id})
        )
        loop.close()
        if 'content' in result and result['content']:
            return result['content'][0].get('text', 'Session deleted')
        return "Session deleted"
    except Exception as e:
        return f"Error: {str(e)}"


# ============================================
# V7 Tools (Code Indexing)
# ============================================

@mcp.tool()
async def index_code(directory: str, recursive: bool = True) -> str:
    """
    Index code structure from a directory.
    
    Args:
        directory: Absolute path to directory to index
        recursive: Whether to index recursively (default: True)
    
    Returns:
        Indexing statistics including files, functions, and classes indexed
    """
    try:
        if _tool_logger:
            _tool_logger.index(f"Indexing: {directory}", recursive=recursive)
        
        server = get_v6_server()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            server._index_code({
                'directory': directory,
                'recursive': recursive
            })
        )
        loop.close()
        
        if _tool_logger:
            _tool_logger.success(f"Indexed: {directory}")
        
        if 'content' in result and result['content']:
            return result['content'][0].get('text', 'Indexing complete')
        return "Indexing complete"
    except Exception as e:
        if _tool_logger:
            _tool_logger.error(f"Indexing failed: {directory}", error=str(e))
        return f"Error: {str(e)}"


@mcp.tool()
async def search_entity(name: str, entity_type: str = "any") -> str:
    """
    Search for a code entity (function or class).
    
    Args:
        name: Entity name to search for (supports partial matches)
        entity_type: Type of entity - function, class, or any (default)
    
    Returns:
        Matching entities with their locations and signatures
    """
    try:
        server = get_v6_server()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            server._search_entity({
                'name': name,
                'entity_type': entity_type
            })
        )
        loop.close()
        if 'content' in result and result['content']:
            return result['content'][0].get('text', 'No entities found')
        return "No entities found"
    except Exception as e:
        return f"Error: {str(e)}"


# ============================================
# Advanced Features Tools
# ============================================

@mcp.tool()
async def process_advanced(query: str, documents: Optional[List[Dict[str, Any]]] = None, domain: str = "general") -> str:
    """
    Process a query using ALL advanced features:
    - Dynamic Chunking Adaptativo
    - Multi-Vector Retrieval (MVR)
    - Query Expansion Automática
    - Confidence Calibration Dinámica
    
    Args:
        query: The search query to process
        documents: Optional list of documents with 'content' and 'path' keys
        domain: Domain context for processing (default: general)
    
    Returns:
        Comprehensive processing result with expanded queries, chunks, search results, and confidence scores
    """
    try:
        orchestrator = get_orchestrator()
        if not orchestrator:
            return "Error: Advanced features orchestrator not available"
        
        context = {"domain": domain}
        result = await orchestrator.process_advanced(query, documents or [], context)
        
        output = "=== Advanced Processing Result ===\n"
        output += f"Query: {result.query}\n\n"
        
        if hasattr(result, 'expanded_queries') and result.expanded_queries:
            output += f"Expanded Terms: {', '.join(result.expanded_queries[:5])}\n"
        
        if hasattr(result, 'chunks') and result.chunks:
            output += f"\nChunks Generated: {len(result.chunks)}\n"
            for i, chunk in enumerate(result.chunks[:3]):
                if hasattr(chunk, 'text'):
                    output += f"  [{i+1}] {chunk.text[:100]}...\n"
        
        if hasattr(result, 'search_results') and result.search_results:
            output += f"\nSearch Results: {len(result.search_results)}\n"
            for i, sr in enumerate(result.search_results[:3]):
                score = getattr(sr, 'score', 0)
                output += f"  [{i+1}] Score: {score:.3f}\n"
        
        if hasattr(result, 'feature_status'):
            output += "\nFeature Status:\n"
            for feature, status in result.feature_status.items():
                status_val = getattr(status, 'value', 'unknown')
                output += f"  • {feature}: {status_val}\n"
        
        return output
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def expand_query(query: str, max_expansions: int = 5, strategies: Optional[List[str]] = None) -> str:
    """
    Automatically expand a query for better search coverage.
    
    Strategies available:
    - semantic: Expansion based on embeddings
    - statistical: Term co-occurrence
    - contextual: Domain-specific patterns
    - synonyms: Synonym expansion
    
    Args:
        query: The original search query
        max_expansions: Maximum number of expansions (default: 5)
        strategies: List of strategies to use (default: all)
    
    Returns:
        Expanded queries and terms
    """
    try:
        from advanced_features.query_expansion import expand_query as do_expand
        
        strats = strategies or ["semantic", "statistical", "contextual"]
        expansion = do_expand(query, max_expansions=max_expansions, strategies=strats)
        
        output = "=== Query Expansion ===\n"
        output += f"Original: {query}\n\n"
        
        if hasattr(expansion, 'expanded_queries'):
            output += "Expanded Queries:\n"
            for eq in expansion.expanded_queries[:max_expansions]:
                output += f"  • {eq}\n"
        
        if hasattr(expansion, 'expanded_terms'):
            output += f"\nExpanded Terms: {', '.join(expansion.expanded_terms[:10])}\n"
        
        return output
    except ImportError:
        return "Error: Query expansion module not available"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def chunk_document(content: str, file_path: str = "document.txt", min_size: int = 200, max_size: int = 1000) -> str:
    """
    Apply dynamic adaptive chunking to a document.
    
    Features:
    - Auto-detects content type (code, markdown, text, JSON, XML)
    - Semantic chunking for coherence
    - Structural chunking for code
    - Intelligent overlapping
    
    Args:
        content: The document content to chunk
        file_path: File path hint for type detection
        min_size: Minimum chunk size in characters (default: 200)
        max_size: Maximum chunk size in characters (default: 1000)
    
    Returns:
        List of chunks with metadata
    """
    try:
        from advanced_features.dynamic_chunking import adaptive_chunking
        
        chunks = adaptive_chunking(
            text=content,
            file_path=file_path,
            min_chunk_size=min_size,
            max_chunk_size=max_size
        )
        
        output = "=== Dynamic Chunking Result ===\n"
        output += f"File: {file_path}\n"
        output += f"Total Chunks: {len(chunks)}\n\n"
        
        for i, chunk in enumerate(chunks[:5]):
            text = chunk.text if hasattr(chunk, 'text') else str(chunk)[:200]
            output += f"[Chunk {i+1}]\n{text[:200]}...\n\n"
        
        if len(chunks) > 5:
            output += f"... and {len(chunks) - 5} more chunks\n"
        
        return output
    except ImportError:
        return "Error: Dynamic chunking module not available"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def get_system_status() -> str:
    """
    Get comprehensive system status for all components.
    
    Returns:
        Status of V6 server, advanced features, and all enabled components
    """
    try:
        output = "=== MCP Hub v7 System Status ===\n\n"
        
        # V6 Server Status
        try:
            server = get_v6_server()
            output += "📊 V7 Core Server: ✅ Running\n"
            status_result = server._index_status({})
            if 'content' in status_result and status_result['content']:
                output += status_result['content'][0].get('text', '')
        except Exception as e:
            output += f"📊 V7 Core Server: ❌ Error - {e}\n"
        
        output += "\n"
        
        # Advanced Features Status
        try:
            orchestrator = get_orchestrator()
            if orchestrator:
                status = orchestrator.get_system_status()
                output += "🚀 Advanced Features Orchestrator: ✅ Available\n"
                output += f"   Mode: {status.get('config', {}).get('processing_mode', 'unknown')}\n"
                
                features = status.get('config', {}).get('enabled_features', [])
                output += f"   Enabled Features ({len(features)}):\n"
                for f in features:
                    output += f"     • {f.replace('_', ' ').title()}\n"
                
                if 'statistics' in status:
                    stats = status['statistics']
                    output += f"   Operations: {stats.get('operations_count', stats.get('total_operations', 0))}\n"
            else:
                output += "🚀 Advanced Features: ⚠️ Not initialized\n"
        except Exception as e:
            output += f"🚀 Advanced Features: ❌ Error - {e}\n"
        
        return output
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def add_feedback(query: str, result_doc_id: str, relevance_score: float, was_helpful: bool) -> str:
    """
    Add feedback to the system for dynamic recalibration.
    
    This feedback is used to improve confidence calibration and search ranking over time.
    
    Args:
        query: The original query that was searched
        result_doc_id: ID of the document/result being rated
        relevance_score: Score from 0.0 to 1.0 indicating relevance
        was_helpful: Whether the result was helpful (true/false)
    
    Returns:
        Confirmation of feedback recorded
    """
    try:
        orchestrator = get_orchestrator()
        if not orchestrator:
            return "Error: Advanced features orchestrator not available"
        
        orchestrator.add_feedback(
            query=query,
            result_doc_id=result_doc_id,
            relevance_score=relevance_score,
            was_helpful=was_helpful,
            context={}
        )
        
        return f"✅ Feedback recorded:\n  Query: {query}\n  Doc: {result_doc_id}\n  Score: {relevance_score}\n  Helpful: {was_helpful}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def optimize_configuration() -> str:
    """
    Optimize system configuration based on usage patterns and feedback.
    
    Analyzes historical usage to recommend or auto-apply optimizations.
    
    Returns:
        Optimization recommendations and any auto-applied changes
    """
    try:
        orchestrator = get_orchestrator()
        if not orchestrator:
            return "Error: Advanced features orchestrator not available"
        
        result = orchestrator.optimize_configuration()
        
        output = "=== Configuration Optimization ===\n\n"
        
        if 'current_performance' in result:
            perf = result['current_performance']
            output += "📈 Current Performance:\n"
            output += f"   Avg Processing Time: {perf.get('avg_processing_time', 0)*1000:.2f}ms\n"
            output += f"   Total Operations: {perf.get('total_operations', 0)}\n\n"
        
        if 'recommendations' in result:
            output += "💡 Recommendations:\n"
            for rec in result['recommendations']:
                output += f"   • {rec}\n"
            output += "\n"
        
        if 'auto_applied' in result and result['auto_applied']:
            output += "✅ Auto-Applied Changes:\n"
            for change in result['auto_applied']:
                output += f"   • {change}\n"
        else:
            output += "ℹ️ No auto-applied changes\n"
        
        return output
    except Exception as e:
        return f"Error: {str(e)}"


# ============================================
# CODE GUARDIAN TOOLS (Anti-Duplication System)
# ============================================

@mcp.tool()
@visual_tool_decorator
async def check_code_creation(name: str, code_type: str, content: str, context: Optional[Dict] = None, auto_prevent: bool = True) -> str:
    """
    🛡️ PREVIENE duplicación ANTES de crear código
    
    Detecta si el código que intentas crear ya existe y sugiere alternativas.
    
    Args:
        name: Nombre del elemento (función, clase, etc.)
        code_type: Tipo de código: function, class, module, template, model, view
        content: Contenido completo del código propuesto
        context: Contexto adicional (opcional)
        auto_prevent: Si debe prevenir automáticamente la creación (default: True)
    
    Returns:
        Resultado de la validación con alertas y sugerencias
    """
    try:
        tools = get_code_guardian_tools()
        if tools is None:
            return "❌ Error: Code Guardian no está disponible"
        
        result = tools['check_code_creation'](
            code_content=content,
            file_path=name,
            code_type=code_type
        )
        
        if result.get('alert'):
            alert = result['alert']
            if alert.get('severity') == 'critical':
                output = f"🚨 CÓDIGO PREVENIDO: {alert.get('message', 'Duplicación detectada')}\n\n"
                if result.get('suggestions'):
                    output += "💡 SUGERENCIAS:\n"
                    for suggestion in result['suggestions']:
                        output += f"  • {suggestion}\n"
                return output
            else:
                return f"⚠️ ADVERTENCIA: {alert.get('message', 'Similitud detectada')}\n💡 Recomendaciones: {alert.get('recommendations', ['Revisar código existente'])}"
        
        else:
            return f"✅ CÓDIGO APROBADO: {result.get('message', 'No se detectaron duplicados significativos')}"
            
    except Exception as e:
        return f"Error en Code Guardian: {str(e)}"


@mcp.tool()
@visual_tool_decorator
async def analyze_project_redundancy(project_path: Optional[str] = None, threshold: float = 0.85) -> str:
    """
    📊 ANALIZA redundancia en TODO el proyecto
    
    Escanea todo el proyecto en busca de código duplicado o redundante.
    
    Args:
        project_path: Ruta del proyecto (default: directorio actual)
        threshold: Umbral de similitud (0.0 a 1.0, default: 0.85)
    
    Returns:
        Análisis completo de redundancias encontradas
    """
    try:
        tools = get_code_guardian_tools()
        if tools is None:
            return "❌ Error: Code Guardian no está disponible"
        
        result = tools['analyze_project_redundancy'](
            project_path=project_path or '.',
            threshold=threshold
        )
        
        output = "=== ANÁLISIS DE REDUNDANCIA DEL PROYECTO ===\n\n"
        
        redundant_groups = result.get('redundant_groups', [])
        total_elements = result.get('total_elements', 0)
        
        if redundant_groups:
            output += f"🚨 ENCONTRADAS {len(redundant_groups)} GRUPOS REDUNDANTES:\n\n"
            
            for i, group in enumerate(redundant_groups, 1):
                similarity = group.get('similarity', 0)
                output += f"{i}. GRUPO DE REDUNDANCIA (similitud: {similarity:.2%})\n"
                
                if 'codes' in group:
                    output += f"   📄 Códigos involucrados:\n"
                    for code in group['codes']:
                        name = code.get('name', 'Desconocido')
                        code_type = code.get('type', 'unknown')
                        file_path = code.get('file_path', 'unknown')
                        output += f"      • {name} ({code_type}) - {file_path}\n"
                
                if 'recommendations' in group:
                    output += f"   💡 Recomendaciones:\n"
                    for rec in group['recommendations']:
                        output += f"      • {rec}\n"
                
                output += "\n"
        
        else:
            output += "✅ No se encontraron redundancias significativas\n"
        
        output += f"\n📈 RESUMEN:\n"
        output += f"   Total de elementos analizados: {total_elements}\n"
        output += f"   Redundancias encontradas: {len(redundant_groups)}\n"
        output += f"   Umbral de similitud: {threshold:.2%}\n"
        
        return output
        
    except Exception as e:
        return f"Error analizando redundancia: {str(e)}"


@mcp.tool()
@visual_tool_decorator
async def get_code_suggestions(query: str, code_type: Optional[str] = None, limit: int = 5) -> str:
    """
    💡 SUGIERE código reutilizable existente
    
    Busca código existente que pueda ser reutilizado para tu necesidad.
    
    Args:
        query: Descripción de lo que necesitas
        code_type: Tipo de código (opcional): function, class, module, etc.
        limit: Número máximo de sugerencias (default: 5)
    
    Returns:
        Sugerencias de código reutilizable con detalles
    """
    try:
        tools = get_code_guardian_tools()
        if tools is None:
            return "❌ Error: Code Guardian no está disponible"
        
        suggestions = tools['get_code_suggestions'](
            query=query,
            limit=limit
        )
        
        if not suggestions:
            return "🔍 No se encontraron sugerencias relevantes de código reutilizable"
        
        output = f"=== SUGERENCIAS DE CÓDIGO REUTILIZABLE ===\n\n"
        output += f"📋 Búsqueda: '{query}'\n\n"
        
        for i, suggestion in enumerate(suggestions, 1):
            name = suggestion.get('name', 'Desconocido')
            code_type = suggestion.get('type', 'unknown')
            file_path = suggestion.get('file_path', 'unknown')
            similarity = suggestion.get('similarity', 0)
            complexity = suggestion.get('complexity', 0)
            
            output += f"{i}. 💡 SUGERENCIA: {name} ({code_type})\n"
            output += f"   📄 Archivo: {file_path}\n"
            output += f"   🔗 Similitud: {similarity:.2%}\n"
            output += f"   📊 Complejidad: {complexity:.2f}\n"
            
            if suggestion.get('usage_pattern'):
                output += f"   📈 Patrón de uso: {suggestion['usage_pattern']}\n"
            
            if suggestion.get('dependencies'):
                deps = suggestion['dependencies'][:3] if isinstance(suggestion['dependencies'], list) else []
                output += f"   🔗 Dependencias: {', '.join(deps)}\n"
            
            output += "\n"
        
        return output
        
    except Exception as e:
        return f"Error obteniendo sugerencias: {str(e)}"


@mcp.tool()
@visual_tool_decorator
async def learn_from_context(context_files: Optional[List[str]] = None) -> str:
    """
    🧠 APRENDE de archivos de contexto específicos
    
    Actualiza el conocimiento del Code Guardian con archivos de contexto.
    
    Args:
        context_files: Lista de archivos de contexto (default: archivos del proyecto)
    
    Returns:
        Resultado del aprendizaje con estadísticas
    """
    try:
        tools = get_code_guardian_tools()
        if tools is None:
            return "❌ Error: Code Guardian no está disponible"
        
        result = tools['learn_from_context'](context_files=context_files)
        
        output = "=== APRENDIZAJE DE CONTEXTO ===\n\n"
        output += f"📚 Archivos procesados: {result.get('files_processed', 0)}\n"
        output += f"🔍 Elementos de código aprendidos: {result.get('elements_learned', 0)}\n"
        
        processing_time = result.get('processing_time', 0)
        output += f"⏱️ Tiempo de procesamiento: {processing_time:.2f}s\n"
        
        files_processed = result.get('files_processed', 0)
        elements_learned = result.get('elements_learned', 0)
        if files_processed > 0:
            output += f"📈 Promedio de elementos por archivo: {elements_learned/files_processed:.1f}\n"
        
        if result.get('errors'):
            errors = result['errors']
            output += f"\n⚠️ Errores encontrados: {len(errors)}\n"
            for error in errors[:3]:  # Mostrar primeros 3 errores
                output += f"   • {error}\n"
        
        output += f"\n✅ Base de conocimiento actualizada exitosamente"
        
        return output
        
    except Exception as e:
        return f"Error en aprendizaje de contexto: {str(e)}"


# ============================================
# Smart Session Orchestrator
# ============================================
_smart_orchestrator = None

def get_smart_orchestrator():
    """Get or create singleton instance of Smart Session Orchestrator"""
    global _smart_orchestrator
    if _smart_orchestrator is None:
        try:
            from smart_session_orchestrator import SmartSessionOrchestrator
            _smart_orchestrator = SmartSessionOrchestrator(mcp_server=get_v6_server())
        except Exception as e:
            print(f"Warning: Could not create smart orchestrator: {e}", file=sys.stderr)
            _smart_orchestrator = None
    return _smart_orchestrator


# ============================================
# Smart Session Tools (Auto-Management)
# ============================================

@mcp.tool()
async def smart_session_init(project_path: Optional[str] = None, context: str = "", force_new: bool = False) -> str:
    """
    Intelligent session initialization - automatically detects project and session type.
    
    This smart tool:
    - Detects the project from the path (or uses current directory)
    - Reuses existing sessions for the same project (if recent)
    - Auto-detects session type from context (feature, bugfix, refactor, review)
    - Auto-indexes code if needed
    - Maintains full persistence
    
    Args:
        project_path: Path to project directory (optional, uses CWD if not provided)
        context: Context text to detect session type (e.g., "fixing login bug", "adding new feature")
        force_new: Force creation of a new session even if one exists
    
    Returns:
        Session information including ID, type, and status
    
    Example usage:
        smart_session_init("/path/to/my-app", "implementing user authentication")
        -> Creates or reuses a "feature" type session for my-app
    """
    try:
        if _tool_logger:
            _tool_logger.tool("smart_session_init", project=project_path or "auto", context=context[:30] if context else "none")
        
        orchestrator = get_smart_orchestrator()
        if not orchestrator:
            return "Error: Smart orchestrator not available"
        
        result = await orchestrator.smart_initialize(
            project_path=project_path,
            context=context,
            force_new_session=force_new
        )
        
        # Log result
        if _tool_logger and result.get("session_id"):
            status = "NEW" if result.get("is_new") else "REUSED"
            _tool_logger.session(status, result['session_id'], type=result.get('session_type', 'general'))
        
        output = "=== Smart Session Initialization ===\n\n"
        
        if result.get("session_id"):
            status = "🆕 CREATED" if result.get("is_new") else "♻️ REUSED"
            output += f"📌 Session: {result['session_id']}\n"
            output += f"   Status: {status}\n"
            output += f"   Type: {result.get('session_type', 'general')}\n"
            output += f"   Project: {result.get('project_path', 'N/A')}\n"
            
            if result.get("was_indexed"):
                output += "   📁 Code: Auto-indexed\n"
            
            output += f"\n✅ {result.get('message', 'Ready')}\n"
        else:
            output += f"❌ {result.get('message', 'Error initializing session')}\n"
        
        return output
    except Exception as e:
        if _tool_logger:
            _tool_logger.error("smart_session_init failed", error=str(e))
        return f"Error: {str(e)}"


@mcp.tool()
async def smart_query(query: str, project_path: Optional[str] = None) -> str:
    """
    Execute a query with automatic session management.
    
    This tool automatically:
    - Creates or reuses a session based on the project
    - Executes the query with session context
    - Maintains history for future queries
    
    Args:
        query: The search query to execute
        project_path: Optional project path (uses current session if not provided)
    
    Returns:
        Query results with session context
    """
    try:
        if _tool_logger:
            _tool_logger.tool("smart_query", query=query[:40])
        
        orchestrator = get_smart_orchestrator()
        if not orchestrator:
            return "Error: Smart orchestrator not available"
        
        result = await orchestrator.smart_query(query, project_path, auto_session=True)
        
        if "error" in result:
            if _tool_logger:
                _tool_logger.error("smart_query failed", error=result['error'])
            return f"Error: {result['error']}"
        
        if _tool_logger:
            _tool_logger.success("smart_query completed", session=result.get('session_id', 'N/A'))
        
        output = "=== Smart Query Result ===\n"
        output += f"Session: {result.get('session_id', 'N/A')}\n\n"
        
        # Extract actual result
        if "result" in result:
            res = result["result"]
            if isinstance(res, dict) and "content" in res:
                for content in res.get("content", []):
                    output += content.get("text", "") + "\n"
            else:
                output += str(res)
        
        return output
    except Exception as e:
        if _tool_logger:
            _tool_logger.error("smart_query exception", error=str(e))
        return f"Error: {str(e)}"


@mcp.tool()
async def get_smart_status() -> str:
    """
    Get comprehensive status of the smart session orchestrator.
    
    Returns:
        Statistics and current state of smart session management including:
        - Active projects and their sessions
        - Session statistics (created, reused, indexed)
        - Current active session
    """
    try:
        orchestrator = get_smart_orchestrator()
        if not orchestrator:
            return "Error: Smart orchestrator not available"
        
        stats = orchestrator.get_statistics()
        all_sessions = orchestrator.get_all_project_sessions()
        
        output = "=== Smart Session Orchestrator Status ===\n\n"
        
        # Current session
        current = stats.get("current_session")
        output += f"📌 Current Session: {current or 'None'}\n\n"
        
        # Statistics
        output += "📊 Statistics:\n"
        stat_data = stats.get("statistics", {})
        output += f"   Sessions Created: {stat_data.get('sessions_created', 0)}\n"
        output += f"   Sessions Reused: {stat_data.get('sessions_reused', 0)}\n"
        output += f"   Auto-Indexes: {stat_data.get('auto_indexes', 0)}\n\n"
        
        # Active projects
        output += f"📁 Active Projects: {stats.get('active_projects', 0)}\n"
        output += f"📂 Indexed Projects: {stats.get('indexed_projects', 0)}\n\n"
        
        # Project details
        if all_sessions:
            output += "🗂️ Project Sessions:\n"
            for proj in all_sessions[:5]:  # Show first 5
                output += f"   • {proj.get('project_path', 'N/A')}\n"
                output += f"     Session: {proj.get('session_id', 'N/A')}\n"
                output += f"     Type: {proj.get('session_type', 'N/A')}\n"
            
            if len(all_sessions) > 5:
                output += f"   ... and {len(all_sessions) - 5} more\n"
        
        return output
    except Exception as e:
        return f"Error: {str(e)}"


# ============================================
# Extended Knowledge System
# ============================================
_extended_knowledge = None
_quality_guardian = None

def get_extended_knowledge():
    """Get or create singleton instance of Extended Knowledge Indexer"""
    global _extended_knowledge
    if _extended_knowledge is None:
        try:
            from extended_knowledge import ExtendedKnowledgeIndexer
            _extended_knowledge = ExtendedKnowledgeIndexer()
            _extended_knowledge.load_index()  # Cargar índice existente
        except Exception as e:
            print(f"Warning: Could not create extended knowledge: {e}", file=sys.stderr)
            _extended_knowledge = None
    return _extended_knowledge

def get_quality_guardian_instance():
    """Get or create singleton instance of Quality Guardian"""
    global _quality_guardian
    if _quality_guardian is None:
        try:
            from extended_knowledge import QualityGuardian
            _quality_guardian = QualityGuardian()
        except Exception as e:
            print(f"Warning: Could not create quality guardian: {e}", file=sys.stderr)
            _quality_guardian = None
    return _quality_guardian


# ============================================
# Extended Knowledge Tools
# ============================================

@mcp.tool()
async def extended_index(directory: str, recursive: bool = True) -> str:
    """
    Index code with EXTENDED knowledge - goes beyond functions/classes.
    
    This tool indexes:
    - 📌 Constants and configurations
    - 🌐 API endpoints (Django, Flask, FastAPI)
    - 📦 Data models (Django, Pydantic, dataclass, SQLAlchemy)
    - 🎨 Design patterns (Singleton, Factory, Observer, etc.)
    - 📝 TODOs, FIXMEs, and HACKs
    - 🔗 Module dependencies
    
    Args:
        directory: Path to directory to index
        recursive: Index subdirectories (default: True)
    
    Returns:
        Extended indexing statistics
    """
    try:
        if _tool_logger:
            _tool_logger.tool("extended_index", directory=directory)
        
        indexer = get_extended_knowledge()
        if not indexer:
            return "Error: Extended knowledge indexer not available"
        
        stats = indexer.index_directory_extended(directory, recursive)
        indexer.save_index()
        
        if _tool_logger:
            _tool_logger.success(f"Extended indexed: {stats.get('files', 0)} files", 
                               endpoints=stats.get('endpoints', 0), 
                               models=stats.get('models', 0))
        
        output = "=== Extended Knowledge Indexing Complete ===\n\n"
        output += f"📁 Files Processed: {stats.get('files', 0)}\n"
        output += f"📌 Constants/Configs: {stats.get('constants', 0)}\n"
        output += f"🌐 API Endpoints: {stats.get('endpoints', 0)}\n"
        output += f"📦 Data Models: {stats.get('models', 0)}\n"
        output += f"🎨 Design Patterns: {stats.get('patterns', 0)}\n"
        output += f"📝 TODOs/FIXMEs: {stats.get('todos', 0)}\n"
        
        # Incluir recordatorio de calidad
        guardian = get_quality_guardian_instance()
        if guardian:
            output += guardian.get_reminder()
        
        return output
    except Exception as e:
        if _tool_logger:
            _tool_logger.error("extended_index failed", error=str(e))
        return f"Error: {str(e)}"


@mcp.tool()
async def extended_search(query: str) -> str:
    """
    Search through extended knowledge (constants, APIs, models, patterns).
    
    Goes beyond function/class search to find:
    - Configuration values
    - API endpoints matching your query
    - Data models
    - And more...
    
    Args:
        query: Search query (name, path, or keyword)
    
    Returns:
        Matching items from extended knowledge
    """
    try:
        indexer = get_extended_knowledge()
        if not indexer:
            return "Error: Extended knowledge indexer not available"
        
        results = indexer.search_extended(query)
        
        if not results:
            return f"No results found for '{query}' in extended knowledge."
        
        output = f"=== Extended Search Results for '{query}' ===\n\n"
        
        for result in results[:15]:  # Limit to 15 results
            rtype = result.get("type", "unknown")
            if rtype == "constant":
                output += f"📌 CONSTANT: {result['name']}\n"
                output += f"   Module: {result['module']}\n"
                output += f"   Value: {result['value'][:50]}...\n\n"
            elif rtype == "endpoint":
                output += f"🌐 ENDPOINT: {result['method']} {result['path']}\n"
                output += f"   Framework: {result['framework']}\n"
                output += f"   Module: {result['module']}\n\n"
            elif rtype == "model":
                output += f"📦 MODEL: {result['name']}\n"
                output += f"   Type: {result['model_type']}\n"
                output += f"   Fields: {result['fields']}\n\n"
        
        if len(results) > 15:
            output += f"... and {len(results) - 15} more results\n"
        
        return output
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def get_knowledge_summary() -> str:
    """
    Get comprehensive summary of all extended knowledge.
    
    Includes:
    - Statistics of indexed items
    - Key API endpoints
    - Data models overview
    - Detected design patterns
    - High priority TODOs/FIXMEs
    - Quality Guardian principles (ALWAYS included)
    
    Returns:
        Complete knowledge summary with quality reminders
    """
    try:
        indexer = get_extended_knowledge()
        if not indexer:
            return "Error: Extended knowledge indexer not available"
        
        return indexer.get_knowledge_summary()
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def sync_world_model() -> str:
    """
    Synchronize the JEPA World Model with current files in data/project_context/.
    Use this after updating project requirements or vision documents.
    """
    global _v6_server
    if _v6_server:
        result = _v6_server.factual_auditor.update_world_model()
        return str(result)
    return "AGI-Context-Vortex Server not initialized."

@mcp.tool()
def test_colors_flow() -> str:
    """
    Test tool to verify visual matrix flow and colors in logs.
    """
    global _v6_server
    if _v6_server and _color_logger and Colors:
        _color_logger.matrix_flow("COLOR-TEST", "INVOKED", color=Colors.GREEN_NEON)
        _color_logger.jepa_flow(
            "JEPA-RAINBOW",
            f"{Colors.RED}R{Colors.YELLOW}A{Colors.GREEN}I{Colors.CYAN}N{Colors.BLUE}B{Colors.MAGENTA}O{Colors.RESET}W test",
        )
        return "Color test executed. Check terminal output."
    return "Server not initialized."
@mcp.tool()
def audit_jepa(proposal: str, query: str = "general project alignment") -> str:
    """
    JEPA-inspired Factual Auditor. Validates a proposal against the Project World Model.
    Use this to detect anti-hallucination and ensure alignment with Roadmap and Vision.
    """
    global _v6_server
    if _v6_server:
        result = _v6_server._handle_audit_jepa({"proposal": proposal, "query": query})
        return str(result['content'][0]['text'])
    return "AGI-Context-Vortex Server not initialized."

@mcp.tool()
async def check_quality(code: str) -> str:
    """
    Check code quality against Quality Guardian principles.
    
    Analyzes code for:
    - 🚫 Redundancy (repeated code patterns)
    - 🔄 Duplication (copy-pasted code)
    - 📈 Scalability issues (functions too long)
    - 🎯 Single responsibility violations
    - 🏜️ DRY principle violations
    
    Args:
        code: Code snippet to analyze
    
    Returns:
        Quality warnings and suggestions with principle reminders
    
    IMPORTANT: Always use this before writing new code to ensure quality!
    """
    try:
        if _tool_logger:
            _tool_logger.quality(f"Analyzing code ({len(code)} chars)")
        
        guardian = get_quality_guardian_instance()
        if not guardian:
            return "Error: Quality Guardian not available"
        
        warnings = guardian.check_code_quality(code)
        
        if _tool_logger:
            if warnings:
                _tool_logger.warning("Quality issues found", count=len(warnings))
            else:
                _tool_logger.success("Quality check passed")
        
        output = "=== 🛡️ Quality Guardian Analysis ===\n\n"
        
        if warnings:
            output += f"⚠️ Found {len(warnings)} potential issues:\n\n"
            for w in warnings:
                severity_icon = "🔴" if w['severity'] == "warning" else "🟡"
                output += f"{severity_icon} [{w['principle'].upper()}] Line {w.get('line', '?')}\n"
                output += f"   {w['message']}\n\n"
        else:
            output += "✅ No quality issues detected in this code!\n\n"
        
        # SIEMPRE incluir los principios
        output += guardian.get_reminder()
        
        return output
    except Exception as e:
        if _tool_logger:
            _tool_logger.error("check_quality failed", error=str(e))
        return f"Error: {str(e)}"


@mcp.tool()
async def get_quality_principles() -> str:
    """
    Get full Quality Guardian principles documentation.
    
    Returns the complete guide to code quality principles that are
    ALWAYS enforced by the MCP system:
    
    - 🚫 No Redundancy
    - 🔄 No Duplication  
    - 📈 Scalability
    - 🎯 Single Responsibility
    - 🏜️ DRY (Don't Repeat Yourself)
    
    Use this as a reference before writing any code!
    """
    try:
        guardian = get_quality_guardian_instance()
        if not guardian:
            return "Error: Quality Guardian not available"
        
        return guardian.get_principles_summary()
    except Exception as e:
        return f"Error: {str(e)}"


# ============================================
# Graceful Shutdown Handler
# ============================================

def graceful_shutdown(logger=None):
    """
    Save all data before shutdown.
    Called when Ctrl+C is pressed.
    """
    if logger:
        logger.divider("Shutdown")
        logger.info("Guardando datos antes de cerrar...")
    else:
        print("\n⏳ Guardando datos antes de cerrar...", file=sys.stderr)
    
    saved_items = []
    
    try:
        # 1. Guardar sesiones del servidor v6
        try:
            server = get_v6_server()
        except Exception as e:
            if logger:
                logger.warning(f"No se pudo obtener servidor v6 durante shutdown: {e}")
            else:
                print(f"⚠️  No se pudo obtener servidor v6 durante shutdown: {e}", file=sys.stderr)
            server = None
            
        if server and hasattr(server, 'session_manager'):
            if hasattr(server.session_manager, 'save_all_sessions'):
                server.session_manager.save_all_sessions()
                saved_items.append("Sessions")
        
        # 2. Guardar índice de código
        if server and hasattr(server, 'indexer'):
            if hasattr(server.indexer, 'save_index'):
                server.indexer.save_index()
                saved_items.append("Code Index")
        
        # 3. Guardar índice de vectores
        if server and hasattr(server, 'index'):
            if hasattr(server.index, 'save'):
                server.index.save()
                saved_items.append("Vectors")
        
        # 4. Guardar Smart Session Orchestrator state
        orchestrator = get_smart_orchestrator()
        if orchestrator:
            if hasattr(orchestrator, '_save_state'):
                orchestrator._save_state()
                saved_items.append("Smart Sessions")
        
        # 5. Guardar Extended Knowledge index
        extended = get_extended_knowledge()
        if extended:
            extended.save_index()
            saved_items.append("Extended Knowledge")
        
        if logger:
            logger.success(f"Datos guardados: {', '.join(saved_items)}")
            logger.divider()
            logger.info("👋 ¡Hasta pronto! MCP Hub v10 Code Guardian cerrado correctamente.")
        else:
            print(f"✅ Guardado: {', '.join(saved_items)}", file=sys.stderr)
            print("👋 ¡Hasta pronto!", file=sys.stderr)

        # 6. Cerrar archivo de logs (AL FINAL)
        if _tool_logger and hasattr(_tool_logger, 'close'):
            _tool_logger.close()
            
    except Exception as e:
        if logger:
            logger.error(f"Error durante shutdown: {e}")
        else:
            print(f"❌ Error: {e}", file=sys.stderr)


# ============================================
# Entry Point
# ============================================

def find_available_port(start_port: int = 8765, max_attempts: int = 10) -> int:
    """
    Find an available port starting from start_port.
    Tries up to max_attempts ports.
    """
    import socket
    
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    
    raise RuntimeError(f"No available port found in range {start_port}-{start_port + max_attempts}")


# ============================================
# CODE GUARDIAN TOOLS - Prevención de Duplicación
# ============================================

@mcp.tool()
@visual_tool_decorator
async def check_code_creation(name: str, code_type: str, content: str, 
                            context: Optional[str] = None, 
                            auto_prevent: bool = True) -> str:
    """
    🛡️ CODE GUARDIAN: Verifica duplicación ANTES de crear código
    
    Este es el POLICÍA que detiene la creación de código duplicado.
    Analiza el código propuesto contra TODO el conocimiento del proyecto
    y PREVIENE la duplicación con severidad crítica.
    
    Args:
        name: Nombre del código propuesto (ej: 'calculate_total', 'UserProfile')
        code_type: Tipo de código ('function', 'class', 'model', 'view', 'template', 'form')
        content: Contenido completo del código a verificar
        context: Contexto adicional en formato JSON (opcional)
        auto_prevent: Si debe prevenir automáticamente duplicación crítica (default: True)
    
    Returns:
        Resultado de la verificación con recomendaciones detalladas
        
    Examples:
        check_code_creation(
            name="calculate_total",
            code_type="function", 
            content="def calculate_total(items): return sum(item.price for item in items)",
            context='{"purpose": "calcular total de factura"}'
        )
    """
    try:
        if _code_guardian_tools is None:
            return "❌ Error: Code Guardian no está disponible"
        
        return _code_guardian_tools['check_code_creation'](
            name=name,
            code_type=code_type,
            content=content,
            context=context,
            auto_prevent=auto_prevent
        )
        
    except Exception as e:
        return f"❌ Error en Code Guardian: {str(e)}"


@mcp.tool()
@visual_tool_decorator
async def analyze_project_redundancy(project_path: str = ".") -> str:
    """
    📊 ANALIZA REDUNDANCIA: Escanea TODO el proyecto en busca de duplicación
    
    Herramienta de análisis profundo que identifica:
    - Patrones de duplicación frecuentes
    - Áreas problemáticas del código
    - Oportunidades de refactorización
    - Riesgos de duplicación por tipo de código
    
    Args:
        project_path: Ruta del proyecto a analizar (default: ".")
    
    Returns:
        Análisis completo con recomendaciones de refactorización
        
    Example:
        analyze_project_redundancy("/path/to/yari-medic")
    """
    try:
        if _code_guardian_tools is None:
            return "❌ Error: Code Guardian no está disponible"
        
        return _code_guardian_tools['analyze_project_redundancy'](project_path)
        
    except Exception as e:
        return f"❌ Error analizando redundancia: {str(e)}"


@mcp.tool()
@visual_tool_decorator
async def get_code_suggestions(requirement: str, code_type: str = "function") -> str:
    """
    💡 SUGIERE CÓDIGO EXISTENTE: Encuentra código reutilizable para tu necesidad
    
    Busca en TODO el conocimiento del proyecto código existente que pueda
    cumplir con tu requisito. Incluye validación JEPA para consistencia.
    
    Args:
        requirement: Descripción del requisito o funcionalidad buscada
        code_type: Tipo de código sugerido ('function', 'class', 'model', etc.)
    
    Returns:
        Sugerencias de código reutilizable con validación JEPA
        
    Examples:
        get_code_suggestions("validar email de usuario", "function")
        get_code_suggestions("modelo de perfil con foto", "model")
    """
    try:
        if _code_guardian_tools is None:
            return "❌ Error: Code Guardian no está disponible"
        
        return _code_guardian_tools['get_code_suggestions'](requirement, code_type)
        
    except Exception as e:
        return f"❌ Error obteniendo sugerencias: {str(e)}"


@mcp.tool()
@visual_tool_decorator
async def learn_from_context(context_files: str) -> str:
    """
    🧠 APRENDE DE CONTEXTO: Mejora la detección con archivos de contexto
    
    Enseña al Code Guardian sobre nuevos archivos de contexto para
    mejorar la detección de duplicación y aprender patrones del proyecto.
    
    Args:
        context_files: Lista de archivos separados por comas (ej: "context.md,Vision.md")
    
    Returns:
        Resultado del aprendizaje con mejoras detectadas
        
    Example:
        learn_from_context("data/project_context/context.md,data/project_context/Vision.md")
    """
    try:
        if _code_guardian_tools is None:
            return "❌ Error: Code Guardian no está disponible"
        
        return _code_guardian_tools['learn_from_context'](context_files)
        
    except Exception as e:
        return f"❌ Error en aprendizaje: {str(e)}"


if __name__ == "__main__":
    import uvicorn
    import signal
    
    main_logger = None
    
    try:
        from pretty_logger import get_logger
        from log_config import setup_clean_logging, get_clean_log_config
        
        # Configurar logging LIMPIO (filtra ruido de SSE, formatea bonito)
        setup_clean_logging()
        main_logger = get_logger("MCP-V8")
        
        # Registrar handler de shutdown
        def signal_handler(sig, frame):
            graceful_shutdown(main_logger)
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Buscar puerto disponible dinámicamente
        port = find_available_port(8765)
        
        # Header bonito v9
        main_logger.header("CONTEXT VORTEX - MCP Hub v9.0", "Contextual Intelligence Engine")
        
        if port != 8765:
            main_logger.warning(f"Puerto 8765 ocupado, usando puerto alternativo: {port}")
        
        main_logger.info("Iniciando servidor SSE...", endpoint=f"http://127.0.0.1:{port}/sse")
        
        from pretty_logger import Colors
        print(f"{Colors.GREEN_MID}  Contextual Intelligence Engine {Colors.RESET}")
        print(f"{Colors.DIM}  ----------------------------- v9 Contextual Intelligence Core ----------------------------{Colors.RESET}")
        print(f"  System Status: {Colors.GREEN_NEON}ONLINE{Colors.RESET} | JEPA World Model: {Colors.GREEN_NEON}ACTIVE{Colors.RESET}")
        print(f"  Model Pulse: {Colors.CYAN}SYNCHRONIZED{Colors.RESET} | Anti-Hallucination: {Colors.GREEN_NEON}ENABLED{Colors.RESET}")
        print(f"{Colors.DIM}  ------------------------------------------------------------------------------------------{Colors.RESET}")
        print(f"\n{Colors.GREEN_NEON}📋 VORTEX ARSENAL Ready:{Colors.RESET}", file=sys.stderr)
        
        # Matrix flows for categories
        main_logger.matrix_flow("V5 Core: ping, get_context, validate, status", "INIT-CORE", color=Colors.GREEN_MINT)
        main_logger.matrix_flow("V9 Intelligence: memory, skills, grounding", "INIT-INTEL", color=Colors.GREEN_NEON)
        main_logger.matrix_flow("V7 Sessions: create, summary, list, delete", "INIT-SESSIONS", color=Colors.GREEN_PALE)
        main_logger.matrix_flow("V7 Code: index, search_entity", "INIT-CODE", color=Colors.GREEN_MID)
        main_logger.matrix_flow("Advanced: process, expand, chunk, feedback", "INIT-ADV", color=Colors.CYAN)
        main_logger.matrix_flow("CODE GUARDIAN: duplication prevention system", "INIT-GUARDIAN", color=Colors.RED_NEON)
        
        main_logger.divider(" Waiting for Neural Link (SSE) ", char="=", width=80)
        
        app = mcp.sse_app()
        
        # Iniciar thread de pulso visual para "vida" en la consola
        import threading
        import time
        import random
        
        def pulse_vortex():
            while True:
                time.sleep(random.randint(60, 120)) # Pulso cada 1-2 minutos
                pulse_id = "".join(random.choice("01") for _ in range(4))
                main_logger.v9_flow("PULSE", f"{Colors.DIM}Vortex Heartbeat {pulse_id} - System Stable{Colors.RESET}")
        
        pulse_thread = threading.Thread(target=pulse_vortex, daemon=True)
        pulse_thread.start()
        
        # Usar configuración de log limpia para uvicorn
        uvicorn.run(app, host="127.0.0.1", port=port, log_config=get_clean_log_config())
        
    except ImportError:
        # Fallback si falla pretty_logger
        def signal_handler(sig, frame):
            graceful_shutdown(None)
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Buscar puerto disponible
        port = find_available_port(8765)
        
        print("=" * 60, file=sys.stderr)
        print("MCP Server v10 - Context Vortex + Code Guardian (Anti-Duplication)", file=sys.stderr)
        if port != 8765:
            print(f"⚠️ Puerto 8765 ocupado, usando: {port}", file=sys.stderr)
        print(f"Endpoint: http://127.0.0.1:{port}/sse", file=sys.stderr)
        print("💾 Presiona Ctrl+C para guardar y cerrar", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        
        app = mcp.sse_app()
        uvicorn.run(app, host="127.0.0.1", port=port)




