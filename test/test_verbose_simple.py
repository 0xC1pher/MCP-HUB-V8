# Test verbose mode
import sys
sys.path.insert(0, 'core')

from v6 import MCPServerV6

print("🚀 Iniciando prueba de modo verbose...")
server = MCPServerV6(verbose=True)
print("✅ Servidor creado con verbose=True")

print("📋 Probando _validate_response...")
result = server._validate_response({
    'response': 'This is a test response',
    'evidence_ids': ['test123']
})
print(f"📊 Resultado: {result['content'][0]['text']}")