"""
Test rápido del protocolo MCP de v6.py
"""
import json
import sys
from pathlib import Path

# Agregar path
sys.path.insert(0, str(Path(__file__).parent / "core"))

from v6 import MCPServerV6

def test_mcp_protocol():
    """Test del protocolo MCP"""
    print("Inicializando servidor v6...")
    server = MCPServerV6()
    
    # Test 1: Initialize
    print("\n=== Test 1: Initialize ===")
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    response = server.handle_request(init_request)
    print("Request:")
    print(json.dumps(init_request, indent=2))
    print("\nResponse:")
    print(json.dumps(response, indent=2))
    
    # Test 2: tools/list
    print("\n=== Test 2: tools/list ===")
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    response = server.handle_request(tools_request)
    print("Request:")
    print(json.dumps(tools_request, indent=2))
    print("\nResponse:")
    print(json.dumps(response, indent=2))
    
    # Verificar formato
    if 'result' in response and 'tools' in response['result']:
        print(f"\n✓ Format correcto: {len(response['result']['tools'])} tools encontradas")
        for tool in response['result']['tools'][:3]:
            print(f"  - {tool['name']}: {tool['description']}")
    else:
        print("\n✗ Formato incorrecto!")
        print("Esperado: response['result']['tools']")
        print(f"Recibido: {list(response.keys())}")

if __name__ == "__main__":
    test_mcp_protocol()
