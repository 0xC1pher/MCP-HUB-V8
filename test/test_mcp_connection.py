"""
Test de conexión MCP - Verifica que el servidor responde correctamente
"""

import subprocess
import json
import sys
from pathlib import Path

def test_mcp_server(version='v6'):
    """Test que el servidor MCP responde correctamente"""
    
    print(f"="*80)
    print(f"Testing MCP Server {version.upper()}")
    print(f"="*80)
    
    # Ruta al launcher
    launcher_path = Path(__file__).parent / "core" / "mcp_launcher.py"
    python_exe = r"C:\Users\0x4171341\Desktop\CONSULTORIO\yari-medic\venv_new\Scripts\python.exe"
    
    # Iniciar el servidor
    print(f"\n1. Iniciando servidor {version}...")
    process = subprocess.Popen(
        [python_exe, "-u", str(launcher_path), version],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Esperar un poco para que el servidor inicie
    import time
    time.sleep(3)
    
    # Test 1: Initialize
    print("\n2. Enviando solicitud de inicialización...")
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
    
    try:
        process.stdin.write(json.dumps(init_request) + '\n')
        process.stdin.flush()
        
        # Leer respuesta
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line)
            print("✓ Respuesta de inicialización recibida:")
            print(json.dumps(response, indent=2))
        else:
            print("✗ No se recibió respuesta de inicialización")
            stderr = process.stderr.read()
            if stderr:
                print(f"Error: {stderr}")
            return False
        
        # Test 2: List tools
        print("\n3. Solicitando lista de tools...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        process.stdin.write(json.dumps(tools_request) + '\n')
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line)
            print("✓ Lista de tools recibida:")
            if 'result' in response and 'tools' in response['result']:
                tools = response['result']['tools']
                print(f"  Total tools: {len(tools)}")
                for tool in tools:
                    print(f"  - {tool['name']}: {tool['description']}")
            else:
                print(json.dumps(response, indent=2))
        else:
            print("✗ No se recibió lista de tools")
            return False
        
        print("\n" + "="*80)
        print(f"✓ Servidor {version.upper()} funcionando correctamente")
        print("="*80)
        
        # Cerrar el servidor
        process.terminate()
        process.wait(timeout=5)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
        
        # Leer stderr para más información
        try:
            stderr = process.stderr.read()
            if stderr:
                print(f"\nStderr del servidor:\n{stderr}")
        except:
            pass
        
        process.terminate()
        return False

if __name__ == "__main__":
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*25 + "MCP CONNECTION TEST" + " "*34 + "║")
    print("╚" + "="*78 + "╝")
    print()
    
    # Test v5
    v5_ok = test_mcp_server('v5')
    
    print("\n")
    
    # Test v6
    v6_ok = test_mcp_server('v6')
    
    print("\n" + "="*80)
    print("RESUMEN")
    print("="*80)
    print(f"v5: {'✓ PASS' if v5_ok else '✗ FAIL'}")
    print(f"v6: {'✓ PASS' if v6_ok else '✗ FAIL'}")
    print("="*80)
    
    sys.exit(0 if (v5_ok and v6_ok) else 1)
