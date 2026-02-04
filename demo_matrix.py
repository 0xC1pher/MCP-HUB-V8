import sys
from pathlib import Path

# Add project root to sys.path
root_path = Path(__file__).resolve().parent
sys.path.insert(0, str(root_path))

from core.v6 import MCPServerV6
from core.pretty_logger import get_logger, Colors

def test_matrix():
    logger = get_logger()
    logger.header("MATRIX FLOW DEMO", "Futuristic Tool Tracking")
    
    server = MCPServerV6()
    
    # Test a few tools with different categories
    
    # 1. RETRIEVAL (Mint)
    print("\n--- [V5] get_context ---")
    server.handle_request({
        'method': 'tools/call',
        'params': {'name': 'get_context', 'arguments': {'query': 'test matrix', 'top_k': 1}}
    })
    
    # 2. INTELLIGENCE (Neon)
    print("\n--- [V9] ground_project_context ---")
    server.handle_request({
        'method': 'tools/call',
        'params': {'name': 'ground_project_context', 'arguments': {'query': 'reglas de negocio'}}
    })
    
    # 3. SESSIONS (Pale)
    print("\n--- [V7] smart_session_init ---")
    server.handle_request({
        'method': 'tools/call',
        'params': {'name': 'smart_session_init', 'arguments': {'context': 'testing matrix flow'}}
    })
    
    # 4. ADVANCED (Cyan)
    print("\n--- [ADV] check_quality ---")
    server.handle_request({
        'method': 'tools/call',
        'params': {'name': 'check_quality', 'arguments': {'code': 'def hello(): print("world")'}}
    })

if __name__ == "__main__":
    test_matrix()
