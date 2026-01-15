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

# Create server
mcp = FastMCP("yari-mcp-v7")

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
        server = get_v6_server()
        result = server._get_context({
            'query': query,
            'top_k': top_k,
            'min_score': min_score,
            'session_id': session_id
        })
        if 'content' in result and result['content']:
            return result['content'][0].get('text', 'No context found')
        return "No context found"
    except Exception as e:
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
        result = server._validate_response({
            'response': response,
            'evidence': evidence
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
        result = server._index_status({})
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
        if 'content' in result and result['content']:
            return result['content'][0].get('text', 'Session created')
        return "Session created"
    except Exception as e:
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
        if 'content' in result and result['content']:
            return result['content'][0].get('text', 'Indexing complete')
        return "Indexing complete"
    except Exception as e:
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
# Entry Point
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60, file=sys.stderr)
    print("MCP Server v7 COMPLETO - HTTP/SSE Transport", file=sys.stderr)
    print("Endpoint: http://127.0.0.1:8765/sse", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("\nTools disponibles (16):", file=sys.stderr)
    print("  V5 Core: ping, get_context, validate_response, index_status", file=sys.stderr)
    print("  V7 Sessions: create_session, get_session_summary, list_sessions, delete_session", file=sys.stderr)
    print("  V7 Code: index_code, search_entity", file=sys.stderr)
    print("  Advanced: process_advanced, expand_query, chunk_document, get_system_status, add_feedback, optimize_configuration", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    app = mcp.sse_app()
    uvicorn.run(app, host="127.0.0.1", port=8765)

