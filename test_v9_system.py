import os
import sys
import json
import logging
from pathlib import Path

# Add project root to sys.path
root_path = Path(__file__).resolve().parent
sys.path.insert(0, str(root_path))

from core.v6 import MCPServerV6
from core.pretty_logger import get_logger

def test_flows():
    # Setup logger to see output
    logger = get_logger()
    logger.header("V9 SYSTEM FLOW TEST")
    
    # Initialize Server
    print("\n--- Initializing Server ---")
    server = MCPServerV6()
    
    # 1. Grounding Test
    print("\n--- Testing Grounding Flow ---")
    grounding_result = server.handle_request({
        'method': 'tools/call',
        'params': {'name': 'ground_project_context', 'arguments': {'query': 'reglas de multi-tenancy'}}
    })
    print(f"Grounding Status: OK")
    
    # 2. Memory Test
    print("\n--- Testing Memory Flow ---")
    # Create
    server.handle_request({
        'method': 'tools/call',
        'params': {'name': 'memory_tool', 'arguments': {'command': 'create', 'file_path': 'test_v9.txt', 'content': 'V9 Flow is working!'}}
    })
    # Read
    read_result = server.handle_request({
        'method': 'tools/call',
        'params': {'name': 'memory_tool', 'arguments': {'command': 'read', 'file_path': 'test_v9.txt'}}
    })
    print(f"Memory Read: {read_result['result']['content'][0]['text']}")
    
    # 3. Expansion/Retrieval (get_context)
    print("\n--- Testing Retrieval/Expansion Flow ---")
    context_result = server.handle_request({
        'method': 'tools/call',
        'params': {'name': 'get_context', 'arguments': {'query': 'como funciona el crm'}}
    })
    print(f"Context Result Status: {'OK' if 'result' in context_result else 'FAIL'}")
    
    # 4. Tool List Test
    print("\n--- Testing available tools (v9 Arsenal) ---")
    tools = server._handle_tools_list()
    tool_list = [t['name'] for t in tools.get('tools', [])]
    print(f"Total Tools Registered: {len(tool_list)}")
    print(f"Tools list: {', '.join(tool_list)}")

if __name__ == "__main__":
    try:
        test_flows()
    except Exception as e:
        print(f"ERROR DURING TEST: {e}")
        import traceback
        traceback.print_exc()
