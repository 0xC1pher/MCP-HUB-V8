"""
MCP Server v7 COMPLETO - HTTP/SSE Transport
Integra TODAS las funcionalidades de v7 + Advanced Features

TOOLS INCLUIDAS (16 total):
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
"""
import sys
import os
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any

# Setup paths
current_dir = Path(__file__).resolve().parent
mcp_hub_root = current_dir.parent
sys.path.insert(0, str(mcp_hub_root))
sys.path.insert(0, str(current_dir))

from mcp.server.fastmcp import FastMCP

# Import Pretty Logger for beautiful logging
try:
    from pretty_logger import get_logger
    _tool_logger = get_logger("MCP-Tools")
except ImportError:
    _tool_logger = None

# Create server
mcp = FastMCP("AGI-Context-Vortex")

# ============================================
# Singleton instances
# ============================================
_v6_server = None
_orchestrator = None

def get_v6_server():
    """Get or create singleton instance of MCPServerV6"""
    global _v6_server
    if _v6_server is None:
        from v6 import MCPServerV6
        _v6_server = MCPServerV6()
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


# ============================================
# V5 Tools (Core Retrieval)
# ============================================

@mcp.tool()
async def ping() -> str:
    """Simple ping test to verify MCP connectivity."""
    return "pong - MCP v7 HTTP server is working!"


@mcp.tool()
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
        
        # Extraer texto del resultado unificado
        if 'content' in result and result['content']:
            return result['content'][0].get('text', 'No context found')
        return "No context found"
    except Exception as e:
        if _tool_logger:
            _tool_logger.error(f"Query failed: {query[:30]}...", error=str(e))
        return f"Error: {str(e)}"


@mcp.tool()
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

# ============================================
# v9 Tools (Knowledge & Persistence)
# ============================================

@mcp.tool()
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
        
        output = f"=== Advanced Processing Result ===\n"
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
            output += f"\nFeature Status:\n"
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
        
        output = f"=== Query Expansion ===\n"
        output += f"Original: {query}\n\n"
        
        if hasattr(expansion, 'expanded_queries'):
            output += f"Expanded Queries:\n"
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
        
        output = f"=== Dynamic Chunking Result ===\n"
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
                output += f"   📁 Code: Auto-indexed\n"
            
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
                _tool_logger.error(f"smart_query failed", error=result['error'])
            return f"Error: {result['error']}"
        
        if _tool_logger:
            _tool_logger.success(f"smart_query completed", session=result.get('session_id', 'N/A'))
        
        output = f"=== Smart Query Result ===\n"
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
                _tool_logger.warning(f"Quality issues found", count=len(warnings))
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
        server = get_v6_server()
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
        
        # 6. Cerrar archivo de logs
        if _tool_logger and hasattr(_tool_logger, 'close'):
            _tool_logger.close()
            saved_items.append("Logs")
        
        if logger:
            logger.success(f"Datos guardados: {', '.join(saved_items)}")
            logger.divider()
            logger.info("👋 ¡Hasta pronto! MCP Hub v8 cerrado correctamente.")
        else:
            print(f"✅ Guardado: {', '.join(saved_items)}", file=sys.stderr)
            print("👋 ¡Hasta pronto!", file=sys.stderr)
            
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
        print(f"\n{Colors.GREEN_NEON}📋 VORTEX ARSENAL Ready:{Colors.RESET}", file=sys.stderr)
        
        # Matrix flows for categories
        main_logger.matrix_flow("V5 Core: ping, get_context, validate, status", "INIT-CORE", color=Colors.GREEN_MINT)
        main_logger.matrix_flow("V9 Intelligence: memory, skills, grounding", "INIT-INTEL", color=Colors.GREEN_NEON)
        main_logger.matrix_flow("V7 Sessions: create, summary, list, delete", "INIT-SESSIONS", color=Colors.GREEN_PALE)
        main_logger.matrix_flow("V7 Code: index, search_entity", "INIT-CODE", color=Colors.GREEN_MID)
        main_logger.matrix_flow("Advanced: process, expand, chunk, feedback", "INIT-ADV", color=Colors.CYAN)
        
        main_logger.divider(f" Waiting for Neural Link (SSE) ", char="=", width=80)
        
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
        import socket
        
        # Fallback si falla pretty_logger
        def signal_handler(sig, frame):
            graceful_shutdown(None)
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Buscar puerto disponible
        port = find_available_port(8765)
        
        print("=" * 60, file=sys.stderr)
        print("MCP Server v8 - Extended Knowledge + Quality Guardian", file=sys.stderr)
        if port != 8765:
            print(f"⚠️ Puerto 8765 ocupado, usando: {port}", file=sys.stderr)
        print(f"Endpoint: http://127.0.0.1:{port}/sse", file=sys.stderr)
        print("💾 Presiona Ctrl+C para guardar y cerrar", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        
        app = mcp.sse_app()
        uvicorn.run(app, host="127.0.0.1", port=port)




