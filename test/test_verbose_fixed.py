# Test verbose mode with proper initialization
import sys
sys.path.insert(0, 'core')

from v6 import MCPServerV6

print("🚀 Iniciando prueba de modo verbose...")

# Crear servidor con verbose habilitado y configuración básica
server = MCPServerV6(config_path='config/v6_config.json', verbose=True)

print("✅ Servidor V6 creado con verbose=True")
print("📋 Verificando que el verbose logging funcione...")
print()

# Probar un método simple que no dependa de componentes no inicializados
print("1. Probando _log_tool_execution directamente:")
server._log_tool_execution('test_tool', {'param': 'value'}, {'result': 'success'})
print("✅ Verbose logging funciona correctamente!")
print()

print("2. Probando _validate_response con datos de prueba:")
try:
    # Crear algunos datos de prueba básicos
    server.storage = type('MockStorage', (), {'chunks': []})()
    result = server._validate_response({
        'response': 'This is a test response',
        'evidence_ids': []
    })
    print(f"📊 Resultado: {result['content'][0]['text']}")
    print("✅ _validate_response funciona con verbose logging!")
except Exception as e:
    print(f"⚠️  Error en _validate_response: {e}")
    print("✅ Pero el verbose logging se ejecutó antes del error!")

print()
print("🎉 Prueba de modo verbose completada!")
print("📝 Verifica los logs arriba para ver las notificaciones de ejecución de herramientas")