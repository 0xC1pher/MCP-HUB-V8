"""
Decoradores para las herramientas MCP
"""

import functools
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

def visual_tool_decorator(tool_name: str = None):
    """
    Decorador para herramientas MCP que añade logging visual
    
    Args:
        tool_name: Nombre personalizado para la herramienta (opcional)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = tool_name or func.__name__
            logger.info(f"🛠️ Ejecutando herramienta: {name}")
            
            try:
                result = func(*args, **kwargs)
                logger.info(f"✅ Herramienta {name} completada exitosamente")
                return result
            except Exception as e:
                logger.error(f"❌ Error en herramienta {name}: {e}")
                raise
        
        # Añadir metadatos para herramientas MCP
        wrapper._tool_name = tool_name or func.__name__
        wrapper._is_visual_tool = True
        
        return wrapper
    
    return decorator